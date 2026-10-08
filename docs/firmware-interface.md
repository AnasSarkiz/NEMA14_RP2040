# RP2040 firmware contract

No motor-control firmware is implemented. Use the Pico SDK RP2040 target with 12 MHz XOSC and 2 MB GD25Q16EEIGR flash. A generic 03h SPI boot stage is a conservative starting point; verify exact QE/status behavior before quad XIP. ROM USB boot and flashed firmware require physical validation.

| Function | GPIO / physical pin | Polarity or operation |
| --- | --- | --- |
| STEP | GPIO6 / 8 | ≥1 µs high/low; initial target 5 µs |
| DIR | GPIO7 / 9 | ≥200 ns setup/hold; initial target 5 µs |
| ENABLE_N | GPIO8 / 11 | HIGH disables |
| SLEEP | GPIO9 / 12 | LOW sleeps; wait≥2 ms after release initially |
| PD_GOOD | GPIO10 / 13 | Active LOW |
| VM_ENABLE_N | GPIO27 / 39 | HIGH/high impedance isolates; LOW enables VM switch |
| VM_SENSE | ADC2 /GPIO28 / 40 | Switched bus sense, conversion×21 |
| DATA_PRESENT | GPIO29 / 41 | Digital, active LOW from NPN collector |
| SWCLK /SWDIO | 24 / 25 | Debug interface |
| RUN | 26 | Active-low reset |
| USB DM /DP | 46 /47 | Through 27 Ω resistors to Data USB-C |

Keep ENABLE_N HIGH and SLEEP LOW during reset/initialization. Keep VM_ENABLE_N high impedance/HIGH in ROM, reset and before logic supply validation. After stableV3V3, drive VM_ENABLE_N LOW, wait≥0.5 ms and sample/calibrate:

**VM_V=VM_SENSE_V×21**, from 100 kΩ over(10 kΩ||10 kΩ) while switchON. A disabled switch reading is not a valid motor-voltage sample. Earlier×11 and×(122/22) conversions are obsolete.

Require active-low PG plus calibrated VM within the accepted 15 V window before waking/enabling the motor. **DATA_PRESENT LOW means host attached**; keep USB device pull-up disconnected when the signal is HIGH/host absent. Confirm this detector's thresholds and polarity physically.

Release VM_ENABLE_N HIGH/high impedance before planned power-down and promptly on brownout. Verify reset defaults and output-capacitor discharge against actual rail fall; firmware cannot alone guarantee very fast unpowered-pin transients. Cable loss, timeout and brownout must return the driver to disabled/asleep, with regeneration behavior measured.

Motor full steps:400/revolution; fixed 1/16 microsteps:6400/revolution. Initial unloaded targets:5 rpm, 20 rpm/s ramp, 30 rpm ceiling. These are prototype settings, not guaranteed torque/speed limits.

J_DEBUG exposes 3V3, GND, SWCLK, SWDIO, RUN. J_BOOT pulls flash CS to GND through 1 kΩ during reset for ROM USB entry; remove the short afterward. Use [USB programming](usb-programming.md), then [bring-up acceptance](bringup-checklist.md).

## USB connector identification and cable access

Both USB-C openings face outward from the same **+Y edge**. **J_PD** is at X=−5.3 mm and supplies motor PD power; **J_DATA** is at X=+5.3 mm and connects the computer/programming interface. Firmware roles and signal pin assignments are unchanged by this placement. The 10.6 mm port-center pitch requires compact overmolds **≤10 mm wide** as a screening gate; verify both selected cables fit simultaneously and clear the carrier, screw heads and bend path before operating the prototype.
