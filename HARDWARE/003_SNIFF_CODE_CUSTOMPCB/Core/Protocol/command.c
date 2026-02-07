/*
 * command.c
 *
 *  Created on: 21-Dec-2025
 *      Author: shubh
 */

#include "command.h"
#include "process.h"
#include "usbd_cdc_if.h"
#include "main.h"
#include "can_setting.h"
#include <string.h>




const char company_code[] = "BTB";
const char product_code[] = "CS";
const char product_type[] = "ALL";

static device_info_t dev_info;

extern FDCAN_HandleTypeDef hfdcan3;
extern FDCAN_HandleTypeDef hfdcan2;

volatile uint8_t is_trace_running = 0;

void update_device_info(void)
{
	// Generate the serial number into the buffer size
	generate_serial_number(dev_info.serial_no, sizeof(dev_info.serial_no));

	// Filling other parameter
	strncpy(dev_info.fw_version, "1.0.0", sizeof(dev_info.fw_version));
	dev_info.no_of_CAN_Channel = 2;
	dev_info.CAN_type[0] = 2;
	dev_info.CAN_type[1] = 2;
	dev_info.CAN_Channel_speed[0] = 8000000;
	dev_info.CAN_Channel_speed[1] = 5000000;

	dev_info.CAN_Channel_current_baud[0] = CAN_Get_Baudrate(0);
	dev_info.CAN_Channel_current_baud[1] = CAN_Get_Baudrate(1);
}

void command_process(uint8_t cmd)
{
	if(cmd == CMD_CONNECT)
	{
		HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_SET);

		update_device_info();

		uint8_t resp_buf[1+sizeof(device_info_t)];

		resp_buf[0] = RESP_ACK;

		memcpy(&resp_buf[1], &dev_info, sizeof(device_info_t));

	    CDC_Transmit_FS(resp_buf, sizeof(resp_buf));

		vTaskDelay(pdMS_TO_TICKS(5));
	}

	else if (cmd == CMD_DISCONNECT)
	{
		HAL_GPIO_WritePin(LED1_GPIO_Port, LED1_Pin, GPIO_PIN_RESET);
	}

	else if (cmd == CMD_CAN_TX)
	{
		process_handle_can_tx();
	}

	// Read Current baudrate
//	else if (cmd == CMD_READ_BAUDRATE)
//	{
//		uint32_t speed = CAN_Get_Current_Baudrate(&hfdcan3);
//		uint8_t resp[5];
//		resp[0] = CMD_READ_BAUDRATE;
//		resp[1] = (speed >> 0) & 0xFF;
//		resp[2] = (speed >> 8) & 0xFF;
//		resp[3] = (speed >> 16) & 0xFF;
//		resp[4] = (speed >> 24) & 0xFF;
//
//		CDC_Transmit_FS(resp, 5);
//	}
	else if (cmd == CMD_READ_BAUDRATE) // 0x32
	    {
	        uint8_t ch_idx = 0;

	        // 1. Wait for the 2nd byte (Channel ID) from Python
	        // Python sends: [0x32, 0x00] (for Ch0) or [0x32, 0x01] (for Ch1)
	        if (xQueueReceive(usbRxQueue, &ch_idx, pdMS_TO_TICKS(10)) == pdPASS)
	        {
	            // 2. Get the ACTIVE speed for this specific channel
	            // This function (in can_setting.c) looks up 'current_baud_chX'
	            uint32_t speed = CAN_Get_Baudrate(ch_idx);

	            uint8_t resp[6];
	            resp[0] = CMD_READ_BAUDRATE; // Echo Command
	            resp[1] = ch_idx;            // Echo Channel ID
	            resp[2] = (speed >> 0) & 0xFF;
	            resp[3] = (speed >> 8) & 0xFF;
	            resp[4] = (speed >> 16) & 0xFF;
	            resp[5] = (speed >> 24) & 0xFF;

	            // 3. Send response back: [0x32, CH, SP, SP, SP, SP]
	            CDC_Transmit_FS(resp, 6);
	        }
	    }

	// ---  Handle Set Baud Rate (0x71 to 0x82) ---
	else if (cmd == CMD_SET_BAUDRATE)
	{
		uint8_t payload[2]; // Buffer for [Channel, Baud]

		// Try to read 2 bytes from the Queue
		// Note: We read one by one
		if (xQueueReceive(usbRxQueue, &payload[0], pdMS_TO_TICKS(10)) == pdPASS) // Channel
		{
			if (xQueueReceive(usbRxQueue, &payload[1], pdMS_TO_TICKS(10)) == pdPASS) // Baud Cmd
			{
				uint8_t ch_idx = payload[0];
				uint8_t baud_cmd = payload[1];

				// 1. Apply Settings
				CAN_Set_Baudrate(ch_idx, baud_cmd);

				// 2. Update Global Info (so next Connect is accurate)
				update_device_info();

				// 3. Optional: Echo back to Python to confirm
				// Format: [0x33] [CH] [BAUD_CMD]
				uint8_t resp[3] = {CMD_SET_BAUDRATE, ch_idx, baud_cmd};
				CDC_Transmit_FS(resp, 3);
			}
		}
	}

	// Starting the trace
	else if (cmd == CMD_START_TRACE)
	{
		is_trace_running = 1;
		// Next send the ack
	}

	else if (cmd == CMD_STOP_TRACE)
	{
		is_trace_running = 0;
	}

}

void generate_serial_number(char *serial_buffer, size_t buffer_size)
{
	uint32_t uid = HAL_GetUIDw2();

	snprintf(serial_buffer, buffer_size, "%s-%s-%s-%08lX", company_code, product_code, product_type, uid);
}
