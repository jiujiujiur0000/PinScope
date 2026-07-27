/**
 * @file pin_scope.c
 * @brief PinScope v1.0 - STM32 通用引脚调试与串口收发模块实现 (SysTick 零循环自动采样)
 */

#include "pin_scope.h"
#include <stdio.h>
#include <string.h>

#if defined(STM32F10X_HD) || defined(STM32F10X_MD) || defined(STM32F10X_LD)
    #include "stm32f10x.h"
#else
    #include "stm32f10x.h"
#endif

static uint16_t last_port_a = 0xFFFF;
static uint16_t last_port_b = 0xFFFF;

static char rx_buffer[64];
static uint8_t rx_index = 0;

/* 私有函数：解析并执行上位机 PinScope 发来的串口命令 */
static void PinScope_ProcessCommand(const char *cmd)
{
    /* 格式 0: PING 握手响应 */
    if (strncmp(cmd, "PING", 4) == 0)
    {
        printf("PONG\r\n");
    }
    /* 格式 1: PULSE:PA0 或 PULSE:PB3 */
    else if (strncmp(cmd, "PULSE:", 6) == 0)
    {
        char port = cmd[6]; // 'A' 或 'B'
        int num = 0;
        if (sscanf(&cmd[7], "%d", &num) == 1 && num >= 0 && num <= 15)
        {
            GPIO_TypeDef* GPIOx = (port == 'A' || port == 'a') ? GPIOA : GPIOB;
            uint16_t pin = (1 << num);
            
            /* 拉高 */
            GPIO_SetBits(GPIOx, pin);
            
            /* 简易延时 (约 300ms) */
            for (volatile uint32_t i = 0; i < 720000; i++);
            
            /* 拉低 */
            GPIO_ResetBits(GPIOx, pin);
        }
    }
    /* 格式 2: SET:PA0:1 或 SET:PB2:0 */
    else if (strncmp(cmd, "SET:", 4) == 0)
    {
        char port = cmd[4];
        int num = 0, val = 0;
        if (sscanf(&cmd[5], "%d:%d", &num, &val) == 2 && num >= 0 && num <= 15)
        {
            GPIO_TypeDef* GPIOx = (port == 'A' || port == 'a') ? GPIOA : GPIOB;
            uint16_t pin = (1 << num);
            if (val) {
                GPIO_SetBits(GPIOx, pin);
            } else {
                GPIO_ResetBits(GPIOx, pin);
            }
        }
    }
}

void PinScope_Init(void)
{
    /* 使能 GPIOA, GPIOB 与 USART1 时钟 */
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB | RCC_APB2Periph_USART1, ENABLE);

    /* 配置 USART1 TX (PA9) */
    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    /* 配置 USART1 RX (PA10) */
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    /* 配置 USART1 参数: 115200, 8N1 */
    USART_InitTypeDef USART_InitStructure;
    USART_InitStructure.USART_BaudRate = 115200;
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;
    USART_InitStructure.USART_StopBits = USART_StopBits_1;
    USART_InitStructure.USART_Parity = USART_Parity_No;
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART1, &USART_InitStructure);

    /* 开启接收中断 */
    USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
    USART_Cmd(USART1, ENABLE);

    /* 使能 NVIC 串口中断 */
    NVIC_InitTypeDef NVIC_InitStructure;
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);

    /* 配置 SysTick 系统滴答中断 (每 10ms 触发一次自动采样，主循环 0 负担) */
    SysTick_Config(SystemCoreClock / 100);
}

void PinScope_Update(void)
{
    uint16_t curr_a = GPIO_ReadInputData(GPIOA);
    uint16_t curr_b = GPIO_ReadInputData(GPIOB);

    /* 比对 GPIOA 变化 */
    if (curr_a != last_port_a)
    {
        for (int i = 0; i < 16; i++)
        {
            uint8_t old_b = (last_port_a >> i) & 1;
            uint8_t new_b = (curr_a >> i) & 1;
            if (old_b != new_b)
            {
                printf("PA%d: %d\r\n", i, new_b);
            }
        }
        last_port_a = curr_a;
    }

    /* 比对 GPIOB 变化 */
    if (curr_b != last_port_b)
    {
        for (int i = 0; i < 16; i++)
        {
            uint8_t old_b = (last_port_b >> i) & 1;
            uint8_t new_b = (curr_b >> i) & 1;
            if (old_b != new_b)
            {
                printf("PB%d: %d\r\n", i, new_b);
            }
        }
        last_port_b = curr_b;
    }
}

void PinScope_OnRxByte(char c)
{
    if (c == '\r' || c == '\n')
    {
        if (rx_index > 0)
        {
            rx_buffer[rx_index] = '\0';
            PinScope_ProcessCommand(rx_buffer);
            rx_index = 0;
        }
    }
    else
    {
        if (rx_index < sizeof(rx_buffer) - 1)
        {
            rx_buffer[rx_index++] = c;
        }
    }
}

/* USART1 中断入口 */
void USART1_IRQHandler(void)
{
    if (USART_GetITStatus(USART1, USART_IT_RXNE) != RESET)
    {
        char c = (char)USART_ReceiveData(USART1);
        PinScope_OnRxByte(c);
        USART_ClearITPendingBit(USART1, USART_IT_RXNE);
    }
}

/* SysTick 系统滴答中断入口：自动在后台扫描引脚，无需在 while(1) 中调用 */
void SysTick_Handler(void)
{
    PinScope_Update();
}
