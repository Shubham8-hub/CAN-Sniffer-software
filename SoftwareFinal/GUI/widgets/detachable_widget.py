# from PyQt5.QtWidgets import
from PySide6.QtWidgets import (QWidget, QTableView, QVBoxLayout, QHBoxLayout,
                               QPushButton, QMenu,QDialog, QLabel)
from PySide6.QtCore import Qt

class DetachableWidget(QWidget):

    def __init__(self, title=""):
        super().__init__()
        self.floating_window = None
        self.title = title

        title_label = QLabel(self.title)
        title_label.setStyleSheet("color:white; font-size:20px; font-weight:bold;")


        # Main Layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Title bar
        top_bar = QHBoxLayout()
        top_bar.setAlignment(Qt.AlignRight)
        top_bar.addWidget(title_label)

        top_bar.addStretch()

        self.menu_button = QPushButton("⋮")
        self.menu_button.setFixedWidth(40)
        self.menu_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.menu_button.clicked.connect(self.show_menu)

        top_bar.addWidget(self.menu_button)
        self.main_layout.addLayout(top_bar)

        #Placeholder for child widget
        self.child_container = QVBoxLayout()
        self.main_layout.addLayout(self.child_container)

    def set_child(self, widget):
        self.child_container.addWidget(widget)

    def show_menu(self):
        menu = QMenu()
        if not self.is_detached():
            menu.addAction("Detach Window", self.detach_window)
        else:
            menu.addAction("Attach Back", self.attach_window)
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomRight()))

    def is_detached(self):
        return self.floating_window is not None

    def detach_window(self):
        """Move widget into a floating window"""
        self.setParent(None)
        self.floating_window = QDialog()
        self.floating_window.setWindowTitle("Floating Window")
        layout = QVBoxLayout()
        self.floating_window.setLayout(layout)
        layout.addWidget(self)

        self.floating_window.resize(600, 400)
        self.floating_window.show()

        self.floating_window.finished.connect(self.attach_window)

    def attach_window(self):
        """Re-attach back to parent"""
        if self.floating_window:
            self.floating_window = None

        # Parent window will re-add it
        self.on_attach_request()

    def on_attach_request(self):
        """Must be implemented by parent window"""
        pass