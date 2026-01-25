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

#include <string.h>


const char company_code[] = "BTB";
const char product_code[] = "CS";
const char product_type[] = "ALL";

static device_info_t dev_info;

void update_device_info(void)
{
	// Generate the serial number into the buffer size
	generate_serial_number(dev_info.serial_no, sizeof(dev_info.serial_no));

	// Filling other parameter
	strncpy(dev_info.fw_version, "1.0.0", sizeof(dev_info.fw_version));
	dev_info.no_of_CAN_Channel = 2;
	dev_info.CAN_type[0] = 2;
	dev_info.CAN_type[1] = 2;
	dev_info.CAN_Channel_speed[0] = 800000;
	dev_info.CAN_Channel_speed[1] = 500000;
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
}

void generate_serial_number(char *serial_buffer, size_t buffer_size)
{
	uint32_t uid = HAL_GetUIDw2();

	snprintf(serial_buffer, buffer_size, "%s-%s-%s-%08lX", company_code, product_code, product_type, uid);
}
