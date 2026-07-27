/**
 * @file pin_scope.h
 * @brief PinScope v1.0 - STM32 通用引脚调试与串口收发模块
 * 
 * 使用说明：
 * 1. 将 pin_scope.h 与 pin_scope.c 加入您的 STM32 工程。
 * 2. 在 main.c 的 /* USER CODE BEGIN Includes */ 中引入：
 *    #include "pin_scope.h"
 * 3. 在 main() 函数的 /* USER CODE BEGIN 2 */ 中调用初始化：
 *    PinScope_Init();
 * 4. 在 while(1) 循环的 /* USER CODE BEGIN WHILE */ 中调用轮询：
 *    PinScope_Update();
 *    (或在 SysTick 定时中断中调用)
 */

#ifndef __PIN_SCOPE_H
#define __PIN_SCOPE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化 PinScope 串口(USART1, 115200bps, PA9-TX, PA10-RX)及相关端口
 */
void PinScope_Init(void);

/**
 * @brief 扫描并检测 GPIOA / GPIOB 引脚的电平跳变，有变化则通过串口自动上报 "PAx: 1" 或 "PAx: 0"
 */
void PinScope_Update(void);

/**
 * @brief 串口接收字符处理函数 (供 USART1_IRQHandler 调用)
 * @param c 接收到的单个字符
 */
void PinScope_OnRxByte(char c);

#ifdef __cplusplus
}
#endif

#endif /* __PIN_SCOPE_H */
