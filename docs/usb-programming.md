# USB programming

1. Short the two bare `J_BOOT` pads to hold flash chip-select low through `R_BOOT` (1 kΩ).
2. While holding the short, connect the computer to **J_DATA** from a fully unpowered board, or momentarily pull `J_DEBUG.RUN` to GND to reset the powered MCU.
3. Release `J_BOOT` after the ROM enters USB boot mode.
4. Copy a firmware UF2 built for this RP2040 board to the ROM's `RPI-RP2` drive, or use `picotool`.

Source: [RP2040 datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf), boot sequence and USB boot documentation. The QSPI flash, 12 MHz crystal, USB 27 Ω series resistors and required rails are present. There is no fitted BOOT button; use the exposed pads. SWD and RUN remain available on `J_DEBUG`.

The **PD port is motor power only**, requesting 15 V. Programming uses the separate **Data USB-C port**. USB ROM entry connections and physical copper continuity have been checked in CAD. Enumeration, boot-ROM PHY operation at the chosen supply, and actual flashing must still be tested on an assembled prototype. No motor-control firmware has been implemented or preloaded. Keep the motor disconnected during the first flashing/rail checks.
