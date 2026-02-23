#ifndef CAN_PROTOCOL_H
#define CAN_PROTOCOL_H

#include <stdint.h>

#define CMD_CONNECT         0x30
#define CMD_DISCONNECT      0x31

#define CMD_READ_BAUDRATE   0x32
#define CMD_SET_BAUDRATE    0x33

#define RESP_ACK            0x40
#define RESP_NACK           0x41

#define CMD_CAN_TX          0x50
#define CMD_START_TRACE     0x51
#define CMD_STOP_TRACE      0x52

#define MAX_CAN_CHANNEL 4

// Force 1-byte alignment so it exactly matches the STM32 struct
#pragma pack(push,1)
struct device_info_t
{
    char serial_no[32];
    char fw_version[6];
    uint32_t no_of_CAN_Channel;
    uint8_t CAN_type[MAX_CAN_CHANNEL];
    uint32_t CAN_Channel_speed[MAX_CAN_CHANNEL];
    uint32_t CAN_Channel_current_baud[MAX_CAN_CHANNEL];
};
#pragma pack(pop)
#endif // CAN_PROTOCOL_H
