/*
 * process.h
 *
 *  Created on: 21-Dec-2025
 *      Author: shubh
 */

#ifndef APP_PROCESS_H_
#define APP_PROCESS_H_

#include "FreeRTOS.h"
#include "queue.h"
#include <stdint.h>

typedef struct{
	uint32_t id;
	uint8_t dlc;
	uint8_t data[8];
	uint8_t channel;
}CANFrame_t;

extern QueueHandle_t usbRxQueue;

extern volatile uint8_t is_trace_running;

void process_init(void);

void HeartbeatTask(void *argument);
void UsbRxTask(void *argument);
void UsbTxTask(void *argument);
void CAN_RxTask(void *argument);
void LedIndicatorTask(void *argument);
void process_handle_can_tx(void);

extern QueueHandle_t canRxQueue;
extern QueueHandle_t canTxQueue;

#endif /* APP_PROCESS_H_ */
