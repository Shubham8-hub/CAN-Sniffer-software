/*
 * can_setting.c
 *
 *  Created on: 02-Feb-2026
 *      Author: shubh
 */


#include "can_setting.h"
#include <string.h>

extern FDCAN_HandleTypeDef hfdcan3;
extern FDCAN_HandleTypeDef hfdcan2;

// Current Baudrate command (Default Baudrate 500Kbps)
static uint8_t current_baud_ch0 = CMD_BAUD_500K;
static uint8_t current_baud_ch1 = CMD_BAUD_500K;
/* * TIMING LOOKUP TABLE
 * TODO: You MUST update these values based on your FDCAN Clock Source.
 * Example below assumes specific clock.
 * Use STM32CubeMX to find valid Prescaler/TS1/TS2 for your clock.
 */
static const CAN_Timing_t baud_table[] = {
    // Cmd,        		Speed,    	Presc, 	Seg1, 	Seg2, 	SJW
    {CMD_BAUD_125K, 	125000,	   	40,   	13,   	2,   	1},
    {CMD_BAUD_250K, 	250000,	   	20,    	13,   	2,   	1},
    {CMD_BAUD_500K, 	500000,	   	10,    	13,   	2,   	1}, // Default
    {CMD_BAUD_1M,   	1000000,	5,    	13,   	2,   	1},
	{CMD_BAUD_2M,   	2000000, 	4,		7,		2,		1},
    {CMD_BAUD_2_5M, 	2500000,	4,    	5,   	2,   	1},
    {CMD_BAUD_3M, 		3000000,	0,    	0,   	0,   	0},// unable to find
    {CMD_BAUD_4M,   	4000000,	2,    	7,   	2,   	1},
	{CMD_BAUD_5M,   	5000000, 	2,		5,		2,		1},
    {CMD_BAUD_6M, 		6000000,	0,    	0,   	0,   	0}, // unable to find
    {CMD_BAUD_7M, 		7000000,	0,    	0,   	0,   	0}, // unable to find
    {CMD_BAUD_8M,   	8000000,	1,    	7,   	2,   	1}
};

static const CAN_Timing_t* get_timing_by_cmd(uint8_t cmd) {
    int rows = sizeof(baud_table) / sizeof(baud_table[0]);
    for (int i = 0; i < rows; i++) {
        if (baud_table[i].cmd_byte == cmd) {
            return &baud_table[i];
        }
    }
    return NULL;
}

static FDCAN_HandleTypeDef* get_handle_by_index(uint8_t ch_idx) {
    if (ch_idx == 0) return PHY_CH0_HANDLE; // FDCAN2
    if (ch_idx == 1) return PHY_CH1_HANDLE; // FDCAN3
    return NULL;
}

//static uint32_t get_speed_by_cmd(uint8_t cmd) {
//    const CAN_Timing_t *t = get_timing_by_cmd(cmd);
//    return (t) ? t->speed_bps : 500000;
//}

// Internal function to apply config to hardware
//static void configure_fdcan_params(FDCAN_HandleTypeDef *hfdcan, const CAN_Timing_t *timing) {
//    hfdcan->Init.NominalPrescaler = timing->prescaler;
//    hfdcan->Init.NominalTimeSeg1 = timing->time_seg1;
//    hfdcan->Init.NominalTimeSeg2 = timing->time_seg2;
//    hfdcan->Init.NominalSyncJumpWidth = timing->sjw;
//
//    // Ensure standard settings are maintained
//    hfdcan->Init.ClockDivider = FDCAN_CLOCK_DIV1;
//    hfdcan->Init.FrameFormat = FDCAN_FRAME_CLASSIC; // Or FDCAN_FRAME_FD_BRS
//    hfdcan->Init.Mode = FDCAN_MODE_NORMAL;
//    hfdcan->Init.AutoRetransmission = ENABLE;
//    hfdcan->Init.TransmitPause = DISABLE;
//    hfdcan->Init.ProtocolException = DISABLE;
//    hfdcan->Init.StdFiltersNbr = 0;
//    hfdcan->Init.ExtFiltersNbr = 0;
//    hfdcan->Init.TxFifoQueueMode = FDCAN_TX_FIFO_OPERATION;
//}

void CAN_Setting_Init(void) {
    // 1. Initialize with default 500k
    CAN_Set_Baudrate(0, CMD_BAUD_500K);

    // 2. Initialize Channel 2 if needed
     CAN_Set_Baudrate(1, CMD_BAUD_500K);
}

//uint8_t CAN_Set_Baudrate(uint8_t ch_idx, uint8_t baud_cmd) {
//    FDCAN_HandleTypeDef *hfdcan = get_handle_by_index(ch_idx);
//    if (hfdcan == NULL) return 0;
//
//    const CAN_Timing_t *timing = get_timing_by_cmd(baud_cmd);
//    if (timing == NULL) {
//        // Fallback to default if invalid
//        timing = get_timing_by_cmd(CMD_BAUD_500K);
//        baud_cmd = CMD_BAUD_500K;
//    }
//
//    // 1. Stop and DeInit
//    if (HAL_FDCAN_GetState(hfdcan) != HAL_FDCAN_STATE_RESET) {
//        HAL_FDCAN_Stop(hfdcan);
//    }
//    HAL_FDCAN_DeInit(hfdcan);
//
//    // 2. Apply Timings (Important: Reset Instance!)
//    if (ch_idx == 0) hfdcan->Instance = FDCAN2;
//    else             hfdcan->Instance = FDCAN3;
//
//    hfdcan->Init.NominalPrescaler = timing->prescaler;
//    hfdcan->Init.NominalTimeSeg1 = timing->time_seg1;
//    hfdcan->Init.NominalTimeSeg2 = timing->time_seg2;
//    hfdcan->Init.NominalSyncJumpWidth = timing->sjw;
//
//    // Standard Config
//    hfdcan->Init.ClockDivider = FDCAN_CLOCK_DIV1;
//    hfdcan->Init.FrameFormat = FDCAN_FRAME_CLASSIC;
//    hfdcan->Init.Mode = FDCAN_MODE_NORMAL;
//    hfdcan->Init.AutoRetransmission = ENABLE;
//    hfdcan->Init.TransmitPause = DISABLE;
//    hfdcan->Init.ProtocolException = DISABLE;
//    hfdcan->Init.StdFiltersNbr = 0;
//    hfdcan->Init.ExtFiltersNbr = 0;
//    hfdcan->Init.TxFifoQueueMode = FDCAN_TX_FIFO_OPERATION;
//
//    // 3. Init and Start
//    if (HAL_FDCAN_Init(hfdcan) != HAL_OK) return 0;
//    if (HAL_FDCAN_Start(hfdcan) != HAL_OK) return 0;
//
//    // 4. Update State
//    if (ch_idx == 0) current_baud_ch0 = baud_cmd;
//    else             current_baud_ch1 = baud_cmd;
//
//    return 1;
//}

uint8_t CAN_Set_Baudrate(uint8_t ch_idx, uint8_t baud_cmd) {
    FDCAN_HandleTypeDef *hfdcan = get_handle_by_index(ch_idx);
    if (hfdcan == NULL) return 0; // Invalid channel

    const CAN_Timing_t *timing = get_timing_by_cmd(baud_cmd);
    if (timing == NULL) {
        // Fallback to default
        timing = get_timing_by_cmd(CMD_BAUD_500K);
        baud_cmd = CMD_BAUD_500K;
    }

    // 1. Stop and DeInit
    if (HAL_FDCAN_GetState(hfdcan) != HAL_FDCAN_STATE_RESET) {
        HAL_FDCAN_Stop(hfdcan);
    }
    HAL_FDCAN_DeInit(hfdcan);

    // 2. Set Instance and Timings
    if (ch_idx == 0) hfdcan->Instance = FDCAN2;
    else             hfdcan->Instance = FDCAN3;

    hfdcan->Init.NominalPrescaler = timing->prescaler;
    hfdcan->Init.NominalTimeSeg1 = timing->time_seg1;
    hfdcan->Init.NominalTimeSeg2 = timing->time_seg2;
    hfdcan->Init.NominalSyncJumpWidth = timing->sjw;

    // Standard Config (Adjust if you use specific Filters/Modes)
    hfdcan->Init.ClockDivider = FDCAN_CLOCK_DIV1;
    hfdcan->Init.FrameFormat = FDCAN_FRAME_CLASSIC; // Change to FDCAN_FRAME_FD_BRS if needed
    hfdcan->Init.Mode = FDCAN_MODE_NORMAL;
    hfdcan->Init.AutoRetransmission = ENABLE;
    hfdcan->Init.TransmitPause = DISABLE;
    hfdcan->Init.ProtocolException = DISABLE;
    hfdcan->Init.TxFifoQueueMode = FDCAN_TX_FIFO_OPERATION;

    // 3. Re-Init
    if (HAL_FDCAN_Init(hfdcan) != HAL_OK) return 0;

    // 4. Configure Filters (If needed, add here, otherwise generic open filter)
    // Example: Allow all
    // FDCAN_FilterTypeDef sFilterConfig;
    // sFilterConfig.IdType = FDCAN_STANDARD_ID;
    // sFilterConfig.FilterIndex = 0;
    // sFilterConfig.FilterType = FDCAN_FILTER_MASK;
    // sFilterConfig.FilterConfig = FDCAN_FILTER_TO_RXFIFO0;
    // sFilterConfig.FilterID1 = 0;
    // sFilterConfig.FilterID2 = 0;
    // HAL_FDCAN_ConfigFilter(hfdcan, &sFilterConfig);

    // 5. Start
    if (HAL_FDCAN_Start(hfdcan) != HAL_OK) return 0;

    // 6. Activate Interrupts (Important for your sniffer!)
    HAL_FDCAN_ActivateNotification(hfdcan, FDCAN_IT_RX_FIFO0_NEW_MESSAGE, 0);

    // Update State
    if (ch_idx == 0) current_baud_ch0 = baud_cmd;
    else             current_baud_ch1 = baud_cmd;

    return 1;
}

uint32_t CAN_Get_Baudrate(uint8_t ch_idx) {
    uint8_t cmd = (ch_idx == 0) ? current_baud_ch0 : current_baud_ch1;
    const CAN_Timing_t *t = get_timing_by_cmd(cmd);
    return (t) ? t->speed_bps : 500000;
}
