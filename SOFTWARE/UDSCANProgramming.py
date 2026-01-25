import sys
import struct
import time
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QFileDialog, QProgressBar, QGroupBox,
                             QComboBox, QSpinBox, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont
import serial
import serial.tools.list_ports


class UDSProtocol:
    """Unified Diagnostic Services Protocol Implementation"""
    
    # Service IDs
    SID_DIAGNOSTIC_SESSION = 0x10
    SID_ECU_RESET = 0x11
    SID_SECURITY_ACCESS = 0x27
    SID_WRITE_DATA = 0x2E
    SID_ROUTINE_CONTROL = 0x31
    SID_REQUEST_DOWNLOAD = 0x34
    SID_TRANSFER_DATA = 0x36
    SID_TRANSFER_EXIT = 0x37
    
    # Session types
    SESSION_PROGRAMMING = 0x02
    
    # Security access types
    SECURITY_REQUEST_SEED = 0x01
    SECURITY_SEND_KEY = 0x02
    
    # Routine control
    ROUTINE_ERASE_MEMORY = 0xFF00
    ROUTINE_CRC_CHECK = 0xFF01
    
    # Reset types
    RESET_HARD = 0x03
    
    # Response codes
    POSITIVE_RESPONSE = 0x40
    NRC = 0x7F  # Negative Response Code
    
    @staticmethod
    def calculate_checksum(data):
        """Calculate simple checksum for data"""
        return sum(data) & 0xFF
    
    @staticmethod
    def calculate_crc16(data):
        """Calculate CRC16 for data verification"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc


class FlashingThread(QThread):
    """Thread for handling the flashing process"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, port, baudrate, bin_file, sector_address, sector_size):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.bin_file = bin_file
        self.sector_address = sector_address
        self.sector_size = sector_size
        self.serial_port = None
        self.running = True
        self.uds = UDSProtocol()
        
    def run(self):
        try:
            # Open serial connection
            self.log.emit(f"Opening serial port {self.port} at {self.baudrate} baud...")
            self.serial_port = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(0.1)
            
            # Read binary file
            self.log.emit(f"Reading binary file: {self.bin_file}")
            with open(self.bin_file, 'rb') as f:
                firmware_data = f.read()
            file_size = len(firmware_data)
            self.log.emit(f"File size: {file_size} bytes")
            
            # Execute flashing sequence
            if not self.running:
                return
            
            # Step 1: Enter Programming Session
            self.status.emit("Entering Programming Session...")
            self.progress.emit(5)
            if not self.enter_programming_session():
                self.finished.emit(False, "Failed to enter programming session")
                return
            
            # Step 2: Security Access
            self.status.emit("Requesting Security Access...")
            self.progress.emit(10)
            if not self.perform_security_access():
                self.finished.emit(False, "Security access failed")
                return
            
            # Step 3: Write Fingerprint Data
            self.status.emit("Writing Fingerprint Data...")
            self.progress.emit(15)
            if not self.write_fingerprint():
                self.finished.emit(False, "Failed to write fingerprint")
                return
            
            # Step 4: Erase Memory
            self.status.emit("Erasing Flash Memory...")
            self.progress.emit(20)
            if not self.erase_memory():
                self.finished.emit(False, "Memory erase failed")
                return
            
            # Step 5: Request Download
            self.status.emit("Requesting Download...")
            self.progress.emit(25)
            block_size = self.request_download(file_size)
            if block_size == 0:
                self.finished.emit(False, "Request download failed")
                return
            
            # Step 6: Transfer Data
            self.status.emit("Transferring Data...")
            if not self.transfer_data(firmware_data, block_size):
                self.finished.emit(False, "Data transfer failed")
                return
            
            # Step 7: Transfer Exit
            self.status.emit("Completing Transfer...")
            self.progress.emit(90)
            if not self.transfer_exit():
                self.finished.emit(False, "Transfer exit failed")
                return
            
            # Step 8: CRC Check
            self.status.emit("Verifying CRC...")
            self.progress.emit(95)
            if not self.crc_check(firmware_data):
                self.finished.emit(False, "CRC verification failed")
                return
            
            # Step 9: ECU Reset
            self.status.emit("Resetting ECU...")
            self.progress.emit(98)
            if not self.ecu_reset():
                self.finished.emit(False, "ECU reset failed")
                return
            
            self.progress.emit(100)
            self.finished.emit(True, "Flashing completed successfully!")
            
        except Exception as e:
            self.log.emit(f"Error: {str(e)}")
            self.finished.emit(False, f"Exception: {str(e)}")
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
    
    def send_message(self, data):
        """Send UDS message and wait for response"""
        if not self.serial_port or not self.serial_port.is_open:
            return None
        
        # Log outgoing message
        self.log.emit(f"TX: {' '.join(f'{b:02X}' for b in data)}")
        
        # Send data
        self.serial_port.write(bytes(data))
        
        # Wait for response
        response = self.serial_port.read(256)
        if response:
            self.log.emit(f"RX: {' '.join(f'{b:02X}' for b in response)}")
        
        return response
    
    def enter_programming_session(self):
        """Step 1: Enter Programming Session ($10 02)"""
        message = [self.uds.SID_DIAGNOSTIC_SESSION, self.uds.SESSION_PROGRAMMING]
        response = self.send_message(message)
        
        if response and len(response) >= 2:
            if response[0] == self.uds.SID_DIAGNOSTIC_SESSION + self.uds.POSITIVE_RESPONSE:
                self.log.emit("✓ Programming session entered")
                return True
        
        self.log.emit("✗ Failed to enter programming session")
        return False
    
    def perform_security_access(self):
        """Step 2-3: Request seed and send key"""
        max_tries = 10
        
        for attempt in range(max_tries):
            # Request Seed ($27 01)
            message = [self.uds.SID_SECURITY_ACCESS, self.uds.SECURITY_REQUEST_SEED]
            response = self.send_message(message)
            
            if not response or len(response) < 4:
                continue
            
            if response[0] == self.uds.SID_SECURITY_ACCESS + self.uds.POSITIVE_RESPONSE:
                seed = response[2:6]  # Assuming 4-byte seed
                self.log.emit(f"Seed received: {' '.join(f'{b:02X}' for b in seed)}")
                
                # Calculate key (simplified - implement your algorithm)
                key = self.calculate_security_key(seed)
                
                # Send Key ($27 02)
                message = [self.uds.SID_SECURITY_ACCESS, self.uds.SECURITY_SEND_KEY] + list(key)
                response = self.send_message(message)
                
                if response and response[0] == self.uds.SID_SECURITY_ACCESS + self.uds.POSITIVE_RESPONSE:
                    self.log.emit("✓ Security access granted")
                    return True
            
            self.log.emit(f"Security attempt {attempt + 1}/{max_tries} failed")
            time.sleep(0.1)
        
        self.log.emit("✗ Security access failed after max tries")
        return False
    
    def calculate_security_key(self, seed):
        """Calculate security key from seed - IMPLEMENT YOUR ALGORITHM"""
        # This is a placeholder - implement your actual security algorithm
        # Example: simple XOR with constant
        key = [s ^ 0xAA for s in seed]
        return key
    
    def write_fingerprint(self):
        """Step 4: Write Fingerprint Data ($2E F1 9A)"""
        # Fingerprint data could include: file name, date, version, etc.
        fingerprint = b"FW_V1.0_" + str(int(time.time())).encode()[:8]
        message = [self.uds.SID_WRITE_DATA, 0xF1, 0x9A] + list(fingerprint)
        response = self.send_message(message)
        
        if response and response[0] == self.uds.SID_WRITE_DATA + self.uds.POSITIVE_RESPONSE:
            self.log.emit("✓ Fingerprint written")
            return True
        
        self.log.emit("✗ Failed to write fingerprint")
        return False
    
    def erase_memory(self):
        """Step 5: Erase Memory ($31 01 FF 00)"""
        # Routine Control: Start Routine for Memory Erase
        message = [
            self.uds.SID_ROUTINE_CONTROL,
            0x01,  # Start routine
            (self.uds.ROUTINE_ERASE_MEMORY >> 8) & 0xFF,
            self.uds.ROUTINE_ERASE_MEMORY & 0xFF,
            (self.sector_address >> 24) & 0xFF,
            (self.sector_address >> 16) & 0xFF,
            (self.sector_address >> 8) & 0xFF,
            self.sector_address & 0xFF
        ]
        response = self.send_message(message)
        
        if response and response[0] == self.uds.SID_ROUTINE_CONTROL + self.uds.POSITIVE_RESPONSE:
            self.log.emit("✓ Memory erased")
            time.sleep(2)  # Wait for erase to complete
            return True
        
        self.log.emit("✗ Memory erase failed")
        return False
    
    def request_download(self, file_size):
        """Step 6: Request Download ($34)"""
        # Request Download with address and size
        message = [
            self.uds.SID_REQUEST_DOWNLOAD,
            0x00,  # Data format
            0x44,  # Address and length format (4 bytes each)
            (self.sector_address >> 24) & 0xFF,
            (self.sector_address >> 16) & 0xFF,
            (self.sector_address >> 8) & 0xFF,
            self.sector_address & 0xFF,
            (file_size >> 24) & 0xFF,
            (file_size >> 16) & 0xFF,
            (file_size >> 8) & 0xFF,
            file_size & 0xFF
        ]
        response = self.send_message(message)
        
        if response and response[0] == self.uds.SID_REQUEST_DOWNLOAD + self.uds.POSITIVE_RESPONSE:
            # Extract max block size from response
            block_size = response[2] * 256 + response[3] if len(response) >= 4 else 256
            self.log.emit(f"✓ Download requested, block size: {block_size}")
            return block_size
        
        self.log.emit("✗ Request download failed")
        return 0
    
    def transfer_data(self, data, block_size):
        """Step 7: Transfer Data ($36) in blocks"""
        total_blocks = (len(data) + block_size - 1) // block_size
        sequence_number = 1
        
        for i in range(0, len(data), block_size):
            if not self.running:
                return False
            
            block = data[i:i + block_size]
            message = [self.uds.SID_TRANSFER_DATA, sequence_number] + list(block)
            response = self.send_message(message)
            
            if not response or response[0] != self.uds.SID_TRANSFER_DATA + self.uds.POSITIVE_RESPONSE:
                self.log.emit(f"✗ Transfer failed at block {sequence_number}")
                return False
            
            # Update progress (30-85% range for data transfer)
            progress = 30 + int((i / len(data)) * 55)
            self.progress.emit(progress)
            
            # Increment sequence number (1-255, then wrap to 0)
            sequence_number = (sequence_number + 1) & 0xFF
            if sequence_number == 0:
                sequence_number = 1
            
            if i % (block_size * 10) == 0:  # Log every 10 blocks
                self.log.emit(f"Transferred {i}/{len(data)} bytes ({i*100//len(data)}%)")
        
        self.log.emit("✓ All data transferred")
        return True
    
    def transfer_exit(self):
        """Step 8: Transfer Exit ($37)"""
        message = [self.uds.SID_TRANSFER_EXIT]
        response = self.send_message(message)
        
        if response and response[0] == self.uds.SID_TRANSFER_EXIT + self.uds.POSITIVE_RESPONSE:
            self.log.emit("✓ Transfer completed")
            return True
        
        self.log.emit("✗ Transfer exit failed")
        return False
    
    def crc_check(self, data):
        """Step 9: CRC Check ($31 01 FF 01)"""
        # Calculate CRC16
        crc = self.uds.calculate_crc16(data)
        
        # Routine Control: CRC Check
        message = [
            self.uds.SID_ROUTINE_CONTROL,
            0x01,  # Start routine
            (self.uds.ROUTINE_CRC_CHECK >> 8) & 0xFF,
            self.uds.ROUTINE_CRC_CHECK & 0xFF,
            (crc >> 8) & 0xFF,
            crc & 0xFF
        ]
        response = self.send_message(message)
        
        if response and response[0] == self.uds.SID_ROUTINE_CONTROL + self.uds.POSITIVE_RESPONSE:
            self.log.emit(f"✓ CRC verification passed (CRC: 0x{crc:04X})")
            return True
        
        self.log.emit("✗ CRC verification failed")
        return False
    
    def ecu_reset(self):
        """Step 10: ECU Reset ($11 03)"""
        message = [self.uds.SID_ECU_RESET, self.uds.RESET_HARD]
        response = self.send_message(message)
        
        if response and response[0] == self.uds.SID_ECU_RESET + self.uds.POSITIVE_RESPONSE:
            self.log.emit("✓ ECU reset initiated")
            return True
        
        self.log.emit("✗ ECU reset failed")
        return False
    
    def stop(self):
        """Stop the flashing process"""
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STM32F407 ECU Flasher")
        self.setGeometry(100, 100, 900, 700)
        
        self.flashing_thread = None
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("STM32F407 ECU Firmware Flasher")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Connection Settings Group
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QVBoxLayout()
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Serial Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        conn_layout.addLayout(port_layout)
        
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baud Rate:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baud_combo.setCurrentText("115200")
        baud_layout.addWidget(self.baud_combo)
        conn_layout.addLayout(baud_layout)
        
        conn_group.setLayout(conn_layout)
        main_layout.addWidget(conn_group)
        
        # Flash Settings Group
        flash_group = QGroupBox("Flash Settings")
        flash_layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Binary File:"))
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        file_layout.addWidget(self.file_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        flash_layout.addLayout(file_layout)
        
        addr_layout = QHBoxLayout()
        addr_layout.addWidget(QLabel("Sector Address (Hex):"))
        self.addr_edit = QLineEdit("0x08000000")
        addr_layout.addWidget(self.addr_edit)
        flash_layout.addLayout(addr_layout)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Sector Size (KB):"))
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(1, 2048)
        self.size_spinbox.setValue(512)
        size_layout.addWidget(self.size_spinbox)
        flash_layout.addLayout(size_layout)
        
        flash_group.setLayout(flash_layout)
        main_layout.addWidget(flash_group)
        
        # Progress Section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # Log Section
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.flash_btn = QPushButton("Start Flashing")
        self.flash_btn.clicked.connect(self.start_flashing)
        self.flash_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-size: 14px; }")
        button_layout.addWidget(self.flash_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_flashing)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 10px; font-size: 14px; }")
        button_layout.addWidget(self.stop_btn)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        button_layout.addWidget(clear_log_btn)
        
        main_layout.addLayout(button_layout)
        
    def refresh_ports(self):
        """Refresh available serial ports"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")
    
    def browse_file(self):
        """Open file dialog to select binary file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Binary File",
            "",
            "Binary Files (*.bin);;All Files (*.*)"
        )
        if file_path:
            self.file_edit.setText(file_path)
            file_size = Path(file_path).stat().st_size
            self.log_text.append(f"Selected file: {file_path}")
            self.log_text.append(f"File size: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    def start_flashing(self):
        """Start the flashing process"""
        # Validate inputs
        if not self.file_edit.text():
            QMessageBox.warning(self, "Error", "Please select a binary file")
            return
        
        if not self.port_combo.currentText():
            QMessageBox.warning(self, "Error", "Please select a serial port")
            return
        
        try:
            sector_address = int(self.addr_edit.text(), 16)
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid sector address format")
            return
        
        # Extract port name from combo box text
        port = self.port_combo.currentText().split(" - ")[0]
        baudrate = int(self.baud_combo.currentText())
        sector_size = self.size_spinbox.value() * 1024
        
        # Disable controls
        self.flash_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.append("\n=== Starting flashing process ===")
        
        # Create and start flashing thread
        self.flashing_thread = FlashingThread(
            port,
            baudrate,
            self.file_edit.text(),
            sector_address,
            sector_size
        )
        self.flashing_thread.progress.connect(self.update_progress)
        self.flashing_thread.status.connect(self.update_status)
        self.flashing_thread.log.connect(self.append_log)
        self.flashing_thread.finished.connect(self.flashing_finished)
        self.flashing_thread.start()
    
    def stop_flashing(self):
        """Stop the flashing process"""
        if self.flashing_thread:
            self.flashing_thread.stop()
            self.log_text.append("Stopping flashing process...")
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def update_status(self, status):
        """Update status label"""
        self.status_label.setText(status)
    
    def append_log(self, message):
        """Append message to log"""
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()
    
    def flashing_finished(self, success, message):
        """Handle flashing completion"""
        self.flash_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.status_label.setText("✓ Flashing Completed Successfully")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("✗ Flashing Failed")
            QMessageBox.critical(self, "Error", message)
        
        self.log_text.append(f"\n=== {message} ===\n")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()