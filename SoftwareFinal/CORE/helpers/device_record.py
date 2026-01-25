from PySide6.QtCore import QObject, Signal

class DeviceGlobalstate(QObject):

    # Signal to notify other parts of the app
    connection_changed = Signal(bool)
    data_updated = Signal()

    def __init__(self):
        super().__init__()

        self.is_connected = False
        self.serial_no = ""
        self.fw_version = ""
        self.num_channel = 0
        self.channels = []

    def update_state(self, info):
        """ Called from serial.py to update the state of the device """
        self.is_connected = True
        self.serial_no = info.get('serial_no', "")
        self.fw_version = info.get('fw', "")
        self.num_channel = info.get('num_channel', 0)
        self.channels = info.get('channels', [])

        self.connection_changed.emit(True)
        self.data_updated.emit()

    def set_disconnected(self):
        """ Called from serial.py to set the state of the device """
        self.is_connected = False
        self.connection_changed.emit(False)


state = DeviceGlobalstate()
