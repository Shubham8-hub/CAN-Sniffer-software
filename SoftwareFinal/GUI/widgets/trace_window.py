# from PySide6.QtWidgets import (QApplication, QMainWindow,QWidget,
#                                QVBoxLayout, QLabel, QTableView)
#
# class TraceWindow(QWidget):
#
#     def __init__(self):
#         super().__init__()
#         layout = QVBoxLayout()
#         layout.addWidget(QLabel("Trace"))
#
#         # layout.addWidget(TraceWindow())
#         table = QTableView()
#         layout.addWidget(table)
#
#         self.setLayout(layout)

from PySide6.QtWidgets import QTableView, QHeaderView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QTimer
from .detachable_widget import DetachableWidget

import random
import time

class TraceWindow(DetachableWidget):
    def __init__(self, parent_callback=None):
        super().__init__(title="CAN Trace")
        self.parent_callback = parent_callback

        # CAN Table
        self.table = QTableView()

        # Dark theme styling
        self.table.setStyleSheet("""
            QTableView {
                background-color: #1e1e1e;
                color: white;
                gridline-color: #444;
                selection-background-color: #444;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 4px;
            }
        """)

        # Table model
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            ["Time", "ID", "DLC", "Data", "Channel", "Dir"]
        )
        self.table.setModel(self.model)

        # Auto resize
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        self.set_child(self.table)

        # Dummy CAN generator
        self.timer = QTimer()
        self.timer.timeout.connect(self.add_dummy_message)
        self.timer.start(500)  # every 500ms

    def add_dummy_message(self):
        timestamp = f"{time.time():.3f}"
        can_id = hex(random.randint(0x100, 0x7FF))
        dlc = random.randint(0, 8)
        data = " ".join([f"{random.randint(0,255):02X}" for _ in range(dlc)])
        ch = "CH1"
        direction = "Rx"

        row = [
            QStandardItem(timestamp),
            QStandardItem(can_id),
            QStandardItem(str(dlc)),
            QStandardItem(data),
            QStandardItem(ch),
            QStandardItem(direction),
        ]

        self.model.appendRow(row)

    def on_attach_request(self):
        if self.parent_callback:
            self.parent_callback(self)
