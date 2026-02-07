# CORE/CAN/can_receive.py

class CanReceiveLogic:
    def __init__(self):
        # Dictionary to store the state of each CAN ID
        # Format: { 'CAN_ID_HEX': { 'row_index': 0, 'count': 1, 'last_data': [bytes] } }
        self.packet_map = {}
        self.next_row_index = 0

    def process_packet(self, data):
        """
        Processes incoming data and decides if we need to ADD a new row
        or UPDATE an existing one.

        Returns a dict:
        {
            'action': 'ADD' or 'UPDATE',
            'row_index': int,
            'can_id': str,
            'changed_indices': [list of int column indexes that changed],
            'formatted_data': dict (the data to show)
        }
        """
        can_id = data.get('can_id', '000')
        raw_data = data.get('data', [])  # Expecting list of hex strings or bytes

        # Ensure raw_data is a list of integers for comparison
        if isinstance(raw_data, str):
            # Handle space-separated string "FF 01" -> [255, 1]
            try:
                int_data = [int(x, 16) for x in raw_data.split()]
            except:
                int_data = []
        else:
            int_data = raw_data

        is_new_id = can_id not in self.packet_map

        if is_new_id:
            # --- NEW ENTRY ---
            row_idx = self.next_row_index
            self.packet_map[can_id] = {
                'row_index': row_idx,
                'count': 1,
                'last_data': int_data
            }
            self.next_row_index += 1

            return {
                'action': 'ADD',
                'row_index': row_idx,
                'count': 1,
                'changed_indices': [],  # Everything is new
                'int_data': int_data
            }

        else:
            # --- UPDATE ENTRY ---
            record = self.packet_map[can_id]
            record['count'] += 1
            row_idx = record['row_index']
            last_data = record['last_data']

            # Find which bytes changed (for highlighting)
            changed_indices = []
            for i in range(min(len(int_data), len(last_data))):
                if int_data[i] != last_data[i]:
                    changed_indices.append(i)

            # Update record
            record['last_data'] = int_data

            return {
                'action': 'UPDATE',
                'row_index': row_idx,
                'count': record['count'],
                'changed_indices': changed_indices,
                'int_data': int_data
            }

    def reset(self):
        self.packet_map.clear()
        self.next_row_index = 0