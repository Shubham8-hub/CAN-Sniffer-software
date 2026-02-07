/*
 * command.h
 *
 *  Created on: 21-Dec-2025
 *      Author: shubh
 */

#ifndef PROTOCOL_COMMAND_H_
#define PROTOCOL_COMMAND_H_

#include <stdint.h>
#include <stddef.h>

#define CMD_CONNECT					0x30
#define CMD_DISCONNECT				0x31

#define RESP_ACK					0x40
#define RESP_NACK					0x41

#define CMD_CAN_TX					0x50
#define CMD_START_TRACE				0x51
#define CMD_STOP_TRACE				0x52

#define CMD_READ_BAUDRATE			0x32
#define CMD_SET_BAUDRATE			0x33

#define MAX_CAN_CHANNEL				4

typedef struct __attribute__((packed))
{
	char serial_no[32];
	char fw_version[6];
	uint32_t no_of_CAN_Channel;
	uint8_t CAN_type[MAX_CAN_CHANNEL];
	uint32_t CAN_Channel_speed[MAX_CAN_CHANNEL];
	uint32_t CAN_Channel_current_baud[MAX_CAN_CHANNEL];
}device_info_t;




void command_process(uint8_t cmd);
void generate_serial_number(char *serial_buffer, size_t buffer_size);


#endif /* PROTOCOL_COMMAND_H_ */
