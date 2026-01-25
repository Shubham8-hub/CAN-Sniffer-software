import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QComboBox, QLabel

class SnifferApp(QWidget):
    def __init__(self):
        super().__init__()

        self.ser = None

        self.setWindowTitle("STM32 Sniffer Interface")

        layout = QVBoxLayout()

        # Port selector
        self.portBox = QComboBox()
        layout.addWidget(self.portBox)

        # Refresh button
        refreshBtn = QPushButton("Refresh COM Ports")
        refreshBtn.clicked.connect(self.load_ports)
        layout.addWidget(refreshBtn)

        # Connect button
        connectBtn = QPushButton("Connect")
        connectBtn.clicked.connect(self.connect_device)
        layout.addWidget(connectBtn)

        # Status label
        self.status = QLabel("Disconnected")
        layout.addWidget(self.status)

        # Device info display
        self.info = QLabel("Device Info: -")
        layout.addWidget(self.info)

        self.setLayout(layout)

        self.load_ports()

    def load_ports(self):
        self.portBox.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.portBox.addItem(p.device)

    def connect_device(self):
        port = self.portBox.currentText()
        if not port:
            self.status.setText("No COM port selected!")
            return

        try:
            self.ser = serial.Serial(port, 115200, timeout=2)
            self.status.setText("Connected. Sending command 0x10 ...")
        except:
            self.status.setText("Failed to open port!")
            return

        # Send command 0x10
        self.ser.write(bytes([0x10]))

        # Expecting: ACK (0x55) + text
        response = self.ser.read(20)
        print("DEBUG RAW RESPONSE:", response)

        if response and response[0] == 0x55:
            device_info = response[1:].decode(errors="ignore")
            self.info.setText(f"Device Info: {device_info}")
            self.status.setText(f"Connected to {port}")
        else:
            self.status.setText(f"Invalid response. Raw={response}")

        if len(response) >= 2 and response[0] == 0x55:  # ACK
            device_info = response[1:].decode(errors="ignore")
            self.info.setText(f"Device Info: {device_info}")
            self.status.setText(f"Connected to {port}")
        else:
            self.status.setText("Invalid response received!")

app = QApplication(sys.argv)
window = SnifferApp()
window.show()
sys.exit(app.exec_())
