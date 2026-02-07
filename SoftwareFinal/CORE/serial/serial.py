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

    #Signal to update GUI when a read baudrate response comes in
    baud_read_response = Signal(int, int) #(channel_id, speed_bpd)

    def __init__(self):
        super().__init__()
        self.serial = QSerialPort()
        self.serial.readyRead.connect(self._on_ready_read)
        self._rx_buffer = bytearray()
        # self._tx_buffer = bytearray()

        self.is_sniffing = False

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

    def write_data(self, data: bytes):
        if self.serial.isOpen():
            self.serial.write(data)

    def _send_command(self, cmd):
        self.serial.write(bytes([cmd]))

    def start_sniffing(self):
        if self.serial.isOpen():
            self.is_sniffing = True
            # Send the Start Sniff Command (0x51)
            self._send_command(Command.START_SNIFF)


    def stop_sniffing(self):
        if self.serial.isOpen():
            # Send the Stop Sniff Command (0x52)
            self._send_command(Command.STOP_SNIFF)
            self.is_sniffing = False

    def _on_ready_read(self):

        if self.is_sniffing:
            return

        self._rx_buffer.extend(self.serial.readAll())

        # Check command type from first byte
        if len(self._rx_buffer) < 1:
            return

        cmd_type = self._rx_buffer[0]

        # ---------------------------------------------------------
        # CASE 1: CONNECTION ACK (Struct Response)
        # ---------------------------------------------------------
        if cmd_type == Command.ACK:
            # Struct Size: 32+6+4 + 4 + 16 + 16 = 78 bytes.
            # Total Frame: 1 (ACK) + 78 = 79 bytes
            expected_size = 79
            # Expecting: ACK + ID + FW_MAJ + FW_MIN
            if len(self._rx_buffer) < expected_size:
                return

            self.timeout_timer.stop()
            self.busy.emit(False)
            # response = self._rx_buffer[0]

        # if response == Command.ACK:
            try:
                struct_data = self._rx_buffer[1:expected_size]

                unpacked = struct.unpack('<32s6sI4B4I4I', struct_data)

                serial_no = unpacked[0].decode('utf-8').rstrip('\x00')
                fw_vers = unpacked[1].decode('utf-8').rstrip('\x00')
                num_channel = unpacked[2]

                type = unpacked[3:7]
                max_speeds = unpacked[7:11]             # Max Capabilites
                current_speeds = unpacked[11:15]        # Active Baudrates

                # Map Type ID to String (match your C code logic)
                type_map = {1: "Classic", 2: "CANFD"}
                channel_info = []
                for i in range(num_channel):
                    t_str = type_map.get(type[i], "Unknown")
                    channel_info.append({
                        "id": i,
                        "type": t_str,
                        "max_speed": max_speeds[i],      # Store Max speed
                        "current_speed": current_speeds[i] # Store Active speed
                    })

                    print(
                        f"Channel {i} :"
                        f"Type ID = {t_str} ({t_str}),"
                        f"Speed = {max_speeds[i]}"
                    )

                device_info = {
                    "serial_no": serial_no,
                    "fw": fw_vers,
                    "num_channels": num_channel,
                    "channels": channel_info,
                }

                state.update_state(device_info)
                self.connected.emit(device_info)
                # self._rx_buffer.clear()

                # Remove the processed packet from buffer
                self._rx_buffer = self._rx_buffer[expected_size:]

            except Exception as e:
                self.error.emit(f"Parsing error: {str(e)}")
                self._rx_buffer.clear()

        # ---------------------------------------------------------
        # CASE 2: READ BAUDRATE RESPONSE (0x32)
        # Format: [0x32] [CH_ID] [B0] [B1] [B2] [B3] (6 Bytes)
        # ---------------------------------------------------------
        elif cmd_type == Command.CMD_READ_BAUDRATE:
            if len(self._rx_buffer) < 6:
                return

            ch_id = self._rx_buffer[1]
            #unpack 4 byte as uint32 (speed)
            speed = struct.unpack('<I', self._rx_buffer[2:6])[0]

            print(f"Read Response: CH{ch_id} = {speed} bps")

            #Emit signal so GUI can update
            self.baud_read_response.emit(ch_id, speed)
            self._rx_buffer = self._rx_buffer[6:]

        elif cmd_type == Command.CMD_SET_BAUDRATE:
            if len(self._rx_buffer) < 3: return  # Expect [0x33, CH, CMD]

            ch_id = self._rx_buffer[1]
            baud_cmd = self._rx_buffer[2]
            print(f"Hardware Confirmed: Ch{ch_id} set to command {hex(baud_cmd)}")

            self._rx_buffer = self._rx_buffer[3:]  # Clear packet

        else:
            self.error.emit("Failed to read response")

        # self._rx_buffer.clear()

    def _on_timeout(self):
        self.busy.emit(False)
        self.error.emit("Timed out")
        if self.serial.isOpen():
            self.serial.close()

    def send_bytes(self, data):
        if self.serial.isOpen():
            self.serial.write(data)