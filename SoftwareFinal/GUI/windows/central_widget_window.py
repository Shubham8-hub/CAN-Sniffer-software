from PySide6.QtWidgets import QWidget, QVBoxLayout

class CentralWidgetWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def set_widget(self, widget):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.layout.addWidget(widget)