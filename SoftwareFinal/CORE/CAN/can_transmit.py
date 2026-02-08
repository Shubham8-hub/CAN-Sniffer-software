# CORE/CAN/can_transmit.py

import struct
from CORE.helpers.command import Command


class CanTransmitLogic:
    def __init__(self, serial_manager=None):
        self.serial_mgr = serial_manager

    def create_packet(self, can_id, channel, data_bytes, is_fd=False):
        """
        Constructs the byte array to send to the hardware.
        Format based on your receive logic:
        [HEADER: AA] [CMD: 0x50] [CH] [ID:4] [DLC] [DATA: N] [FOOTER: BB]
        """

        # 1. Prepare Header and Footer
        HEADER = 0xAA
        FOOTER = 0xBB
        CMD = Command.CMD_CAN_TX  # 0x50

        # 2. Process ID (Ensure 4 bytes Little Endian)
        # If Extended (29-bit), we might need to flag it.
        # Usually, MSB is used for EXT flag or hardware handles it.
        # Here we just pack the ID as uint32.
        packed_id = struct.pack('<I', can_id)

        # 3. Process Data
        # Ensure data is list of integers
        if isinstance(data_bytes, str):
            # Convert "FF AA" string to [255, 170]
            data_bytes = [int(b, 16) for b in data_bytes.split()]

        # Calculate DLC (Data Length Code)
        # For CAN FD, DLC mapping might be complex, but usually, we send raw length
        dlc = len(data_bytes)

        # 4. Construct Payload
        # Structure: [CMD, CH, ID(4), DLC, DATA...]
        payload = bytearray()
        payload.append(CMD)
        payload.append(channel)
        payload.extend(packed_id)
        payload.append(dlc)
        payload.extend(data_bytes)

        # 5. Wrap in Frame
        frame = bytearray()
        frame.append(HEADER)
        frame.extend(payload)
        frame.append(FOOTER)

        return frame

    def send(self, packet):
        """Writes the packet to the serial port."""
        if self.serial_mgr and self.serial_mgr.serial.isOpen():
            self.serial_mgr.serial.write(packet)
            return True
        return False