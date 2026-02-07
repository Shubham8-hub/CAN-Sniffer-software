from PySide6.QtWidgets import QTableView, QHeaderView
from PySide6.QtGui import QStandardItemModel
from .detachable_widget import DetachableWidget

class TransmitWindow(DetachableWidget):
    def __init__(self, parent_callback=None):
        super().__init__(title="CAN Transmit")
        self.parent_callback = parent_callback

        self.table = QTableView()
        self.set_child(self.table)

        # Simple Transmit UI Columns
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["ID (Hex)", "DLC", "Data (Hex)", "Cycle (ms)", "Count", "Status", "Action"])
        self.table.setModel(self.model)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)