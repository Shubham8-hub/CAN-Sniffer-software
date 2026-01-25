# from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
#                                QVBoxLayout, QLabel, QTableView, QStackedWidget)
#
#
# from CORE.helpers.device_record import state
#
# class SettingWindow(QWidget):
#
#     def __init__(self):
#         super().__init__()
#         # layout = QVBoxLayout()
#         # layout.addWidget(QLabel("Setting"))
#         # # layout.addWidget(TraceWindow())
#         # self.setLayout(layout)
#         self.setup_ui()
#
#         state.connection_changed.connect(self.refresh_ui)
#
#         self.refresh_ui(state.is_connected)
#
#     def setup_ui(self):


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QStackedWidget,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout
)
from PySide6.QtCore import Qt
from CORE.helpers.device_record import state


class SettingWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 1. Initialize UI
        self.setup_ui()

        # 2. Connect to global state signal
        # Whenever serial.py updates the connection, this function runs
        state.connection_changed.connect(self.refresh_ui)

        # 3. Check initial state
        self.refresh_ui(state.is_connected)

    def setup_ui(self):
        """Create the different views for the settings page."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # We use QStackedWidget to swap between Disconnected and Connected screens
        self.stack = QStackedWidget()

        # --- VIEW 1: Disconnected State ---
        self.disconnected_view = QWidget()
        disc_layout = QVBoxLayout(self.disconnected_view)

        self.msg_label = QLabel("Device Not Connected\n\nPlease go to Serial Communication and connect to a device.")
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setStyleSheet("color: #7f8c8d; font-size: 16px; font-weight: bold;")

        disc_layout.addStretch()
        disc_layout.addWidget(self.msg_label)
        disc_layout.addStretch()

        # --- VIEW 2: Connected State ---
        self.connected_view = QWidget()
        conn_layout = QVBoxLayout(self.connected_view)
        conn_layout.setContentsMargins(20, 20, 20, 20)

        # Example Content: CAN Channel Configuration
        self.gb_config = QGroupBox("Device Runtime Configuration")
        config_grid = QGridLayout(self.gb_config)

        # We will update these values in refresh_ui
        self.lbl_sn = QLabel(f"Hardware Serial: -")
        self.lbl_chan_count = QLabel(f"Active Channels: -")

        config_grid.addWidget(self.lbl_sn, 0, 0)
        config_grid.addWidget(self.lbl_chan_count, 1, 0)

        conn_layout.addWidget(self.gb_config)

        # A container to show specific channel settings (Baudrate etc)
        self.channels_container = QGroupBox("Active CAN Channels Details")
        self.channels_vbox = QVBoxLayout(self.channels_container)
        conn_layout.addWidget(self.channels_container)

        conn_layout.addStretch()  # Pushes everything to the top

        # Add views to stack
        self.stack.addWidget(self.disconnected_view)  # Index 0
        self.stack.addWidget(self.connected_view)  # Index 1

        self.main_layout.addWidget(self.stack)

        # Styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdbdbd;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QLabel {
                font-size: 13px;
            }
        """)

    def refresh_ui(self, is_connected):
        """Handles the logic of what the user sees based on connection state."""
        if is_connected:
            # Switch to Connected View
            self.stack.setCurrentIndex(1)

            # Update specific labels using the shared 'state'
            self.lbl_sn.setText(f"Hardware Serial: {state.serial_no}")
            self.lbl_chan_count.setText(f"Active Channels: {state.num_channel}")

            # Clear old channel items from the settings list
            for i in reversed(range(self.channels_vbox.count())):
                self.channels_vbox.itemAt(i).widget().setParent(None)

            # Re-build channel list dynamically
            for ch in state.channels:
                ch_row = QLabel(f"● CH {ch['id']}: Mode {ch['type']} | Running at {ch['speed']} bps")
                self.channels_vbox.addWidget(ch_row)

        else:
            # Switch back to the blank "Please Connect" View
            self.stack.setCurrentIndex(0)