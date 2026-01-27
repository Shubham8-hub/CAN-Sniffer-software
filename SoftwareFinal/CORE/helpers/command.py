
class Command:

    # Command for Connect and disconnect
    CONNECT     =   0x30
    DISCONNECT  =   0x31




    # Command for response from device
    ACK         =   0x40
    NACK        =   0x41

    # Command for Starting and stopping the snipping
    START_SNIFF =   0x60
    STOP_SNIFF  =   0x61

    # Command for setting the baudrate
    BAUD_RATES = [
        {"label": "125 KBPS", "bps": 125000, "cmd": 0x71},
        {"label": "250 KBPS", "bps": 250000, "cmd": 0x72},
        {"label": "500 KBPS", "bps": 500000, "cmd": 0x73},
        {"label": "1 MBPS", "bps": 1000000, "cmd": 0x74},
        {"label": "2 MBPS", "bps": 2000000, "cmd": 0x75},
        {"label": "2.5 MBPS", "bps": 2500000, "cmd": 0x76},
        {"label": "3 MBPS", "bps": 3000000, "cmd": 0x77},
        {"label": "4 MBPS", "bps": 4000000, "cmd": 0x78},
        {"label": "5 MBPS", "bps": 5000000, "cmd": 0x79},
        {"label": "6 MBPS", "bps": 6000000, "cmd": 0x80},
        {"label": "7 MBPS", "bps": 7000000, "cmd": 0x81},
        {"label": "8 MBPS", "bps": 8000000, "cmd": 0x82},
    ]

    #Command for reading the baudrate
    CMD_READ_BAUDRATE = 0x32