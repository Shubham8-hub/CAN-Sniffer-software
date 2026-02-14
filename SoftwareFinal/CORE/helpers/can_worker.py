from PySide6.QtCore import QThread, Signal, QMutex
from CORE.tester.transmit_test import TestTraceGenerator
from CORE.helpers.device_record import state
import time
import struct

class CanReceiverThread(QThread):
    # Signal to send data back to GUI (e.g., to TraceWindow)
    data_received = Signal(object)

    def __init__(self, serial_mgr):
        super().__init__()
        self.serial_mgr = serial_mgr
        self._is_running = True
        self.testtrace = 0
        self.tester = None


        # --- TESTER CONFIGURATION ---
        self.testtrace = 0  # 0 = Real Data, 1 = Simulation Mode
        self.tester = TestTraceGenerator()
        self.mutex = QMutex()

    def set_test_mode(self, enabled: bool):
        """Helper to toggle mode safely from GUI"""
        self.mutex.lock()
        self.testtrace = 1 if enabled else 0
        self.mutex.unlock()

    def run(self):
        buffer = bytearray()
        PACKET_SIZE = 16  # Fixed packet size from your C code

        while self._is_running:
            # 1. SIMULATION MODE (Keep this if you use it)
            if self.testtrace == 1:
                data = self.tester.generate()
                self.data_received.emit(data)
                self.msleep(100)
                continue

            # 2. REAL DATA MODE
            # We must access the QSerialPort object from the manager
            if self.serial_mgr and self.serial_mgr.serial.isOpen() and getattr(self.serial_mgr, 'is_sniffing', False):

                # A. Read all available bytes from the port
                available_bytes = self.serial_mgr.serial.readAll()
                if len(available_bytes) > 0:

                    raw_hex = available_bytes.data().hex().upper()
                    print(f"DEBUG RX: {raw_hex}")
                    buffer.extend(available_bytes.data())  # Convert QByteArray to Python bytes/bytearray

                # B. Process Buffer
                while len(buffer) >= PACKET_SIZE:

                    # Search for Header (0xAA)
                    if buffer[0] != 0xAA:
                        # If first byte isn't AA, pop it and check next
                        buffer.pop(0)
                        continue

                    # Check Footer (0xBB) at index 15
                    if buffer[15] != 0xBB:
                        # Header found but footer missing -> corrupt packet
                        # Remove the header so we can search for a new one
                        buffer.pop(0)
                        continue
                    print(f"DEBUG PKT: ID={struct.unpack('<I', buffer[2:6])[0]:X}")

                    # --- VALID PACKET FOUND ---
                    # Format: AA [CH] [ID:4] [DLC] [DATA:8] BB

                    channel = buffer[1]

                    # Unpack ID (4 bytes, Little Endian)
                    can_id = struct.unpack('<I', buffer[2:6])[0]

                    dlc = buffer[6]
                    data_bytes = list(buffer[7:15])  # Extract 8 data bytes

                    # Create packet dictionary
                    packet = {
                        'timestamp': f"{time.time() % 1000:.3f}",
                        'can_id': f"{can_id:X}",
                        'type': 'EXT' if can_id > 0x7FF else 'STD',
                        'direction': 'Rx',
                        'channel': channel,
                        'dlc': dlc,
                        'data': data_bytes
                    }

                    # Send to GUI
                    self.data_received.emit(packet)

                    # Remove processed packet from buffer
                    del buffer[0:PACKET_SIZE]

                    # ADD THIS: Prevent infinite loop on corrupted data
                    if len(buffer) > 1000:  # Safety limit
                        print("WARNING: Buffer overflow, clearing corrupted data")
                        buffer.clear()
                        break

            # Sleep briefly to prevent 100% CPU usage
            self.msleep(1)

    def stop(self):
        """Safely stop the thread"""
        self._is_running = False
        self.quit()
        self.wait()