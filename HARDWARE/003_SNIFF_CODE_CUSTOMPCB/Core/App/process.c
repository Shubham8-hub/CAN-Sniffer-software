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
TaskHandle_t ledTaskHandle;

QueueHandle_t usbRxQueue;
QueueHandle_t usbTxQueue;
QueueHandle_t canRxQueue;

static uint32_t encode_dlc(uint8_t dlc);
static uint32_t raw_dlc_to_hal(uint8_t dlc);

volatile uint8_t ch0_activity_flag = 0;
volatile uint8_t ch1_activity_flag = 0;

void process_init(void)
{
	  usbRxQueue =	xQueueCreate(32,sizeof(uint8_t));
	  configASSERT(usbRxQueue != NULL);

	  usbTxQueue = xQueueCreate(128, 16);
	  configASSERT(usbTxQueue != NULL);

	  canRxQueue	=	xQueueCreate(16,sizeof(CANFrame_t));
	  configASSERT(canRxQueue != NULL);

	  xTaskCreate(HeartbeatTask, "HeartBeat", 128, NULL, tskIDLE_PRIORITY+1, &heartbeatTaskHandle);

	  xTaskCreate(LedIndicatorTask, "LedInd", 128, NULL, tskIDLE_PRIORITY+1, &ledTaskHandle);

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
    uint8_t resp[16];

    for(;;)
    {
        if (xQueueReceive(usbTxQueue, resp, portMAX_DELAY) == pdPASS)
        {
        	uint8_t len = (resp[0] == 0xAA) ? 16 : 14;
            // Wait until USB is ready
            while (CDC_Transmit_FS(resp, len) == USBD_BUSY)
            {
                vTaskDelay(pdMS_TO_TICKS(1));
            }
        }
    }
}


//void CAN_RxTask(void *argument)
//{
//    CANFrame_t frame;
//    uint8_t resp[14];
//
//    resp[0] = CMD_CAN_RX; // CAN RX
//
//    for (;;)
//    {
//        if (xQueueReceive(canRxQueue, &frame, portMAX_DELAY) == pdPASS)
//        {
//            resp[1] = (frame.id      ) & 0xFF;
//            resp[2] = (frame.id >> 8 ) & 0xFF;
//            resp[3] = (frame.id >> 16) & 0xFF;
//            resp[4] = (frame.id >> 24) & 0xFF;
//            resp[5] = frame.dlc;
//            memcpy(&resp[6], frame.data, 8);
//
//            xQueueSend(usbTxQueue, resp, 0);
//        }
//    }
//}

void CAN_RxTask(void *argument)
{
    CANFrame_t frame;
    uint8_t usb_packet[16]; // Our 16-byte packet buffer

    for(;;)
    {
        // Wait for data from the ISR/Callback
        if (xQueueReceive(canRxQueue, &frame, portMAX_DELAY) == pdPASS)
        {
        	// --- 1. SET ACTIVITY FLAGS ---
			if (frame.channel == 0) {
				ch0_activity_flag = 1;
			}
			else if (frame.channel == 1) {
				ch1_activity_flag = 1;
			}
			// -----------------------------
            // Only send to USB if Trace is Active
            if (is_trace_running)
            {
                // 1. Header
                usb_packet[0] = 0xAA;

                // 2. Channel
                usb_packet[1] = frame.channel;

                // 3. CAN ID (Little Endian)
                usb_packet[2] = (uint8_t)(frame.id & 0xFF);
                usb_packet[3] = (uint8_t)((frame.id >> 8) & 0xFF);
                usb_packet[4] = (uint8_t)((frame.id >> 16) & 0xFF);
                usb_packet[5] = (uint8_t)((frame.id >> 24) & 0xFF);

                // 4. DLC
                usb_packet[6] = frame.dlc;

                // 5. Data (8 Bytes) - Copy safe
                memset(&usb_packet[7], 0, 8); // Clear buffer first
                memcpy(&usb_packet[7], frame.data, (frame.dlc > 8) ? 8 : frame.dlc);

                // 6. Footer
                usb_packet[15] = 0xBB;

                // 7. Send to USB Queue
                // Note: Ensure your USB Task sends all 16 bytes!
//                CDC_Transmit_FS(usb_packet, 16);
                xQueueSend(usbTxQueue,usb_packet,portMAX_DELAY);
            }
        }

    }

}

//void process_handle_can_tx(void)
//{
//    uint8_t buf[13];
//    for(int i=0;i<13;i++)
//        xQueueReceive(usbRxQueue, &buf[i], portMAX_DELAY);
//
//    uint32_t canId = buf[0] | (buf[1]<<8) | (buf[2]<<16) | (buf[3]<<24);
//    uint8_t dlc = buf[4];
//
//    FDCAN_TxHeaderTypeDef TxHeader = {
//        .Identifier = canId,
//        .IdType = FDCAN_STANDARD_ID,
//        .TxFrameType = FDCAN_DATA_FRAME,
//        .DataLength = encode_dlc(dlc),
//        .FDFormat = FDCAN_CLASSIC_CAN,
//        .BitRateSwitch = FDCAN_BRS_OFF
//    };
//
//    HAL_FDCAN_AddMessageToTxFifoQ(&hfdcan3, &TxHeader, &buf[5]);
//}

void process_handle_can_tx(void)
{
    uint8_t ch_idx;
    uint8_t id_buf[4];
    uint32_t can_id;
    uint8_t dlc_val;
    uint8_t data[64];
    uint8_t footer;

    // 1. Read Channel
    if(xQueueReceive(usbRxQueue, &ch_idx, pdMS_TO_TICKS(10)) != pdPASS) return;

    // 2. Read ID (4 Bytes, Little Endian)
    for(int i=0; i<4; i++) {
        if(xQueueReceive(usbRxQueue, &id_buf[i], pdMS_TO_TICKS(10)) != pdPASS) return;
    }
    can_id = id_buf[0] | (id_buf[1] << 8) | (id_buf[2] << 16) | (id_buf[3] << 24);

    // 3. Read DLC (Raw Data Length)
    if(xQueueReceive(usbRxQueue, &dlc_val, pdMS_TO_TICKS(10)) != pdPASS) return;

    // Safety Cap
    if (dlc_val > 64) dlc_val = 64;

    // 4. Read Data Payload
    for(int i=0; i<dlc_val; i++) {
        if(xQueueReceive(usbRxQueue, &data[i], pdMS_TO_TICKS(10)) != pdPASS) return;
    }

    // 5. Read Footer (Expect 0xBB)
    if(xQueueReceive(usbRxQueue, &footer, pdMS_TO_TICKS(10)) != pdPASS) return;

    if (footer != 0xBB) {
        // Footer mismatch error - Packet likely corrupted
        return;
    }

    // --- 6. Configure CAN Header ---
    FDCAN_TxHeaderTypeDef TxHeader;

    TxHeader.Identifier = can_id;

    // Auto-detect Extended ID (29-bit) vs Standard (11-bit)
    if (can_id > 0x7FF) {
        TxHeader.IdType = FDCAN_EXTENDED_ID;
    } else {
        TxHeader.IdType = FDCAN_STANDARD_ID;
    }

    TxHeader.TxFrameType = FDCAN_DATA_FRAME;
    TxHeader.DataLength = raw_dlc_to_hal(dlc_val);
    TxHeader.ErrorStateIndicator = FDCAN_ESI_ACTIVE;
    TxHeader.TxEventFifoControl = FDCAN_NO_TX_EVENTS;
    TxHeader.MessageMarker = 0;

    // Auto-detect CAN FD vs Classic based on Data Length
    // (If DLC > 8, it MUST be FD. If <=8, we default to Classic for compatibility)
    if (dlc_val > 8) {
        TxHeader.FDFormat = FDCAN_FD_CAN;
        TxHeader.BitRateSwitch = FDCAN_BRS_ON; // Enable Fast Bitrate for FD
    } else {
        TxHeader.FDFormat = FDCAN_CLASSIC_CAN;
        TxHeader.BitRateSwitch = FDCAN_BRS_OFF;
    }

    // --- 7. Select Hardware Channel ---
    // Assuming: Channel 0 -> hfdcan2, Channel 1 -> hfdcan3 (Check your main.c for correct mapping)
    FDCAN_HandleTypeDef *hfdcan = NULL;
    if (ch_idx == 0) hfdcan = &hfdcan2;
    else if (ch_idx == 1) hfdcan = &hfdcan3;

    if (hfdcan != NULL) {
        // Send Message
        HAL_FDCAN_AddMessageToTxFifoQ(hfdcan, &TxHeader, data);
    }
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

// Helper to convert raw integer length (e.g. 8) to FDCAN Enum (e.g. FDCAN_DLC_BYTES_8)
static uint32_t raw_dlc_to_hal(uint8_t dlc) {
    if (dlc <= 0) return FDCAN_DLC_BYTES_0;
    if (dlc == 1) return FDCAN_DLC_BYTES_1;
    if (dlc == 2) return FDCAN_DLC_BYTES_2;
    if (dlc == 3) return FDCAN_DLC_BYTES_3;
    if (dlc == 4) return FDCAN_DLC_BYTES_4;
    if (dlc == 5) return FDCAN_DLC_BYTES_5;
    if (dlc == 6) return FDCAN_DLC_BYTES_6;
    if (dlc == 7) return FDCAN_DLC_BYTES_7;
    if (dlc == 8) return FDCAN_DLC_BYTES_8;
    if (dlc <= 12) return FDCAN_DLC_BYTES_12;
    if (dlc <= 16) return FDCAN_DLC_BYTES_16;
    if (dlc <= 20) return FDCAN_DLC_BYTES_20;
    if (dlc <= 24) return FDCAN_DLC_BYTES_24;
    if (dlc <= 32) return FDCAN_DLC_BYTES_32;
    if (dlc <= 48) return FDCAN_DLC_BYTES_48;
    return FDCAN_DLC_BYTES_64;
}

void LedIndicatorTask(void *argument)
{
    for(;;)
    {
        // Run every 250ms.
        // 250ms ON + 250ms OFF = 500ms Blink Cycle
        vTaskDelay(pdMS_TO_TICKS(250));

        // --- Channel 0 (LED 2) ---
        if (ch0_activity_flag == 1)
        {
            // Data received recently -> Toggle LED
            HAL_GPIO_TogglePin(LED2_GPIO_Port, LED2_Pin);

            // Clear flag. If data keeps coming, it will be set to 1 again
            // by CAN_RxTask before the next 250ms check.
            ch0_activity_flag = 0;
        }
        else
        {
            // No data recently -> Force LED OFF
            HAL_GPIO_WritePin(LED2_GPIO_Port, LED2_Pin, GPIO_PIN_RESET);
        }

        // --- Channel 1 (LED 3) ---
        if (ch1_activity_flag == 1)
        {
            HAL_GPIO_TogglePin(LED3_GPIO_Port, LED3_Pin);
            ch1_activity_flag = 0;
        }
        else
        {
            HAL_GPIO_WritePin(LED3_GPIO_Port, LED3_Pin, GPIO_PIN_RESET);
        }
    }
}
