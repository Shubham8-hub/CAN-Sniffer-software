from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QStackedWidget,
                               QGridLayout, QGroupBox, QComboBox, QPushButton)
from PySide6.QtCore import Qt
from CORE.helpers.device_record import state
from CORE.helpers.command import Command


class ChannelConfigBox(QGroupBox):
    def __init__(self, ch_info, serial_mgr):
        super().__init__(f"Channel {ch_info['id']}")
        self.ch_id = ch_info['id']

        self.serial_mgr = serial_mgr

        # --- FIX: MULTIPLY BY 10 ---

        self.max_speed = ch_info['max_speed']

        self.current_speed = ch_info['current_speed']


        self.lbl_current_val = QLabel("unknown") # place holder
        self.lbl_current_val.setStyleSheet("color: #0a5fc7; font-weight: bold;")

        self.setup_ui(ch_info)

        if self.serial_mgr:
            self.serial_mgr.baud_read_response.connect(self.on_baud_read)

    def setup_ui(self, info):
        layout = QGridLayout(self)

        # Row 0: CAN Type and Max Speed
        layout.addWidget(QLabel("CAN Type :"), 0, 0)
        layout.addWidget(QLabel(info['type']), 0, 1)

        layout.addWidget(QLabel("Baudrate Max :"), 0, 2)

        # Format label to show Mbps correctly
        if self.max_speed >= 1000000:
            max_text = f"{self.max_speed / 1000000:.0f} MBPS"
        else:
            max_text = f"{self.max_speed / 1000:.0f} KBPS"

        lbl_max_val = QLabel(max_text)
        lbl_max_val.setStyleSheet("color: #07912a; font-weight: bold;")
        layout.addWidget(lbl_max_val, 0, 3)

        # Row 1: Set Baudrate (Filtered)
        layout.addWidget(QLabel("Set Baudrate :"), 1, 0)
        self.combo_baud = QComboBox()

        # Now the math will work:
        # For CH0: self.max_speed is 8,000,000.
        # rate['bps'] 8,000,000 <= 8,000,000 is True.
        for rate in Command.BAUD_RATES:
            if rate['bps'] <= self.max_speed:
                self.combo_baud.addItem(rate['label'], rate['cmd'])

        layout.addWidget(self.combo_baud, 1, 1)

        layout.addWidget(QLabel("Current Baudrate :"), 1, 2)
        layout.addWidget(self.lbl_current_val, 1, 3)

        # Row 2: Buttons
        btn_set = QPushButton("Set Baudrate")
        btn_set.setStyleSheet("background-color: #45a307; padding: 6px; font-weight: bold;")
        btn_set.clicked.connect(self.apply_baudrate)

        btn_read = QPushButton("Read Baudrate")
        btn_read.setStyleSheet("background-color: #0a5fc7; padding: 6px; font-weight: bold;")
        btn_read.clicked.connect(self.read_baudrate)

        layout.addWidget(btn_set, 2, 0, 1, 2)
        layout.addWidget(btn_read, 2, 2, 1, 2)

    def update_current_label(self, speed):
        # Helper to format the text nicely
        if speed >= 1000000:
            txt = f"{speed / 1000000:.1f} MBPS"
        elif speed > 0:
            txt = f"{speed / 1000:.0f} KBPS"
        else:
            txt = "Unknown"
        self.lbl_current_val.setText(txt)

    def apply_baudrate(self):
        cmd_baud_byte = self.combo_baud.currentData()
        # Packet formed : [0x33, Channel, BaudCmd]
        packet = bytes([Command.CMD_SET_BAUDRATE, self.ch_id, cmd_baud_byte])

        if self.serial_mgr:
            self.serial_mgr.write_data(packet)
            print(f"Sending Set Baud: Cmd={cmd_baud_byte} for Ch={self.ch_id}")

            # If autoread is needed to verify
            # self.read_baudrate()

    def read_baudrate(self):
        if self.serial_mgr:
            # --- Send 2 Bytes [READ_CMD, CH_ID] ---
            packet = bytes([Command.CMD_READ_BAUDRATE, self.ch_id])
            self.serial_mgr.write_data(packet)
            print(f"Sending Read Baud: Ch={self.ch_id}")

    def on_baud_read(self, ch_id, speed):
        # Only update if the response is for THIS channel
        if ch_id == self.ch_id:
            self.update_current_label(speed)
            print(f"UI Updated: Ch{ch_id} -> {speed}")


class SettingWindow(QWidget):
    def __init__(self, serial_mgr):
        super().__init__()
        self.serial_mgr = serial_mgr
        self.setup_ui()
        state.connection_changed.connect(self.refresh_ui)
        self.refresh_ui(state.is_connected)

        # self.serial_mgr.connected.connect(self.on_connected)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.stack = QStackedWidget()

        self.disc_view = QLabel("Device Not Connected")
        self.disc_view.setAlignment(Qt.AlignCenter)

        self.conn_view = QWidget()
        self.scroll_layout = QVBoxLayout(self.conn_view)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.stack.addWidget(self.disc_view)
        self.stack.addWidget(self.conn_view)
        self.layout.addWidget(self.stack)

    def refresh_ui(self, is_connected):
        if is_connected:
            self.stack.setCurrentIndex(1)
            while self.scroll_layout.count():
                child = self.scroll_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            for ch in state.channels:
                self.scroll_layout.addWidget(ChannelConfigBox(ch, self.serial_mgr))
        else:
            self.stack.setCurrentIndex(0)