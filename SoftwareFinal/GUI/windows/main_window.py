#
# from PySide6.QtGui import QAction, QIcon
# from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
#                                QHBoxLayout, QToolBar, QStackedWidget)
# from PySide6.QtCore import Qt, QSize
#
# import os
# from GUI.widgets.about_window import AboutWindow
# from GUI.widgets.serial_window import SerialWindow
# from GUI.widgets.setting_window import SettingWindow
# from GUI.widgets.transmit_window import TransmitWindow
# from GUI.widgets.trace_window import TraceWindow
#
#
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#
#         # 1. Setup paths
#         base_path = os.path.dirname(os.path.abspath(__file__))
#         res_path = os.path.join(base_path, "../resources/icons/")
#
#         self.setWindowTitle("BitSniff CAN - BitSniff Coding")
#         self.resize(1000, 600)
#
#         # 2. Setup the Stacked Widget (The container for all tabs)
#         self.stack = QStackedWidget()
#         self.setCentralWidget(self.stack)
#
#         # 3. Pre-create ALL windows so they never get deleted
#         self.serial_page = SerialWindow()
#         self.setting_page = SettingWindow(self.serial_page.serial_mgr)  # Pass serial manager to settings
#         self.about_page = AboutWindow()
#         self.msg_center_page = self._create_message_center_layout()
#
#         # Add to stack: Order determines Index
#         self.stack.addWidget(self.msg_center_page)  # Index 0
#         self.stack.addWidget(self.setting_page)  # Index 1
#         self.stack.addWidget(self.serial_page)  # Index 2
#         self.stack.addWidget(self.about_page)  # Index 3
#
#         # 4. Setup Toolbar
#         self._init_toolbar(res_path)
#         self.statusBar().showMessage("Made in INDIA")
#
#     def _init_toolbar(self, path):
#         toolbar = QToolBar("Toolbar")
#         toolbar.setIconSize(QSize(40, 40))
#         toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
#         self.addToolBar(toolbar)
#
#         # Create actions that just change the Stack Index
#         actions = [
#             ("Message center", "message_center.png", 0),
#             ("Setting", "setting.png", 1),
#             ("Serial", "serial.png", 2),
#             ("About", "about.png", 3)
#         ]
#
#         for text, icon_name, index in actions:
#             act = QAction(QIcon(os.path.join(path, icon_name)), text, self)
#             act.triggered.connect(lambda checked, i=index: self.stack.setCurrentIndex(i))
#             toolbar.addAction(act)
#             toolbar.addSeparator()
#
#     def _create_message_center_layout(self):
#         container = QWidget()
#         layout = QHBoxLayout(container)
#         self.trace_window = TraceWindow(parent_callback=lambda w: self.stack.setCurrentIndex(0))
#         self.transmit_window = TransmitWindow(parent_callback=lambda w: self.stack.setCurrentIndex(0))
#         layout.addWidget(self.trace_window)
#         layout.addWidget(self.transmit_window)
#         return container

#
#
# from PySide6.QtGui import QAction, QIcon
# from PySide6.QtWidgets import (QMainWindow, QWidget, QToolBar, QStackedWidget,
#                                QTabWidget, QToolButton, QMenu)
# from PySide6.QtCore import Qt, QSize, QThread
#
# import os
# # Adjust imports based on your folder structure
# from GUI.widgets.about_window import AboutWindow
# from GUI.widgets.serial_window import SerialWindow
# from GUI.widgets.setting_window import SettingWindow
# from GUI.widgets.transmit_window import TransmitWindow
# from GUI.widgets.trace_window import TraceWindow
# from CORE.serial.serial import SerialManager
# from CORE.helpers.can_worker import CanReceiverThread
# from GUI.windows.central_widget_window import CentralWidgetWindow
#
#
# class MainWindow(QMainWindow):
#     def __init__(self):
#         # super().__init__()
#         #
#         # # 1. Setup paths
#         # base_path = os.path.dirname(os.path.abspath(__file__))
#         # self.res_path = os.path.join(base_path, "../resources/icons/")
#         #
#         # self.setWindowTitle("BitSniff CAN - BitSniff Coding")
#         # self.resize(1000, 600)
#         #
#         # # --- THREADING SETUP ---
#         # # 1. Create the Thread
#         # self.worker_thread = QThread()
#         #
#         # # 2. Create the Serial Manager (The Worker)
#         # self.serial_mgr = SerialManager()
#         #
#         # # 3. Move the Worker to the Thread
#         # self.serial_mgr.moveToThread(self.worker_thread)
#         #
#         # # 4. Start the thread
#         # self.worker_thread.start()
#         # # -----------------------
#         #
#         # # 2. Setup the Stacked Widget
#         # self.stack = QStackedWidget()
#         # self.setCentralWidget(self.stack)
#         #
#         # # 3. Create Pages
#         # # -- Page 0: Message Center (Tab Widget container) --
#         # self.msg_center_tabs = QTabWidget()
#         # self.msg_center_tabs.setTabsClosable(True)
#         # self.msg_center_tabs.tabCloseRequested.connect(self._close_tab)
#         #
#         # # Widget References (Initialize as None)
#         # self.transmit_window = None
#         # self.trace_window = None
#         #
#         # # -- Page 1, 2, 3: Other Windows --
#         # # Pass the threaded serial_mgr to windows that need it
#         # self.serial_page = SerialWindow(self.serial_mgr)
#         # self.setting_page = SettingWindow(self.serial_mgr)
#         # self.about_page = AboutWindow()
#         #
#         # # Add to stack
#         # self.stack.addWidget(self.msg_center_tabs)  # Index 0
#         # self.stack.addWidget(self.setting_page)  # Index 1
#         # self.stack.addWidget(self.serial_page)  # Index 2
#         # self.stack.addWidget(self.about_page)  # Index 3
#         #
#         # # 4. Setup Toolbar
#         # self._init_toolbar(self.res_path)
#         # self.statusBar().showMessage("Ready - Serial running on background thread")
#         super().__init__()
#
#         # 1. Initialize the Core Logic FIRST
#         self.serial_mgr = SerialManager()
#
#         # 2. Setup Threading
#         self.rx_thread = CanReceiverThread(self.serial_mgr)
#         self.rx_thread.start()  # Start listening immediately
#
#         # 3. Setup UI
#         self.setWindowTitle("BitSniff CAN")
#         self.resize(1200, 800)
#
#         # 4. Setup Central Area with Tabs
#         # We use a QTabWidget inside the central area to hold "Transmit" and "Receive"
#         self.central_tabs = QTabWidget()
#         self.central_tabs.setTabsClosable(True)
#         self.central_tabs.tabCloseRequested.connect(self.close_tab)
#         self.setCentralWidget(self.central_tabs)
#
#         # 5. Create Windows
#         # Pass the shared manager to SerialWindow
#         self.serial_page = SerialWindow(self.serial_mgr)
#
#         # Create Transmit/Trace windows but don't show them yet
#         self.transmit_window = TransmitWindow()  # You might need to pass serial_mgr here too later
#         self.trace_window = TraceWindow()
#
#         # Connect Thread data to Trace Window
#         self.rx_thread.data_received.connect(self.trace_window.update_table)  # Ensure TraceWindow has this method
#
#         # 6. Setup Menu Actions (Example)
#         self.create_menus()
#
#         # Open Serial Window by default (as a tab or separate dock, purely your choice)
#         self.central_tabs.addTab(self.serial_page, "Connection")
#
#     def _init_toolbar(self, path):
#         toolbar = QToolBar("Toolbar")
#         toolbar.setIconSize(QSize(40, 40))
#         toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
#         self.addToolBar(toolbar)
#
#         # --- 1. Message Center (Menu Button) ---
#         msg_btn = QToolButton()
#         msg_btn.setText("Message Center")
#         # Ensure you have this icon or remove the QIcon part if missing
#         if os.path.exists(os.path.join(path, "message_center.png")):
#             msg_btn.setIcon(QIcon(os.path.join(path, "message_center.png")))
#
#         msg_btn.setPopupMode(QToolButton.InstantPopup)
#         msg_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
#
#         # Create Menu
#         msg_menu = QMenu(msg_btn)
#
#         act_tx = QAction("CAN Transmit", self)
#         act_tx.triggered.connect(self.open_transmit_tab)
#         msg_menu.addAction(act_tx)
#
#         act_rx = QAction("CAN Receive", self)
#         act_rx.triggered.connect(self.open_receive_tab)
#         msg_menu.addAction(act_rx)
#
#         msg_btn.setMenu(msg_menu)
#         toolbar.addWidget(msg_btn)
#
#         toolbar.addSeparator()
#
#         # --- 2. Other Standard Actions ---
#         act_setting = QAction(QIcon(os.path.join(path, "setting.png")), "Setting", self)
#         act_setting.triggered.connect(lambda: self.stack.setCurrentIndex(1))
#         toolbar.addAction(act_setting)
#
#         toolbar.addSeparator()
#
#         act_serial = QAction(QIcon(os.path.join(path, "serial.png")), "Serial", self)
#         act_serial.triggered.connect(lambda: self.stack.setCurrentIndex(2))
#         toolbar.addAction(act_serial)
#
#         toolbar.addSeparator()
#
#         act_about = QAction(QIcon(os.path.join(path, "about.png")), "About", self)
#         act_about.triggered.connect(lambda: self.stack.setCurrentIndex(3))
#         toolbar.addAction(act_about)
#
#     def _is_widget_alive(self, widget):
#         """Helper to check if a C++ widget is still valid."""
#         if widget is None:
#             return False
#         try:
#             # Try accessing a property to see if it crashes (or use shiboken if available)
#             # In PySide6, valid wrappers to deleted objects often raise RuntimeError on access
#             _ = widget.objectName()
#             return True
#         except RuntimeError:
#             return False
#
#     def open_transmit_tab(self):
#         # self.stack.setCurrentIndex(0)  # Switch to Msg Center
#         #
#         # # Check if widget exists AND is alive
#         # if not self._is_widget_alive(self.transmit_window):
#         #     # Pass serial manager so Transmit Window can send data
#         #     self.transmit_window = TransmitWindow(self.serial_mgr)
#         #     self.msg_center_tabs.addTab(self.transmit_window, "CAN Transmit")
#         #
#         # # Focus the tab
#         # self.msg_center_tabs.setCurrentWidget(self.transmit_window)
#         if self.central_tabs.indexOf(self.transmit_window) == -1:
#             self.central_tabs.addTab(self.transmit_window, "CAN Transmit")
#         self.central_tabs.setCurrentWidget(self.transmit_window)
#
#     def open_receive_tab(self):
#         # self.stack.setCurrentIndex(0)  # Switch to Msg Center
#         #
#         # if not self._is_widget_alive(self.trace_window):
#         #     # Pass serial manager so Trace Window can receive signals
#         #     self.trace_window = TraceWindow(self.serial_mgr)
#         #     self.msg_center_tabs.addTab(self.trace_window, "CAN Receive")
#         #
#         # self.msg_center_tabs.setCurrentWidget(self.trace_window)
#         if self.central_tabs.indexOf(self.trace_window) == -1:
#             self.central_tabs.addTab(self.trace_window, "CAN Trace")
#         self.central_tabs.setCurrentWidget(self.trace_window)
#
#     # def _close_tab(self, index):
#     #     widget = self.msg_center_tabs.widget(index)
#     #
#     #     # 1. Remove from tab widget first
#     #     self.msg_center_tabs.removeTab(index)
#     #
#     #     # 2. Reset Python References explicitly
#     #     if widget is self.transmit_window:
#     #         self.transmit_window = None
#     #     elif widget is self.trace_window:
#     #         self.trace_window = None
#     #
#     #     # 3. Schedule for deletion
#     #     widget.deleteLater()
#     #
#     # def closeEvent(self, event):
#     #     # Clean up thread on app exit
#     #     self.worker_thread.quit()
#     #     self.worker_thread.wait()
#     #     super().closeEvent(event)
#     def close_tab(self, index):
#         self.central_tabs.removeTab(index)
#
#     def closeEvent(self, event):
#         """
#         Called when the window is closed.
#         Stops the thread safely before the app exits.
#         """
#         if hasattr(self, 'rx_thread') and self.rx_thread.isRunning():
#             print("Stopping Worker Thread...")
#             self.rx_thread.stop()  # Call the stop method we made earlier
#             self.rx_thread.wait()  # Wait for it to actually finish
#
#         super().closeEvent(event)
#
#     def create_menus(self):
#         """Creates the Messenger menu and actions."""
#         # 1. Get the menu bar
#         menu = self.menuBar().addMenu("Messenger")
#
#         # 2. Add 'CAN Transmit' action
#         action_tx = menu.addAction("CAN Transmit")
#         action_tx.triggered.connect(self.open_transmit_tab)
#
#         # 3. Add 'CAN Receive' action
#         action_rx = menu.addAction("CAN Receive")
#         action_rx.triggered.connect(self.open_receive_tab)

from PySide6.QtWidgets import (QMainWindow, QToolBar, QStackedWidget,
                               QWidget, QTabWidget, QVBoxLayout)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, QSize
import os

# --- Import Logic ---
from CORE.serial.serial import SerialManager
from CORE.helpers.can_worker import CanReceiverThread

# --- Import Windows ---
from GUI.widgets.serial_window import SerialWindow
from GUI.widgets.setting_window import SettingWindow
from GUI.widgets.transmit_window import TransmitWindow
from GUI.widgets.trace_window import TraceWindow
from GUI.widgets.about_window import AboutWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BitSniff CAN - Sniffer Software")
        self.resize(1100, 700)

        # ---------------------------------------------------------
        # 0. SETUP PATHS
        # ---------------------------------------------------------
        # This finds the directory of THIS file (main_window.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up two levels (GUI -> SoftwareFinal) then into resources/icons
        self.icon_dir = os.path.join(current_dir, "..","resources", "icons")

        # ---------------------------------------------------------
        # 1. INITIALIZE LOGIC (The Brains)
        # ---------------------------------------------------------
        self.serial_mgr = SerialManager()

        # Start the background listener thread
        self.rx_thread = CanReceiverThread(self.serial_mgr)
        self.rx_thread.start()

        # ---------------------------------------------------------
        # 2. SETUP UI CONTAINERS (Sidebar + Stack)
        # ---------------------------------------------------------
        # A. Central Stack (Holds the different pages)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # B. Sidebar (Toolbar)
        self.toolbar = QToolBar("Main Navigation")
        self.toolbar.setIconSize(QSize(40, 40))
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

        # ---------------------------------------------------------
        # 3. CREATE PAGES
        # ---------------------------------------------------------

        # -- Page 1: Serial Connection --
        # Pass the shared manager so it controls the real connection
        self.page_serial = SerialWindow(self.serial_mgr)

        # -- Page 2: Settings --
        self.page_settings = SettingWindow(self.serial_mgr)

        # -- Page 3: Messenger (Transmit & Receive Tabs) --
        # This is a widget that holds tabs for Tx/Rx
        self.page_messenger = QTabWidget()

        self.transmit_window = TransmitWindow()  # Add serial_mgr here if needed later
        self.trace_window = TraceWindow(worker_thread=self.rx_thread)

        # Add tabs to the Messenger page
        self.page_messenger.addTab(self.transmit_window, "CAN Transmit")
        self.page_messenger.addTab(self.trace_window, "CAN Trace")

        # -- Page 4: About --
        self.page_about = AboutWindow()

        # ---------------------------------------------------------
        # 4. ADD PAGES TO STACK
        # ---------------------------------------------------------
        # Note: The order here determines the Index (0, 1, 2, 3)
        self.stack.addWidget(self.page_serial)  # Index 0
        self.stack.addWidget(self.page_settings)  # Index 1
        self.stack.addWidget(self.page_messenger)  # Index 2
        self.stack.addWidget(self.page_about)  # Index 3

        # ---------------------------------------------------------
        # 5. CONNECT THREAD TO GUI
        # ---------------------------------------------------------
        # When thread gets data -> send it to Trace Window
        self.rx_thread.data_received.connect(self.trace_window.update_table)

        # ---------------------------------------------------------
        # 6. BUILD SIDEBAR NAVIGATION WITH ICON
        # ---------------------------------------------------------
        self._create_nav_action("Connect", 0, "serial.png")
        self._create_nav_action("Settings", 1, "setting.png")
        self._create_nav_action("Messenger", 2, "message_center.png")
        self._create_nav_action("About", 3, "about.png")

        # Default to Serial Page
        self.stack.setCurrentIndex(0)

    def _create_nav_action(self, name, index, icon_filename):
        """Helper to create sidebar buttons with icons"""
        action = QAction(name, self)

        # construct full path
        icon_path = os.path.join(self.icon_dir, icon_filename)

        # Load icon if it exists
        if os.path.exists(icon_path):
            action.setIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon not found at {icon_path}")

        action.triggered.connect(lambda: self.stack.setCurrentIndex(index))
        self.toolbar.addAction(action)

    def closeEvent(self, event):
        """Stop the background thread safely when closing"""
        if self.rx_thread.isRunning():
            self.rx_thread.stop()
            self.rx_thread.wait()
        super().closeEvent(event)