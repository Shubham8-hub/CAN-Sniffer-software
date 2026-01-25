import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QComboBox, QCheckBox,
    QRadioButton, QLineEdit, QSpinBox, QSlider,
    QProgressBar, QTableWidget, QTableWidgetItem,
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QMenu
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication


class ResponsiveDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Responsive UI Test")

        # ---------- Adaptive window size ----------
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))

        self._create_menu()
        self._create_status_bar()
        self._create_central_ui()

    # ---------- MENU ----------
    def _create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        view_menu = menubar.addMenu("View")
        help_menu = menubar.addMenu("Help")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(exit_action)
        view_menu.addAction(QAction("Reset Layout", self))
        help_menu.addAction(QAction("About", self))

    # ---------- STATUS BAR ----------
    def _create_status_bar(self):
        self.statusBar().showMessage("Ready")

    # ---------- CENTRAL UI ----------
    def _create_central_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout(central)

        # LEFT PANEL
        left_panel = self._create_left_panel()
        left_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # RIGHT PANEL
        right_panel = self._create_right_panel()
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)

        self.setCentralWidget(central)

    # ---------- LEFT PANEL ----------
    def _create_left_panel(self):
        box = QGroupBox("Settings Panel")
        layout = QVBoxLayout(box)

        # Dropdown
        layout.addWidget(QLabel("Select COM Port"))
        combo = QComboBox()
        combo.addItems(["COM1", "COM2", "COM3", "COM4"])
        layout.addWidget(combo)

        # Checkboxes
        layout.addWidget(QCheckBox("Enable Logging"))
        layout.addWidget(QCheckBox("Auto Connect"))

        # Radio buttons
        layout.addWidget(QLabel("Mode"))
        layout.addWidget(QRadioButton("Normal"))
        layout.addWidget(QRadioButton("Advanced"))

        # Line edit
        layout.addWidget(QLabel("Device Name"))
        layout.addWidget(QLineEdit("STM32 Sniffer"))

        # SpinBox
        layout.addWidget(QLabel("Baud Rate Index"))
        layout.addWidget(QSpinBox())

        layout.addStretch()
        return box

    # ---------- RIGHT PANEL ----------
    def _create_right_panel(self):
        box = QGroupBox("Main Content")
        layout = QVBoxLayout(box)

        # Top controls
        top_controls = QGridLayout()
        top_controls.addWidget(QLabel("Speed"), 0, 0)

        slider = QSlider(Qt.Horizontal)
        progress = QProgressBar()

        slider.valueChanged.connect(progress.setValue)

        top_controls.addWidget(slider, 0, 1)
        top_controls.addWidget(progress, 1, 1)

        layout.addLayout(top_controls)

        # Table
        table = QTableWidget(10, 4)
        table.setHorizontalHeaderLabels(["ID", "DLC", "Data", "Timestamp"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for row in range(10):
            table.setItem(row, 0, QTableWidgetItem(f"0x{100+row:X}"))
            table.setItem(row, 1, QTableWidgetItem("8"))
            table.setItem(row, 2, QTableWidgetItem("AA BB CC DD EE FF 11 22"))
            table.setItem(row, 3, QTableWidgetItem("12:00:00"))

        layout.addWidget(table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(QPushButton("Start"))
        btn_layout.addWidget(QPushButton("Stop"))
        btn_layout.addWidget(QPushButton("Clear"))

        layout.addLayout(btn_layout)

        return box


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ResponsiveDemo()
    window.show()
    sys.exit(app.exec())
