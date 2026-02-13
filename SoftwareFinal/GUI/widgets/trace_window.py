
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView,
                               QHeaderView, QPushButton, QFrame, QGridLayout,
                               QLabel, QCheckBox, QLineEdit, QComboBox, QSpacerItem, QSizePolicy)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush, QIcon
from PySide6.QtCore import Qt
from .detachable_widget import DetachableWidget
from CORE.CAN.can_receive import CanReceiveLogic

from CORE.helpers.command import Command

class TraceWindow(DetachableWidget):
    def __init__(self, worker_thread=None):
        super().__init__(title="CAN Trace")

        self.worker_thread = worker_thread
        self.logic = CanReceiveLogic()

        # --- Layouts ---
        self.content_layout = QHBoxLayout()
        self.set_child_layout(self.content_layout)

        # --- Table (Left) ---
        self.table_container = QWidget()
        self.table_layout = QVBoxLayout(self.table_container)
        self.table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableView()
        # Hide default vertical numbers (using our own Sr. column)
        self.table.verticalHeader().setVisible(False)

        self.model = QStandardItemModel()
        self.table.setModel(self.model)
        self.table.setStyleSheet(
            "QTableView { selection-background-color: #444; alternate-background-color: #2b2b2b; }")
        self.table.setAlternatingRowColors(True)

        self.table_layout.addWidget(self.table)
        self.content_layout.addWidget(self.table_container, stretch=4)

        # --- Settings (Right - Hidden by Default) ---
        self.settings_panel = QFrame()
        self.settings_panel.setFrameShape(QFrame.StyledPanel)
        self.settings_panel.setFixedWidth(250)
        self.settings_panel.hide()

        self._build_settings_ui()
        self.content_layout.addWidget(self.settings_panel, stretch=1)

        # --- Toggle Button ---
        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.setCheckable(True)
        self.btn_settings.clicked.connect(self.toggle_settings)
        self.table_layout.insertWidget(0, self.btn_settings, alignment=Qt.AlignRight)

        self.setup_columns()

    def set_child_layout(self, layout):
        container_widget = QWidget()
        container_widget.setLayout(layout)
        self.set_child(container_widget)

    def toggle_settings(self):
        if self.btn_settings.isChecked():
            self.settings_panel.show()
        else:
            self.settings_panel.hide()

    def _build_settings_ui(self):
        layout = QVBoxLayout(self.settings_panel)

        layout.addWidget(QLabel("<b>Trace Settings</b>"))

        # --- NEW: Start / Stop Buttons ---
        btn_layout = QHBoxLayout()

        self.btn_start = QPushButton("Start")
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.start_trace)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.btn_stop.clicked.connect(self.stop_trace)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

        # 1. Pause Button (NEW)
        self.btn_pause = QPushButton("Pause Trace")
        self.btn_pause.setCheckable(True)
        self.btn_pause.setStyleSheet("font-weight: bold;")
        self.btn_pause.toggled.connect(self.on_pause_toggled)
        layout.addWidget(self.btn_pause)

        layout.addWidget(self.create_h_line())  # Separator

        # 2. Data Mode
        layout.addWidget(QLabel("Data Mode:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["CAN (8 Bytes)", "CAN FD (64 Bytes)"])
        self.combo_type.currentIndexChanged.connect(self.setup_columns)
        layout.addWidget(self.combo_type)

        # 3. ID Filters
        layout.addWidget(QLabel("ID Filters (Hex):"))
        self.filters = []
        for i in range(5):
            le = QLineEdit()
            le.setPlaceholderText(f"Filter ID {i + 1}")
            self.filters.append(le)
            layout.addWidget(le)

        # 4. Options
        self.chk_highlight = QCheckBox("Highlight Changes")
        self.chk_highlight.setChecked(True)
        layout.addWidget(self.chk_highlight)

        self.chk_binary = QCheckBox("Show Binary Data")
        self.chk_binary.toggled.connect(self.refresh_view_mode)
        layout.addWidget(self.chk_binary)

        # 5. Simulation
        layout.addWidget(self.create_h_line())
        self.chk_sim = QCheckBox("TEST MODE (Simulate)")
        self.chk_sim.setStyleSheet("color: orange; font-weight: bold;")
        self.chk_sim.toggled.connect(self.toggle_simulation)
        layout.addWidget(self.chk_sim)

        layout.addStretch()

        # 6. Clear
        btn_clear = QPushButton("Clear Trace")
        btn_clear.clicked.connect(self.clear_trace)
        layout.addWidget(btn_clear)

    def create_h_line(self):
        """Helper to create a separator line"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def on_pause_toggled(self, checked):
        """Changes button appearance when Paused"""
        if checked:
            self.btn_pause.setText("Resume Trace ▶")
            self.btn_pause.setStyleSheet("background-color: #ffcccc; color: red; font-weight: bold;")
        else:
            self.btn_pause.setText("Pause Trace ⏸")
            self.btn_pause.setStyleSheet("font-weight: bold;")

    def toggle_simulation(self, checked):
        if self.worker_thread:
            self.worker_thread.set_test_mode(checked)

    def setup_columns(self):
        self.model.clear()

        headers = ["Sr.", "Time", "Count", "Ch", "ID", "Type", "Dir", "DLC"]
        is_fd = self.combo_type.currentIndex() == 1
        num_data_cols = 64 if is_fd else 8

        for i in range(num_data_cols):
            headers.append(f"D{i}")

        self.model.setHorizontalHeaderLabels(headers)
        self.logic.reset()

    # def update_table(self, data_packet):
    #     """Updates the table with new data"""
    #
    #     # --- 1. PAUSE CHECK (New) ---
    #     if self.btn_pause.isChecked():
    #         return  # Ignore updates if paused
    #
    #     # --- 2. Process Logic ---
    #     result = self.logic.process_packet(data_packet)
    #
    #     row_idx = result['row_index']
    #     int_data = result['int_data']
    #     show_binary = self.chk_binary.isChecked()
    #
    #     # --- 3. Add New Row ---
    #     if result['action'] == 'ADD':
    #         items = []
    #         # Metadata
    #         items.append(QStandardItem(str(row_idx + 1)))
    #         items.append(QStandardItem(str(data_packet.get('timestamp', '0.0'))))
    #         items.append(QStandardItem(str(result['count'])))
    #         items.append(QStandardItem(str(data_packet.get('channel', '0'))))
    #         items.append(QStandardItem(str(data_packet.get('can_id', '000'))))
    #         items.append(QStandardItem(str(data_packet.get('type', 'STD'))))
    #         items.append(QStandardItem(str(data_packet.get('direction', 'Rx'))))
    #         items.append(QStandardItem(str(data_packet.get('dlc', '0'))))
    #
    #         # Data
    #         for val in int_data:
    #             text = f"{val:02X}"
    #             if show_binary: text += f"\n{val:08b}"
    #             items.append(QStandardItem(text))
    #
    #         self.model.appendRow(items)
    #         self.table.scrollToBottom()
    #
    #     # --- 4. Update Existing Row ---
    #     elif result['action'] == 'UPDATE':
    #         # Update Time & Count
    #         self.model.setItem(row_idx, 1, QStandardItem(str(data_packet.get('timestamp', '0.0'))))
    #         self.model.setItem(row_idx, 2, QStandardItem(str(result['count'])))
    #
    #         highlight_brush = QBrush(QColor(255, 255, 0, 100))  # Yellow
    #
    #         do_highlight = self.chk_highlight.isChecked()
    #
    #         for i, val in enumerate(int_data):
    #             col_idx = 8 + i
    #             if col_idx >= self.model.columnCount(): break
    #
    #             text = f"{val:02X}"
    #             if show_binary: text += f"\n{val:08b}"
    #
    #             item = QStandardItem(text)
    #
    #             if do_highlight and (i in result['changed_indices']):
    #                 item.setBackground(highlight_brush)
    #
    #             self.model.setItem(row_idx, col_idx, item)

    def refresh_view_mode(self, checked):
        """
        When toggling Binary view, we must clear the table because
        the row indices will completely change (1 row vs 2 rows per ID).
        """
        self.clear_trace()

    def update_table(self, data_packet):
        """Updates the table with new data, handling the optional Binary Row."""

        # 1. Check Pause
        if self.btn_pause.isChecked():
            return

        # 2. Process Logic
        result = self.logic.process_packet(data_packet)

        # 3. Calculate Visual Row Index
        # If Binary is ON, each Logical Row takes 2 Visual Rows.
        show_binary = self.chk_binary.isChecked()
        row_multiplier = 2 if show_binary else 1
        visual_row_idx = result['row_index'] * row_multiplier

        int_data = result['int_data']

        # --- HANDLE NEW ROW (ADD) ---
        if result['action'] == 'ADD':
            # ---------------------------
            # ROW 1: HEX DATA + METADATA
            # ---------------------------
            row1_items = []
            # Metadata Columns (0-7)
            row1_items.append(QStandardItem(str(result['row_index'] + 1)))  # Sr.
            row1_items.append(QStandardItem(str(data_packet.get('timestamp', '0.0'))))  # Time
            row1_items.append(QStandardItem(str(result['count'])))  # Count
            row1_items.append(QStandardItem(str(data_packet.get('channel', '0'))))
            row1_items.append(QStandardItem(str(data_packet.get('can_id', '000'))))
            row1_items.append(QStandardItem(str(data_packet.get('type', 'STD'))))
            row1_items.append(QStandardItem(str(data_packet.get('direction', 'Rx'))))
            row1_items.append(QStandardItem(str(data_packet.get('dlc', '0'))))

            # Data Columns (Hex)
            for val in int_data:
                # Hex format
                row1_items.append(QStandardItem(f"{val:02X}"))

            self.model.appendRow(row1_items)

            # ---------------------------
            # ROW 2: BINARY DATA (Optional)
            # ---------------------------
            if show_binary:
                row2_items = []
                # Metadata placeholders (Empty, because we will span Row 1 over them)
                for _ in range(8):
                    row2_items.append(QStandardItem(""))

                # Data Columns (Binary)
                for val in int_data:
                    # Binary format (e.g., 00001111)
                    row2_items.append(QStandardItem(f"{val:08b}"))

                self.model.appendRow(row2_items)

                # --- SPANNING LOGIC ---
                # Make Metadata columns (0-7) cover both rows (Visual Row N and N+1)
                for col in range(8):
                    self.table.setSpan(visual_row_idx, col, 2, 1)

            self.table.scrollToBottom()

        # --- HANDLE UPDATE ROW (UPDATE) ---
        elif result['action'] == 'UPDATE':
            # Update Metadata (Time & Count)
            # We only need to update the top row (visual_row_idx) because of the span
            self.model.setItem(visual_row_idx, 1, QStandardItem(str(data_packet.get('timestamp', '0.0'))))
            self.model.setItem(visual_row_idx, 2, QStandardItem(str(result['count'])))

            # Add this to ensure the Channel column stays correct for that row
            self.model.setItem(visual_row_idx, 3, QStandardItem(str(data_packet.get('channel', '0'))))

            # Prepare Highlight Brush
            highlight_brush = QBrush(QColor(255, 255, 0, 100))  # Yellow
            normal_brush = QBrush(Qt.NoBrush)
            do_highlight = self.chk_highlight.isChecked()

            # Update Data Columns
            # We must update both Hex (Row 1) and Binary (Row 2) if visible
            for i, val in enumerate(int_data):
                col_idx = 8 + i
                if col_idx >= self.model.columnCount(): break

                # 1. Update HEX (Row 1)
                hex_item = QStandardItem(f"{val:02X}")
                if do_highlight and (i in result['changed_indices']):
                    hex_item.setBackground(highlight_brush)
                self.model.setItem(visual_row_idx, col_idx, hex_item)

                # 2. Update BINARY (Row 2)
                if show_binary:
                    bin_item = QStandardItem(f"{val:08b}")
                    # Also highlight the binary cell if changed
                    if do_highlight and (i in result['changed_indices']):
                        bin_item.setBackground(highlight_brush)
                    # Note: +1 for the next row
                    self.model.setItem(visual_row_idx + 1, col_idx, bin_item)

    def refresh_view_mode(self):
        pass

    def clear_trace(self):
        self.model.removeRows(0, self.model.rowCount())
        self.logic.reset()

    def start_trace(self):
        """Sends 0x51 to hardware to start the trace."""
        if self.worker_thread and self.worker_thread.serial_mgr:
            self.worker_thread.serial_mgr.start_sniffing()
            print("Tracing started")

            if not self.worker_thread.isRunning():
                self.worker_thread.start()

    def stop_trace(self):
        """Sends 0x52 to hardware to stop streaming"""
        if self.worker_thread and self.worker_thread.serial_mgr:
            # Send 0x52
            self.worker_thread.serial_mgr.stop_sniffing()
            print("Trace stopped")