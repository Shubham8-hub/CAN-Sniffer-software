import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QGroupBox, QLabel,
    QComboBox, QGridLayout, QVBoxLayout
)
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtCore import Qt


class SerialPortWidget(QGroupBox):
    def __init__(self):
        super().__init__("Serial COM Port")

        self.serial = QSerialPort(self)

        # UI elements
        self.label_com = QLabel("COM:")
        self.combo_com = QComboBox()

        # Layout
        layout = QGridLayout()
        layout.addWidget(self.label_com, 0, 0)
        layout.addWidget(self.combo_com, 0, 1)
        self.setLayout(layout)

        self.populate_ports()

    def populate_ports(self):
        """Fill dropdown with available COM ports"""
        self.combo_com.clear()

        ports = QSerialPortInfo.availablePorts()
        for port in ports:
            # Display text shown to user
            display_text = f"{port.portName()} - {port.description()}"
            # Store port name as data
            self.combo_com.addItem(display_text, port.portName())

    def get_selected_port(self):
        """Return selected COM port name"""
        return self.combo_com.currentData()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Serial Port Example")
        self.resize(400, 150)

        self.serial_group = SerialPortWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.serial_group)
        layout.addStretch()

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
