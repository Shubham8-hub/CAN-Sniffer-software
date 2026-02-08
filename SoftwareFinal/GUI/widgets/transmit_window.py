# from PySide6.QtWidgets import QTableView, QHeaderView
# from PySide6.QtGui import QStandardItemModel
# from .detachable_widget import DetachableWidget
#
# class TransmitWindow(DetachableWidget):
#     def __init__(self, parent_callback=None):
#         super().__init__(title="CAN Transmit")
#         self.parent_callback = parent_callback
#
#         self.table = QTableView()
#         self.set_child(self.table)
#
#         # Simple Transmit UI Columns
#         self.model = QStandardItemModel()
#         self.model.setHorizontalHeaderLabels(["ID (Hex)", "DLC", "Data (Hex)", "Cycle (ms)", "Count", "Status", "Action"])
#         self.table.setModel(self.model)
#
#         header = self.table.horizontalHeader()
#         header.setSectionResizeMode(QHeaderView.Stretch)

# GUI/widgets/transmit_window.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QLineEdit, QRadioButton, QSpinBox,
    QPushButton, QGroupBox, QScrollArea, QFrame, QHeaderView, QTableView
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QIntValidator, QRegularExpressionValidator
from PySide6.QtCore import Qt, QTimer, QRegularExpression, Signal
from .detachable_widget import DetachableWidget
from CORE.CAN.can_transmit import CanTransmitLogic
import time

class TransmitWindow(DetachableWidget):

    message_sent = Signal(dict)

    def __init__(self, serial_mgr=None):
        super().__init__(title="CAN Transmit")

        self.serial_mgr = serial_mgr
        self.logic = CanTransmitLogic(serial_mgr)

        # Store timers for periodic messages: {row_index: QTimer}
        self.active_timers = {}

        self.container_widget = QWidget()

        self.main_layout = QVBoxLayout(self.container_widget)

        self.set_child(self.container_widget)

        # --- Main Layout ---
        # self.main_layout = QVBoxLayout()


        # 1. Input Config Area
        self._setup_input_area()

        # 2. Data Byte Grid (D0 - D63)
        self._setup_data_grid()

        # 3. Message Table
        self._setup_table()

        # Connect signals
        self.combo_type.currentIndexChanged.connect(self._on_can_type_changed)
        self.radio_periodic.toggled.connect(self._toggle_interval_input)

        # Initialize View
        self._on_can_type_changed()  # Set initial state for data grid

    def _setup_input_area(self):
        """Creates the top configuration form."""
        config_group = QGroupBox("Message Configuration")
        layout = QGridLayout(config_group)

        # --- Row 0: CAN Type & Channel ---
        layout.addWidget(QLabel("CAN Type:"), 0, 0)
        self.combo_type = QComboBox()
        self.combo_type.addItems(["CAN Classic", "CAN FD"])
        layout.addWidget(self.combo_type, 0, 1)

        layout.addWidget(QLabel("Channel:"), 0, 2)
        self.combo_channel = QComboBox()
        self.combo_channel.addItems(["Channel 0", "Channel 1"])
        layout.addWidget(self.combo_channel, 0, 3)

        # --- Row 1: ID & Cycle ---
        layout.addWidget(QLabel("CAN ID (Hex):"), 1, 0)
        self.txt_id = QLineEdit()
        self.txt_id.setPlaceholderText("e.g. 123")
        # Validator for Hex (3 chars for std, 8 for ext)
        reg_ex = QRegularExpression("^[0-9A-Fa-f]{1,8}$")
        self.txt_id.setValidator(QRegularExpressionValidator(reg_ex))
        layout.addWidget(self.txt_id, 1, 1)

        # Frequency Mode
        self.mode_layout = QHBoxLayout()
        self.radio_one_shot = QRadioButton("One Shot")
        self.radio_periodic = QRadioButton("Periodic")
        self.radio_one_shot.setChecked(True)
        self.mode_layout.addWidget(self.radio_one_shot)
        self.mode_layout.addWidget(self.radio_periodic)
        layout.addLayout(self.mode_layout, 1, 2)

        # Interval Input
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(10, 10000)
        self.spin_interval.setValue(100)
        self.spin_interval.setSuffix(" ms")
        self.spin_interval.setEnabled(False)  # Disabled by default
        layout.addWidget(self.spin_interval, 1, 3)

        # Add Button
        self.btn_add_msg = QPushButton("Add Message to List")
        self.btn_add_msg.setStyleSheet("background-color: #0a5fc7; color: white; font-weight: bold;")
        self.btn_add_msg.clicked.connect(self._add_message_to_table)
        layout.addWidget(self.btn_add_msg, 0, 4, 2, 1)  # Span 2 rows

        self.main_layout.addWidget(config_group)

    def _setup_data_grid(self):
        """Creates the grid of 64 input boxes for data bytes."""
        self.data_group = QGroupBox("Data Bytes (Hex)")
        self.data_layout = QVBoxLayout(self.data_group)

        # Scroll Area is useful if 64 bytes take too much space
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(180)  # Limit height

        container = QWidget()
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(5)

        self.byte_inputs = []  # List to store QLineEdits

        # Create 64 Input Boxes
        for i in range(64):
            # Input Box
            le = QLineEdit()
            le.setPlaceholderText(f"{i:02X}")
            le.setMaxLength(2)
            le.setAlignment(Qt.AlignCenter)
            le.setFixedWidth(35)
            # Hex Validator
            le.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9A-Fa-f]{2}")))

            self.byte_inputs.append(le)

            # Add to grid: 8 columns per row
            row = i // 8
            col = i % 8
            self.grid_layout.addWidget(QLabel(f"D{i}"), row * 2, col, alignment=Qt.AlignCenter)
            self.grid_layout.addWidget(le, (row * 2) + 1, col)

        scroll.setWidget(container)
        self.data_layout.addWidget(scroll)
        self.main_layout.addWidget(self.data_group)

    def _setup_table(self):
        """Creates the table to list messages."""
        self.table = QTableView()
        self.model = QStandardItemModel()

        headers = ["ID", "Channel", "Type", "DLC", "Data payload", "Mode", "Interval", "Status", "Action"]
        self.model.setHorizontalHeaderLabels(headers)
        self.table.setModel(self.model)

        # Formatting
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # Set column widths
        self.table.setColumnWidth(4, 300)  # Data column wider

        self.main_layout.addWidget(self.table)

    # --- Logic Methods ---

    def _on_can_type_changed(self):
        """Shows 8 bytes for Classic CAN, 64 for CAN FD."""
        is_fd = self.combo_type.currentIndex() == 1  # 0=Classic, 1=FD
        max_bytes = 64 if is_fd else 8

        # Loop through all 64 inputs and hide/show based on type
        for i, le in enumerate(self.byte_inputs):
            # We need to find the label associated with this input to hide it too
            # Logic: In grid, Label is at (row*2, col), Widget is at (row*2 + 1, col)
            row = i // 8
            col = i % 8

            label_item = self.grid_layout.itemAtPosition(row * 2, col)
            input_item = self.grid_layout.itemAtPosition((row * 2) + 1, col)

            if i < max_bytes:
                if label_item: label_item.widget().show()
                if input_item: input_item.widget().show()
            else:
                if label_item: label_item.widget().hide()
                if input_item: input_item.widget().hide()

    def _toggle_interval_input(self):
        """Enables interval input only if Periodic is selected."""
        self.spin_interval.setEnabled(self.radio_periodic.isChecked())

    def _add_message_to_table(self):
        """Reads inputs and adds a row to the table."""
        # 1. Validate ID
        can_id_str = self.txt_id.text().strip()
        if not can_id_str:
            return  # TODO: Show Error Message

        try:
            can_id = int(can_id_str, 16)
        except ValueError:
            return

        # 2. Collect Data
        data_bytes = []
        is_fd = self.combo_type.currentIndex() == 1
        limit = 64 if is_fd else 8

        for i in range(limit):
            txt = self.byte_inputs[i].text().strip()
            if txt:
                try:
                    val = int(txt, 16)
                    data_bytes.append(val)
                except ValueError:
                    pass  # Ignore invalid inputs

        # Formatted string for table
        data_str = " ".join([f"{b:02X}" for b in data_bytes])

        # 3. Mode Info
        is_periodic = self.radio_periodic.isChecked()
        interval = self.spin_interval.value() if is_periodic else 0
        mode_str = "Periodic" if is_periodic else "One Shot"
        interval_str = f"{interval} ms" if is_periodic else "-"

        # 4. Create Table Row
        row_items = [
            QStandardItem(f"{can_id:X}"),  # ID
            QStandardItem(str(self.combo_channel.currentIndex())),  # Channel
            QStandardItem("FD" if is_fd else "STD"),  # Type
            QStandardItem(str(len(data_bytes))),  # DLC
            QStandardItem(data_str),  # Data
            QStandardItem(mode_str),  # Mode
            QStandardItem(interval_str),  # Interval
            QStandardItem("Ready"),  # Status
            QStandardItem("")  # Action (Placeholder for button)
        ]

        self.model.appendRow(row_items)
        row_idx = self.model.rowCount() - 1

        # 5. Add "Send" Button to the last column
        btn_action = QPushButton("Send")
        if is_periodic:
            btn_action.setText("Start")
            btn_action.setCheckable(True)
            btn_action.clicked.connect(lambda checked, r=row_idx: self._handle_periodic_send(checked, r))
        else:
            btn_action.clicked.connect(lambda _, r=row_idx: self._handle_one_shot_send(r))

        self.table.setIndexWidget(self.model.index(row_idx, 8), btn_action)

    # --- Sending Logic ---

    def _handle_one_shot_send(self, row_idx):
        packet_bytes = self._build_packet_from_row(row_idx)
        if packet_bytes:
            # 1. Send to Hardware
            success = self.logic.send(packet_bytes)

            if success:
                self.model.setItem(row_idx, 7, QStandardItem("Sent"))

                # 2. Create a "Ghost" Packet for the Trace Window
                trace_packet = self._create_trace_packet(row_idx)

                # 3. Emit Signal
                self.message_sent.emit(trace_packet)

    def _handle_periodic_send(self, is_running, row_idx):
        """Starts or Stops the timer for periodic sending."""
        btn = self.table.indexWidget(self.model.index(row_idx, 8))

        if is_running:
            # START
            btn.setText("Stop")
            self.model.setItem(row_idx, 7, QStandardItem("Running..."))

            # Get Interval
            interval_str = self.model.item(row_idx, 6).text()
            interval = int(interval_str.split()[0])

            # Create Timer
            timer = QTimer()
            timer.timeout.connect(lambda: self._send_periodic_tick(row_idx))
            timer.start(interval)
            self.active_timers[row_idx] = timer
        else:
            # STOP
            btn.setText("Start")
            self.model.setItem(row_idx, 7, QStandardItem("Stopped"))

            if row_idx in self.active_timers:
                self.active_timers[row_idx].stop()
                del self.active_timers[row_idx]

    def _send_periodic_tick(self, row_idx):
        packet_bytes = self._build_packet_from_row(row_idx)
        if packet_bytes:
            self.logic.send(packet_bytes)

            # Emit to Trace
            trace_packet = self._create_trace_packet(row_idx)
            self.message_sent.emit(trace_packet)

    def _create_trace_packet(self, row_idx):
        """Creates a dictionary formatted exactly like 'can_worker' packets."""

        # Extract raw string data from table
        can_id_hex = self.model.item(row_idx, 0).text()
        channel = self.model.item(row_idx, 1).text()
        type_str = self.model.item(row_idx, 2).text()
        dlc = self.model.item(row_idx, 3).text()
        data_str = self.model.item(row_idx, 4).text()

        # Process Data
        data_bytes = [int(x, 16) for x in data_str.split()] if data_str else []

        return {
            'timestamp': f"{time.time() % 1000:.3f}",
            'can_id': can_id_hex,
            'type': type_str,  # 'STD' or 'FD'
            'direction': 'Tx',  # <--- Important: Shows as Transmit
            'channel': int(channel),
            'dlc': int(dlc),
            'data': data_bytes
        }

    def _build_packet_from_row(self, row_idx):
        """Reconstructs the binary packet from table data."""
        try:
            can_id = int(self.model.item(row_idx, 0).text(), 16)
            channel = int(self.model.item(row_idx, 1).text())
            type_str = self.model.item(row_idx, 2).text()
            data_str = self.model.item(row_idx, 4).text()

            data_bytes = [int(x, 16) for x in data_str.split()] if data_str else []
            is_fd = (type_str == "FD")

            return self.logic.create_packet(can_id, channel, data_bytes, is_fd)
        except Exception as e:
            print(f"Error building packet: {e}")
            return None