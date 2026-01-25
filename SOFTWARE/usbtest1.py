# can_sniffer_gui.py
import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QComboBox, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer

REQUEST_BYTE = b'\x10'
ACK_BYTE = b'\x55'
DEVICE_INFO_EXPECTED = b'TEST2CHFD'  # used only for visual verification

class SerialReaderThread(QThread):
    received = pyqtSignal(bytes)   # raw bytes
    error = pyqtSignal(str)

    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self._running = True

    def run(self):
        try:
            while self._running and self.ser and self.ser.is_open:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        self.received.emit(data)
                self.msleep(50)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._running = False
        self.wait(200)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAN Sniffer - Connector")
        self.resize(420, 180)

        self.ser = None
        self.reader = None
        self.buffer = b''

        layout = QVBoxLayout()
        top = QHBoxLayout()

        self.port_combo = QComboBox()
        self.refresh_ports()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_ports)

        top.addWidget(QLabel("Port:"))
        top.addWidget(self.port_combo)
        top.addWidget(self.refresh_btn)

        layout.addLayout(top)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connect)
        layout.addWidget(self.connect_btn)

        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.info_label = QLabel("Device Info: -")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

        # auto refresh ports every 5s (optional)
        self.port_timer = QTimer(self)
        self.port_timer.timeout.connect(self.refresh_ports)
        self.port_timer.start(5000)

    def refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.port_combo.addItem(p.device + " - " + (p.description or ""))
        if current:
            idx = self.port_combo.findText(current)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)

    def toggle_connect(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port_text = self.port_combo.currentText().split(" - ")[0]
        if not port_text:
            QMessageBox.warning(self, "No port", "Select a port first.")
            return
        try:
            # adjust baudrate if using UART. For USB CDC baud doesn't matter but set something.
            self.ser = serial.Serial(port_text, 115200, timeout=0.2)
        except Exception as e:
            QMessageBox.critical(self, "Open port failed", str(e))
            self.ser = None
            return

        # start background reader
        self.reader = SerialReaderThread(self.ser)
        self.reader.received.connect(self.on_data_received)
        self.reader.error.connect(self.on_reader_error)
        self.reader.start()

        # send the request byte 0x10
        try:
            self.buffer = b''
            self.ser.write(REQUEST_BYTE)
        except Exception as e:
            QMessageBox.critical(self, "Send failed", str(e))
            self.disconnect()
            return

        self.status_label.setText("Status: Waiting for device reply...")
        self.connect_btn.setText("Disconnect")

        # if you want a timeout, use a QTimer (e.g., 3 seconds)
        self.response_timer = QTimer(self)
        self.response_timer.setSingleShot(True)
        self.response_timer.timeout.connect(self.on_response_timeout)
        self.response_timer.start(3000)

    def disconnect(self):
        if hasattr(self, 'response_timer') and self.response_timer.isActive():
            self.response_timer.stop()
        if self.reader:
            self.reader.stop()
            self.reader = None
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
            self.ser = None
        self.status_label.setText("Status: Disconnected")
        self.connect_btn.setText("Connect")
        self.info_label.setText("Device Info: -")
        self.buffer = b''

    def on_response_timeout(self):
        # timeout if no ack
        self.status_label.setText("Status: No reply (timeout)")
        # keep connection open so user can retry; or disconnect automatically:
        # self.disconnect()

    def on_reader_error(self, errmsg):
        QMessageBox.critical(self, "Reader error", errmsg)
        self.disconnect()

    def on_data_received(self, data: bytes):
        # append to buffer and parse
        self.buffer += data

        # parse simple scheme: look for 0x55 then ASCII after it
        # If there might be noise before ack, search for 0x55 position:
        pos = self.buffer.find(ACK_BYTE)
        if pos == -1:
            # ack not yet received
            return

        # everything after ack is the device string (we assume device sends it immediately)
        # take everything after first ACK as device info
        device_info = self.buffer[pos + 1:]  # raw bytes after ack
        # trim control characters/newlines
        device_info = device_info.strip(b'\r\n\x00')

        # Some devices may send ack and device info in multiple packets; if device_info empty, wait more
        if len(device_info) == 0:
            # wait for more bytes
            return

        # Good: we got ack + immediate payload
        self.response_timer.stop()
        self.status_label.setText("Status: Connected")
        # decode safely
        try:
            info_str = device_info.decode('ascii', errors='ignore')
        except:
            info_str = repr(device_info)
        self.info_label.setText("Device Info: " + info_str)
        # Optionally verify expected string
        if device_info.startswith(DEVICE_INFO_EXPECTED):
            # success
            pass
        # If you want continuous listening for further messages, keep reader running
        # If you prefer one-shot, stop reading:
        # self.reader.stop()

    def closeEvent(self, event):
        self.disconnect()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
