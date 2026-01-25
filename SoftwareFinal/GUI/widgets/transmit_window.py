from PySide6.QtWidgets import QTableView, QHeaderView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt
from .detachable_widget import DetachableWidget

class TransmitWindow(DetachableWidget):
    def __init__(self, parent_callback=None):
        super().__init__(title="CAN Transmit")
        self.parent_callback = parent_callback

        self.table = QTableView()
        self.set_child(self.table)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["ID", "DLC", "Data", "Mode"])
        self.table.setModel(self.model)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

    def on_attach_request(self):
        if self.parent_callback:
            self.parent_callback(self)
