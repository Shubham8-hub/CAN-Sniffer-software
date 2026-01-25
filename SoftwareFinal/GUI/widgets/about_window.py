from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QVBoxLayout, QLabel, QTableView)


class AboutWindow(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("About"))
        # layout.addWidget(TraceWindow())
        self.setLayout(layout)