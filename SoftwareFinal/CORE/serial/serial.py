from PySide6.QtCore import  QObject, Signal, QTimer
from PySide6.QtSerialPort import QSerialPort
from CORE.helpers.command import Command

import struct

from CORE.helpers.device_record import state

class SerialManager(QObject):

    connected = Signal(dict)
    disconnected = Signal()
    error = Signal(str)
    busy = Signal(bool)

    def __init__(self):
        super().__init__()
        self.serial = QSerialPort()
        self.serial.readyRead.connect(self._on_ready_read)
        self._rx_buffer = bytearray()
        # self._tx_buffer = bytearray()

        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._on_timeout)

    def connect_device(self, port_name, baudrate=115200):
        if self.serial.isOpen():
            self.serial.close()
        self.serial.setPortName(port_name)
        self.serial.setBaudRate(baudrate)


        if not self.serial.open(QSerialPort.ReadWrite):
            self.error.emit("Failed to open serial port")
            return

        self.busy.emit(True)
        self._rx_buffer.clear()

        self._send_command(Command.CONNECT)

        self.timeout_timer.start(2000)

    def disconnect_device(self):
        if self.serial.isOpen():
            # Send DISCONNECT command (0x31)
            self._send_command(Command.DISCONNECT)

            self.serial.flush()

            self.serial.close()

        state.set_disconnected()
        self.disconnected.emit()


    def _send_command(self, cmd):
        self.serial.write(bytes([cmd]))

    def _on_ready_read(self):
        self._rx_buffer.extend(self.serial.readAll())

        expected_size = 63

        # Expecting: ACK + ID + FW_MAJ + FW_MIN
        if len(self._rx_buffer) < expected_size:
            return

        self.timeout_timer.stop()
        self.busy.emit(False)

        response = self._rx_buffer[0]

        if response == Command.ACK:
            try:
                struct_data = self._rx_buffer[1:expected_size]

                unpacked = struct.unpack('<32s6sI4B4I', struct_data)

                serial_no = unpacked[0].decode('utf-8').rstrip('\x00')
                fw_vers = unpacked[1].decode('utf-8').rstrip('\x00')
                num_channel = unpacked[2]

                type = unpacked[3:7]
                speeds = unpacked[7:11]

                # Map Type ID to String (match your C code logic)
                type_map = {1: "Classic", 2: "CANFD"}
                channel_info = []
                for i in range(num_channel):
                    t_str = type_map.get(type[i], "Unknown")
                    channel_info.append({
                        "id": i,
                        "type": t_str,
                        "speed": speeds[i]
                    })

                    print(
                        f"Channel {i} :"
                        f"Type ID = {t_str} ({t_str}),"
                        f"Speed = {speeds[i]}"
                    )

                device_info = {
                    "serial_no": serial_no,
                    "fw": fw_vers,
                    "num_channels": num_channel,
                    "channels": channel_info,
                }

                state.update_state(device_info)
                self.connected.emit(device_info)

            except Exception as e:
                self.error.emit(f"Parsing error: {str(e)}")

        else:
            self.error.emit("Failed to read response")

        self._rx_buffer.clear()

    def _on_timeout(self):
        self.busy.emit(False)
        self.error.emit("Timed out")
        if self.serial.isOpen():
            self.serial.close()