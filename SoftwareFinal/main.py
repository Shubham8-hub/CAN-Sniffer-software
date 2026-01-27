# from PySide6.QtWidgets.QWidget import window
from PySide6.QtWidgets import QApplication
from GUI.windows.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()


