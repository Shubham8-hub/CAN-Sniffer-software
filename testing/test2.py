import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QGroupBox, QLabel,
    QComboBox, QPushButton, QGridLayout, QVBoxLayout
)
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtCore import Qt


class SerialConnectionWidget(QGroupBox):
    def __init__(self):
        super().__init__("Serial COM Port")

        self.serial = QSerialPort(self)

        self.setAlignment(Qt.AlignCenter)

        self.label_com = QLabel("COM")
        self.combo_com = QComboBox()
        self.btn_refresh = QPushButton("Refresh")

        self._setup_ui()
        self._populate_ports()

    def _setup_ui(self):
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(self.label_com, 0, 0)
        layout.addWidget(self.combo_com, 0, 1)
        layout.addWidget(self.btn_refresh, 0, 2)

        self.setLayout(layout)

        # -------- Styling (same look & feel) --------
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdbdbd;
                border-radius: 6px;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
            }
            QLabel {
                font-weight: bold;
            }
            QComboBox {
                padding: 4px;
                min-width: 180px;
            }
            QPushButton {
                padding: 4px 10px;
            }
        """)

        self.btn_refresh.clicked.connect(self._populate_ports)

    def _populate_ports(self):
        self.combo_com.clear()

        for port in QSerialPortInfo.availablePorts():
            text = f"{port.portName()} - {port.description()}"
            self.combo_com.addItem(text, port.portName())

    def selected_port(self):
        return self.combo_com.currentData()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Connection")
        self.resize(420, 160)

        serial_widget = SerialConnectionWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(serial_widget)
        layout.addStretch()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())