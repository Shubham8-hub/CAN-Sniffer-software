# # from PyQt5.QtWidgets import QToolBar
# from PySide6.QtGui import QAction, QIcon
# from PySide6.QtWidgets import QApplication, QMainWindow,QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout, QLabel, QToolBar, QToolButton
# from PySide6.QtCore import Qt, QSize
#
# import os
# import sys
#
# from GUI.windows.central_widget_window import CentralWidgetWindow
# from GUI.widgets.about_window import AboutWindow
# from GUI.widgets.serial_window import SerialWindow
# from GUI.widgets.setting_window import SettingWindow
# from GUI.widgets.transmit_window import TransmitWindow
# from GUI.widgets.trace_window import TraceWindow
#
# class MainWindow(QMainWindow):
#
#     def __init__(self):
#         super().__init__()
#
#         #Build absolute path to the icon
#         base_path = os.path.dirname(os.path.abspath(__file__))
#         message_center_icon = os.path.join(base_path, "../resources/icons/message_center.png")
#         setting_icon = os.path.join(base_path, "../resources/icons/setting.png")
#         serial_icon = os.path.join(base_path, "../resources/icons/serial.png")
#         about_icon = os.path.join(base_path, "../resources/icons/about.png")
#
#         self.setWindowTitle("BitSniff CAN - BitSniff Coding ")
#         # self.setFixedSize(400,400)          # To set the application to fixed size
#         self.resize(1000,600)                # To set the application to resize and maximize the windows to the max screen
#
#         self.central = CentralWidgetWindow()
#         self.setCentralWidget(self.central)
#
#
#         toolbar = QToolBar("Toolbar")
#         toolbar.setIconSize(QSize(40,40))
#         toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
#         self.addToolBar(toolbar)
#
#         message_center_action = QAction(QIcon(message_center_icon),"Message center", self)
#         # message_center_action.setStatusTip("Message Center")
#         message_center_action.triggered.connect(self.load_message_center)
#         toolbar.addAction(message_center_action)
#
#         toolbar.addSeparator()
#
#         setting_action = QAction(QIcon(setting_icon),"Setting", self)
#         # message_center_action.setStatusTip("Message Center")
#         setting_action.triggered.connect(self.load_setting)
#         toolbar.addAction(setting_action)
#
#         toolbar.addSeparator()
#
#         serial_action = QAction(QIcon(serial_icon),"&Serial", self)
#         # message_center_action.setStatusTip("Message Center")
#         serial_action.triggered.connect(self.load_serial)
#         toolbar.addAction(serial_action)
#
#         toolbar.addSeparator()
#
#         about_action = QAction(QIcon(about_icon),"&About", self)
#         # message_center_action.setStatusTip("Message Center")
#         about_action.triggered.connect(self.load_about)
#         toolbar.addAction(about_action)
#
#         # Status bar
#         self.statusBar().showMessage("Made in INDIA")
#
#
#     #--------------------------------------------------
#     # Window Loading Logic
#     # ------------------------------------------------
#
#     def load_message_center(self):
#         container = QWidget()
#         from PySide6.QtWidgets import QHBoxLayout
#         layout = QHBoxLayout()
#
#         # layout.addWidget(TraceWindow())
#         # layout.addWidget(TransmitWindow())
#         # Callbacks to re-attach
#         self.trace_window = TraceWindow(parent_callback=self.attach_trace)
#         self.transmit_window = TransmitWindow(parent_callback=self.attach_transmit)
#
#         layout.addWidget(self.trace_window)
#         layout.addWidget(self.transmit_window)
#
#         container.setLayout(layout)
#         self.central.set_widget(container)
#
#     def attach_trace(self, widget):
#         self.load_message_center()  # reload UI fresh
#
#     def attach_transmit(self, widget):
#         self.load_message_center()
#
#     def load_setting(self):
#         self.central.set_widget(SettingWindow())
#
#     def load_serial(self):
#         self.central.set_widget(SerialWindow())
#
#     def load_about(self):
#         self.central.set_widget(AboutWindow())

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QToolBar, QStackedWidget)
from PySide6.QtCore import Qt, QSize

import os
from GUI.widgets.about_window import AboutWindow
from GUI.widgets.serial_window import SerialWindow
from GUI.widgets.setting_window import SettingWindow
from GUI.widgets.transmit_window import TransmitWindow
from GUI.widgets.trace_window import TraceWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Setup paths
        base_path = os.path.dirname(os.path.abspath(__file__))
        res_path = os.path.join(base_path, "../resources/icons/")

        self.setWindowTitle("BitSniff CAN - BitSniff Coding")
        self.resize(1000, 600)

        # 2. Setup the Stacked Widget (The container for all tabs)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 3. Pre-create ALL windows so they never get deleted
        self.serial_page = SerialWindow()
        self.setting_page = SettingWindow(self.serial_page.serial_mgr)  # Pass serial manager to settings
        self.about_page = AboutWindow()
        self.msg_center_page = self._create_message_center_layout()

        # Add to stack: Order determines Index
        self.stack.addWidget(self.msg_center_page)  # Index 0
        self.stack.addWidget(self.setting_page)  # Index 1
        self.stack.addWidget(self.serial_page)  # Index 2
        self.stack.addWidget(self.about_page)  # Index 3

        # 4. Setup Toolbar
        self._init_toolbar(res_path)
        self.statusBar().showMessage("Made in INDIA")

    def _init_toolbar(self, path):
        toolbar = QToolBar("Toolbar")
        toolbar.setIconSize(QSize(40, 40))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # Create actions that just change the Stack Index
        actions = [
            ("Message center", "message_center.png", 0),
            ("Setting", "setting.png", 1),
            ("Serial", "serial.png", 2),
            ("About", "about.png", 3)
        ]

        for text, icon_name, index in actions:
            act = QAction(QIcon(os.path.join(path, icon_name)), text, self)
            act.triggered.connect(lambda checked, i=index: self.stack.setCurrentIndex(i))
            toolbar.addAction(act)
            toolbar.addSeparator()

    def _create_message_center_layout(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        self.trace_window = TraceWindow(parent_callback=lambda w: self.stack.setCurrentIndex(0))
        self.transmit_window = TransmitWindow(parent_callback=lambda w: self.stack.setCurrentIndex(0))
        layout.addWidget(self.trace_window)
        layout.addWidget(self.transmit_window)
        return container
