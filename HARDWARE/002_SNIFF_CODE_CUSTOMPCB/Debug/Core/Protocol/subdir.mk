################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/Protocol/command.c 

OBJS += \
./Core/Protocol/command.o 

C_DEPS += \
./Core/Protocol/command.d 


# Each subdirectory must supply rules for building sources it contributes
Core/Protocol/%.o Core/Protocol/%.su Core/Protocol/%.cyclo: ../Core/Protocol/%.c Core/Protocol/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32G473xx -c -I../USB_Device/App -I"F:/SNIFFER_CODING/HARDWARE/002_SNIFF_CODE_CUSTOMPCB/Core/App" -I"F:/SNIFFER_CODING/HARDWARE/002_SNIFF_CODE_CUSTOMPCB/Core/Protocol" -I"F:/SNIFFER_CODING/HARDWARE/002_SNIFF_CODE_CUSTOMPCB/ThirdParty/FreeRTOS" -I"F:/SNIFFER_CODING/HARDWARE/002_SNIFF_CODE_CUSTOMPCB/ThirdParty/FreeRTOS/portable/GCC/ARM_CM4F" -I"F:/SNIFFER_CODING/HARDWARE/002_SNIFF_CODE_CUSTOMPCB/ThirdParty/FreeRTOS/include" -I../USB_Device/Target -I../Core/Inc -I../Drivers/STM32G4xx_HAL_Driver/Inc -I../Drivers/STM32G4xx_HAL_Driver/Inc/Legacy -I../Middlewares/ST/STM32_USB_Device_Library/Core/Inc -I../Middlewares/ST/STM32_USB_Device_Library/Class/CDC/Inc -I../Drivers/CMSIS/Device/ST/STM32G4xx/Include -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Core-2f-Protocol

clean-Core-2f-Protocol:
	-$(RM) ./Core/Protocol/command.cyclo ./Core/Protocol/command.d ./Core/Protocol/command.o ./Core/Protocol/command.su

.PHONY: clean-Core-2f-Protocol

