import random
import time


class TestTraceGenerator:
    def __init__(self):
        # Define a few "devices" on the bus to simulate
        self.simulated_devices = [
            {'id': '101', 'dlc': 8, 'data': [0, 0, 0, 0, 0, 0, 0, 0]},  # Engine
            {'id': '2F1', 'dlc': 8, 'data': [10, 20, 30, 40, 50, 60, 70, 80]},  # Body
            {'id': '405', 'dlc': 4, 'data': [0xAA, 0xBB, 0xCC, 0xDD]},  # Sensor
            {'id': '18DAF110', 'dlc': 8, 'data': [0, 0, 0, 0, 0, 0, 0, 0]}  # Diagnostic
        ]

    def generate(self):
        """Generates a single random CAN packet"""

        # 1. Pick a random device to simulate
        device = random.choice(self.simulated_devices)

        # 2. Mutate the data slightly (to test highlighting)
        # We change one random byte in the data
        idx_to_change = random.randint(0, device['dlc'] - 1)
        device['data'][idx_to_change] = random.randint(0, 255)

        # 3. Construct the packet dictionary
        packet = {
            'timestamp': f"{time.time() % 1000:.3f}",
            'can_id': device['id'],
            'type': 'STD' if len(device['id']) == 3 else 'EXT',
            'direction': 'Rx',
            'channel': 1,
            'dlc': device['dlc'],
            'data': list(device['data'])  # Return a copy so we don't mess up next loop
        }

        return packet

#
# class TestTraceGenerator:
#     def __init__(self):
#         pass
#
#     def generate(self):
#         """Generates a random CAN packet (STD or EXT)"""
#
#         # 1. Randomly decide Type (Standard vs Extended)
#         # Let's say 50% chance for each
#         is_extended = random.choice([True, False])
#
#         if is_extended:
#             # Extended ID (29-bit): 0 to 0x1FFFFFFF
#             can_id_int = random.randint(0, 0x1FFFFFFF)
#             can_type = "EXT"
#             can_id_str = f"{can_id_int:08X}"  # 8 chars for Extended
#         else:
#             # Standard ID (11-bit): 0 to 0x7FF
#             can_id_int = random.randint(0, 0x7FF)
#             can_type = "STD"
#             can_id_str = f"{can_id_int:03X}"  # 3 chars for Standard
#
#         # 2. Random DLC (Data Length) 1 to 8 bytes
#         dlc = random.randint(1, 8)
#
#         # 3. Generate Random Data Bytes
#         data_bytes = [random.randint(0, 255) for _ in range(dlc)]
#
#         # 4. Construct Packet
#         packet = {
#             'timestamp': f"{time.time() % 1000:.3f}",
#             'can_id': can_id_str,
#             'type': can_type,
#             'direction': 'Rx',
#             'channel': random.randint(1, 2),  # Random Channel 1 or 2
#             'dlc': dlc,
#             'data': data_bytes
#         }
#
#         return packet