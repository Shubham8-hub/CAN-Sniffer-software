/*
 * can_setting.h
 *
 *  Created on: 02-Feb-2026
 *      Author: shubh
 */

#ifndef CAN_SETTING_H_
#define CAN_SETTING_H_

#include "main.h"

// Define the Baudrate command
#define CMD_BAUD_125K    0x71
#define CMD_BAUD_250K    0x72
#define CMD_BAUD_500K    0x73
#define CMD_BAUD_1M      0x74
#define CMD_BAUD_2M      0x75
#define CMD_BAUD_2_5M    0x76
#define CMD_BAUD_3M      0x77
#define CMD_BAUD_4M      0x78
#define CMD_BAUD_5M      0x79
#define CMD_BAUD_6M      0x80
#define CMD_BAUD_7M      0x81
#define CMD_BAUD_8M      0x82

// Hardware Mapping
// Software Channel 0 : Hardware FDCAN2
// Software Channel 1 : Hardware FDCAN3
#define PHY_CH0_HANDLE		&hfdcan2
#define PHY_CH1_HANDLE		&hfdcan3

// Helper struct to store timing params
typedef struct
{
	uint8_t cmd_byte;
	uint32_t speed_bps;
	uint32_t prescaler;
	uint32_t time_seg1;
	uint32_t time_seg2;
	uint32_t sjw;
}CAN_Timing_t;



void CAN_Setting_Init(void);
uint8_t CAN_Set_Baudrate(uint8_t ch_idx, uint8_t baud_cmd);
//uint32_t CAN_Get_Current_Baudrate(uint8_t ch_idx);
uint32_t CAN_Get_Baudrate(uint8_t ch_idx);

#endif /* CAN_SETTING_H_ */
