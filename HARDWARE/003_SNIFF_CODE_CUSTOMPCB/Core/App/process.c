/*
 * process.c
 *
 *  Created on: 21-Dec-2025
 *      Author: shubh
 */

#include "process.h"
#include "command.h"
#include "usbd_cdc_if.h"
#include "stm32g4xx_hal_fdcan.h"
#include "main.h"

extern FDCAN_HandleTypeDef hfdcan3;
extern FDCAN_HandleTypeDef hfdcan2;

TaskHandle_t heartbeatTaskHandle;
TaskHandle_t usbRxTaskHandle;

QueueHandle_t usbRxQueue;
QueueHandle_t usbTxQueue;
QueueHandle_t canRxQueue;

static uint32_t encode_dlc(uint8_t dlc);

void process_init(void)
{
	  usbRxQueue =	xQueueCreate(32,sizeof(uint8_t));
	  configASSERT(usbRxQueue != NULL);

	  usbTxQueue = xQueueCreate(128, 14);
	  configASSERT(usbTxQueue != NULL);

	  canRxQueue	=	xQueueCreate(16,sizeof(CANFrame_t));
	  configASSERT(canRxQueue != NULL);

	  xTaskCreate(HeartbeatTask, "HeartBeat", 128, NULL, tskIDLE_PRIORITY+1, &heartbeatTaskHandle);

	  xTaskCreate(UsbRxTask, "USB RX", 256, NULL, tskIDLE_PRIORITY+2, &usbRxTaskHandle);

	  xTaskCreate(UsbTxTask, "USB_TX", 256, NULL, tskIDLE_PRIORITY+2, NULL);

	  xTaskCreate(CAN_RxTask, "CAN RX", 256, NULL, tskIDLE_PRIORITY+2, NULL);

}

void HeartbeatTask(void *argument)
{
	(void)argument;

	for(;;)
	{
		HAL_GPIO_TogglePin(LED4_GPIO_Port, LED4_Pin);
		vTaskDelay(pdMS_TO_TICKS(1000));
	}
}

void UsbRxTask(void *argument)
{
	(void)argument;
	uint8_t cmdByte;

	for(;;)
	{
		if (xQueueReceive(usbRxQueue, &cmdByte, portMAX_DELAY)==pdPASS)
		{
			command_process(cmdByte);

		}
	}
}


void UsbTxTask(void *argument)
{
    uint8_t resp[14];

    for(;;)
    {
        if (xQueueReceive(usbTxQueue, resp, portMAX_DELAY) == pdPASS)
        {
            // Wait until USB is ready
            while (CDC_Transmit_FS(resp, 14) == USBD_BUSY)
            {
                vTaskDelay(pdMS_TO_TICKS(1));
            }
        }
    }
}


void CAN_RxTask(void *argument)
{
    CANFrame_t frame;
    uint8_t resp[14];

    resp[0] = CMD_CAN_RX; // CAN RX

    for (;;)
    {
        if (xQueueReceive(canRxQueue, &frame, portMAX_DELAY) == pdPASS)
        {
            resp[1] = (frame.id      ) & 0xFF;
            resp[2] = (frame.id >> 8 ) & 0xFF;
            resp[3] = (frame.id >> 16) & 0xFF;
            resp[4] = (frame.id >> 24) & 0xFF;
            resp[5] = frame.dlc;
            memcpy(&resp[6], frame.data, 8);

            xQueueSend(usbTxQueue, resp, 0);
        }
    }
}

void process_handle_can_tx(void)
{
    uint8_t buf[13];
    for(int i=0;i<13;i++)
        xQueueReceive(usbRxQueue, &buf[i], portMAX_DELAY);

    uint32_t canId = buf[0] | (buf[1]<<8) | (buf[2]<<16) | (buf[3]<<24);
    uint8_t dlc = buf[4];

    FDCAN_TxHeaderTypeDef TxHeader = {
        .Identifier = canId,
        .IdType = FDCAN_STANDARD_ID,
        .TxFrameType = FDCAN_DATA_FRAME,
        .DataLength = encode_dlc(dlc),
        .FDFormat = FDCAN_CLASSIC_CAN,
        .BitRateSwitch = FDCAN_BRS_OFF
    };

    HAL_FDCAN_AddMessageToTxFifoQ(&hfdcan3, &TxHeader, &buf[5]);
}

static uint32_t encode_dlc(uint8_t dlc)
{
    switch(dlc) {
        case 0: return FDCAN_DLC_BYTES_0;
        case 1: return FDCAN_DLC_BYTES_1;
        case 2: return FDCAN_DLC_BYTES_2;
        case 3: return FDCAN_DLC_BYTES_3;
        case 4: return FDCAN_DLC_BYTES_4;
        case 5: return FDCAN_DLC_BYTES_5;
        case 6: return FDCAN_DLC_BYTES_6;
        case 7: return FDCAN_DLC_BYTES_7;
        default:return FDCAN_DLC_BYTES_8;
    }
}

