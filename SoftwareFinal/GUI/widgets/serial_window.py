from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox,
    QPushButton, QGridLayout, QGroupBox,
)
from PySide6.QtCore import Qt
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

from CORE.serial.serial import SerialManager

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "..", "resources", "icons", "refresh.png")

class SerialWindow(QWidget):

    def __init__(self):
        super().__init__()

        # base_path = os.path.dirname(os.path.abspath(__file__))
        # refresh_icon = os.path.join(base_path, "../resources/icons/refresh.jpg")

        self._create_widgets()
        self._setup_ui()
        self._populate_ports()

        self.serial_mgr = SerialManager()
        self.serial_mgr.connected.connect(self.on_connected)
        self.serial_mgr.error.connect(self.on_error)
        self.serial_mgr.busy.connect(self.on_busy)
        self.serial_mgr.disconnected.connect(self._reset_ui)

        self.btn_connect.clicked.connect(self._on_connect_clicked)

        self.is_connected = False

    # ---------------- Widgets ----------------
    def _create_widgets(self):
        # Serial selection widgets
        self.label_com = QLabel("COM Port:")
        self.combo_com = QComboBox()
        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(QIcon(ICON_PATH))
        self.btn_refresh.setIconSize(QSize(18, 18))
        self.btn_refresh.setFixedSize(32, 32)
        self.btn_refresh.setToolTip("Refresh")

        self.btn_connect = QPushButton("Connect")

        self.label_serial_no = QLabel("Serial No: -")
        self.label_fw_version = QLabel("FW Version: -")
        self.label_num_channels = QLabel("No. of CAN Channels: -")

        # This label will show CH0: CANFD @ 800000... etc.
        self.label_channels_summary = QLabel("Channel Details:\n-")
        self.label_channels_summary.setWordWrap(True)
        self.label_channels_summary.setStyleSheet("color: #07912a; font-weight: normal;") #Green color
        # self.label_channels_summary.setStyleSheet("color: #b50a07; font-weight: normal;") #Red Color
        # self.label_channels_summary.setStyleSheet("color: #c4b50a; font-weight: normal;") #yellow color
        # self.label_channels_summary.setStyleSheet("color: #077391; font-weight: normal;") #light blue

    # ---------------- UI ----------------
    def _setup_ui(self):
        main_layout = QVBoxLayout()

        # -------- GroupBox 1: Serial Port --------
        gb_serial = QGroupBox("Serial Communication")
        gb_serial.setAlignment(Qt.AlignLeft)

        serial_layout = QGridLayout(gb_serial)
        serial_layout.setSpacing(8)

        serial_layout.addWidget(self.label_com, 0, 0)
        serial_layout.addWidget(self.combo_com, 0, 1)
        serial_layout.addWidget(self.btn_refresh, 0, 2)
        serial_layout.addWidget(self.btn_connect, 1, 1)

        # -------- GroupBox 2: Device Info --------
        gb_device = QGroupBox("Device Information")
        gb_device.setAlignment(Qt.AlignLeft)

        device_layout = QVBoxLayout(gb_device)
        device_layout.setSpacing(10)

        # Add the labels to the device info box
        device_layout.addWidget(self.label_serial_no)
        device_layout.addWidget(self.label_fw_version)
        device_layout.addWidget(self.label_num_channels)

        # Add a separator line or just the details
        # device_layout.addWidget(QLabel("___________________________"))
        device_layout.addWidget(self.label_channels_summary)
        device_layout.addStretch()

        # Add to main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(20, 20, 20, 20) #(left,top,right, bottom)

        main_layout.addWidget(gb_serial)
        main_layout.addSpacing(40)
        main_layout.addWidget(gb_device)
        main_layout.addStretch()

        # -------- Styling --------
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdbdbd;
                border-radius: 6px;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
            QLabel {
                font-weight: bold;
            }
            QComboBox {
                padding: 4px;
                min-width: 200px;
            }
            QPushButton {
                padding: 4px 12px;
            }
        """)

        self.btn_refresh.clicked.connect(self._populate_ports)

    # ---------------- Logic ----------------
    def _populate_ports(self):
        self.combo_com.clear()

        for port in QSerialPortInfo.availablePorts():
            text = f"{port.portName()} - {port.description()}"
            self.combo_com.addItem(text, port.portName())

    def selected_port(self):
        return self.combo_com.currentData()

    def _on_connect_clicked(self):
        if not self.is_connected:
            port = self.combo_com.currentData()
            if not port:
                return
            self.serial_mgr.connect_device(port)
        else:
            self.serial_mgr.disconnect_device()

    def on_connected(self, info):
        self.label_serial_no.setText(f"Serial No: {info['serial_no']}")
        self.label_fw_version.setText(f"FW Version: {info['fw']}")

        # Fix: ensure info['num_channels'] matches the key in serial.py
        self.label_num_channels.setText(f"No. of CAN Channels: {info['num_channels']}")

        channel_text = "Channel Details:\n"
        for ch in info['channels']:
            channel_text += f"• CH{ch['id']}: {ch['type']} @ {ch['speed']} bps\n"

        # USE THE MATCHING NAME HERE
        self.label_channels_summary.setText(channel_text)

        self.is_connected = True
        self.btn_connect.setText("Disconnect")
        self.btn_connect.setEnabled(True)

    def on_error(self, info):
        self.btn_connect.setText("Connect")
        print("Error:", info)

    def on_busy(self, state: bool):
        self.btn_connect.setEnabled(not state)

        if state and not self.is_connected:
            self.btn_connect.setText("Connecting....")

    def _reset_ui(self):
        self.is_connected = False

        self.label_serial_no.setText("Serial No: -")
        self.label_fw_version.setText("FW Version: -")
        self.label_num_channels.setText("No. of CAN Channels: -")
        self.label_channels_summary.setText("Channels: -")

        self.btn_connect.setText("Connect")
        self.btn_connect.setEnabled(True)

