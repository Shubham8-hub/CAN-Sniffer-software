import sys
import time
import serial
from serial.tools import list_ports

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QMessageBox,
    QTabWidget, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import Qt, QTimer


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.serial = None
        self.rx_timer = None

        self.setWindowTitle("STM32 CAN Sniffer")

        # --- Root layout ---
        main_layout = QVBoxLayout()

        # ========== TOP: PORT SELECTION + CONNECT ==========
        port_layout = QHBoxLayout()
        port_label = QLabel("Serial Port:")
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_ports)

        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo, 1)
        port_layout.addWidget(self.refresh_button)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect_clicked)

        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.device_info_label = QLabel("Device Info: -")
        self.device_info_label.setAlignment(Qt.AlignCenter)

        main_layout.addLayout(port_layout)
        main_layout.addWidget(self.connect_button)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.device_info_label)

        # ========== MIDDLE: TABS (TX / RX) ==========
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Transmit tab ---
        tx_widget = QWidget()
        tx_layout = QVBoxLayout()

        self.tx_id = QLineEdit("123")
        self.tx_dlc = QLineEdit("8")
        self.tx_data = QLineEdit("11 22 33 44 55 66 77 88")

        self.tx_send = QPushButton("Send CAN Frame")
        self.tx_send.clicked.connect(self.send_can_message)

        tx_layout.addWidget(QLabel("CAN ID (hex, e.g. 123 or 1AB)"))
        tx_layout.addWidget(self.tx_id)
        tx_layout.addWidget(QLabel("DLC (0..8)"))
        tx_layout.addWidget(self.tx_dlc)
        tx_layout.addWidget(QLabel("Data bytes (hex, space separated, up to 8 bytes)"))
        tx_layout.addWidget(self.tx_data)
        tx_layout.addWidget(self.tx_send)

        tx_widget.setLayout(tx_layout)
        self.tabs.addTab(tx_widget, "Transmit")

        # --- Receive tab ---
        rx_widget = QWidget()
        rx_layout = QVBoxLayout()

        self.rx_table = QTableWidget(0, 3)
        self.rx_table.setHorizontalHeaderLabels(["CAN ID", "DLC", "Data"])
        self.rx_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        rx_layout.addWidget(self.rx_table)
        rx_widget.setLayout(rx_layout)
        self.tabs.addTab(rx_widget, "Receive")

        self.setLayout(main_layout)

        # Populate ports initially
        self.refresh_ports()

        # Timer for periodic RX polling (started after connect)
        self.rx_timer = QTimer(self)
        self.rx_timer.setInterval(10)  # ms
        self.rx_timer.timeout.connect(self.poll_serial)

    # ----------------------------------------------------------------------
    # Serial helpers
    # ----------------------------------------------------------------------
    def refresh_ports(self):
        """Scan available COM ports and populate combo box."""
        self.port_combo.clear()
        ports = list_ports.comports()
        for p in ports:
            self.port_combo.addItem(f"{p.device} - {p.description}", p.device)

        if not ports:
            self.port_combo.addItem("No ports found", None)

    def open_serial(self, port_name: str) -> bool:
        """Open the selected serial port."""
        try:
            self.serial = serial.Serial(
                port=port_name,
                baudrate=115200,
                timeout=1.0  # used for handshake blocking read
            )
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open port:\n{e}")
            self.serial = None
            return False

    def close_serial(self):
        """Close serial port if open."""
        if self.serial is not None:
            try:
                self.serial.close()
            except Exception:
                pass
            self.serial = None

    # ----------------------------------------------------------------------
    # Button handler
    # ----------------------------------------------------------------------
    def on_connect_clicked(self):
        # If already connected -> send 0x20 and disconnect
        if self.serial is not None and self.serial.is_open:
            try:
                self.serial.write(b'\x20')  # DISCONNECT command to STM32
                time.sleep(0.05)
            except Exception:
                pass

            self.rx_timer.stop()
            self.close_serial()
            self.update_ui_disconnected()
            return

        # If not connected -> connect
        current_index = self.port_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "Warning", "No COM port selected.")
            return

        port_name = self.port_combo.itemData(current_index)
        if port_name is None:
            QMessageBox.warning(self, "Warning", "No valid COM port.")
            return

        if not self.open_serial(port_name):
            return  # error already shown

        # Perform handshake: send 0x10, expect "TEST1CH" + 0x55
        if self.perform_handshake():
            # set timeout to non-blocking for polling
            self.serial.timeout = 0
            self.rx_timer.start()
            self.update_ui_connected()
        else:
            self.close_serial()
            QMessageBox.warning(
                self,
                "Handshake failed",
                "No valid response from device.\n"
                "Make sure STM32 is running the firmware."
            )

    # ----------------------------------------------------------------------
    # Protocol: Handshake
    # ----------------------------------------------------------------------
    def perform_handshake(self) -> bool:
        """
        Send command 0x10, read response.
        Expect: ASCII 'TEST1CH' followed by 0x55.
        """
        if self.serial is None or not self.serial.is_open:
            return False

        try:
            # Clear any existing data
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

            # Send GET DEVICE INFO command
            self.serial.write(b'\x10')

            # Read response (up to 64 bytes, with timeout=1s)
            data = self.serial.read(64)

            if not data:
                return False

            # Look for final 0x55 in data
            if data[-1] != 0x55:
                return False

            # Everything before last byte should be ASCII device info
            info_bytes = data[:-1]
            try:
                device_info = info_bytes.decode('ascii').strip()
            except UnicodeDecodeError:
                return False

            if device_info != "TEST1CH":
                return False

            # Success: update label
            self.device_info_label.setText(f"Device Info: {device_info}")
            return True

        except Exception as e:
            QMessageBox.critical(self, "Serial error", str(e))
            return False

    # ----------------------------------------------------------------------
    # CAN Transmit
    # ----------------------------------------------------------------------
    def send_can_message(self):
        """Build and send a CAN frame over USB if connected."""
        if self.serial is None or not self.serial.is_open:
            QMessageBox.warning(self, "Not connected", "Connect to device first.")
            return

        try:
            # Parse CAN ID as hex
            can_id_text = self.tx_id.text().strip()
            can_id = int(can_id_text, 16)

            # Parse DLC
            dlc = int(self.tx_dlc.text().strip())
            if not (0 <= dlc <= 8):
                raise ValueError("DLC must be 0..8")

            # Parse data bytes
            data_str = self.tx_data.text().strip()
            data_bytes = bytes()
            if data_str:
                data_bytes = bytes.fromhex(data_str)
            if len(data_bytes) > 8:
                raise ValueError("Max 8 data bytes")

            data_bytes = data_bytes.ljust(8, b'\x00')

            # Build message: [0x30][ID4][DLC][DATA8]
            msg = bytearray()
            msg.append(0x30)
            msg += can_id.to_bytes(4, 'little')
            msg.append(dlc)
            msg += data_bytes

            self.serial.write(msg)

        except ValueError as e:
            QMessageBox.warning(self, "Input error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Serial error", str(e))

    # ----------------------------------------------------------------------
    # Periodic RX polling (CAN frames from STM32)
    # ----------------------------------------------------------------------
    def poll_serial(self):
        if self.serial is None or not self.serial.is_open:
            return

        try:
            while True:
                b = self.serial.read(1)
                if not b:
                    return  # no more data this cycle

                # look for CAN RX header
                if b[0] != 0x31:
                    continue

                # now get the remaining 13 bytes (may come in pieces)
                rest = bytearray()
                while len(rest) < 13:
                    chunk = self.serial.read(13 - len(rest))
                    if not chunk:
                        return  # wait for next timer tick
                    rest.extend(chunk)

                # decode frame
                can_id = int.from_bytes(rest[0:4], 'little')
                dlc = rest[4]
                if dlc > 8:
                    dlc = 8
                data = rest[5:13]

                data_hex = " ".join(f"{b:02X}" for b in data[:dlc])
                self.add_rx_row(can_id, dlc, data_hex)

        except serial.SerialException as e:
            self.rx_timer.stop()
            self.close_serial()
            self.update_ui_disconnected()
            QMessageBox.critical(self, "Serial error", str(e))


    def add_rx_row(self, can_id: int, dlc: int, data_hex: str):
        row = self.rx_table.rowCount()
        self.rx_table.insertRow(row)
        self.rx_table.setItem(row, 0, QTableWidgetItem(f"0x{can_id:X}"))
        self.rx_table.setItem(row, 1, QTableWidgetItem(str(dlc)))
        self.rx_table.setItem(row, 2, QTableWidgetItem(data_hex))
        self.rx_table.scrollToBottom()

    # ----------------------------------------------------------------------
    # UI state updates
    # ----------------------------------------------------------------------
    def update_ui_connected(self):
        self.status_label.setText("Status: Connected")
        self.connect_button.setText("Disconnect")

    def update_ui_disconnected(self):
        self.status_label.setText("Status: Disconnected")
        self.device_info_label.setText("Device Info: -")
        self.connect_button.setText("Connect")


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(600, 400)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
