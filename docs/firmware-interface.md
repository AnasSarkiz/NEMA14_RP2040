
# RP2040 firmware contract

No motor-control firmware is implemented. Use the Pico SDK RP2040 target with 12 MHz XOSC and 2 MB GD25Q16EEIGR flash. A generic 03h SPI boot stage is a conservative starting point; verify exact QE/status behavior before quad XIP. ROM USB boot and flashed firmware require physical validation.

| Function | GPIO / physical pin | Polarity or operation |
| --- | --- | --- |
| STEP | GPIO6 / 8 | ≥1 µs high/low; initial target 5 µs |
| DIR | GPIO7 / 9 | ≥200 ns setup/hold; initial target 5 µs |
| ENABLE_N | GPIO8 / 11 | HIGH disables |
| SLEEP | GPIO9 / 12 | LOW sleeps; wait≥2 ms after release initially |
| PD_GOOD | GPIO10 / 13 | Active LOW |
| VM_SENSE | ADC2 /GPIO28 / 40 | Passive 100 kΩ / (10 kΩ ∥ 470 Ω), scale 223.76596; calibrate ADC |
| DATA_PRESENT | GPIO29 / 41 | Digital, active LOW from NPN collector |
| SWCLK /SWDIO | 24 / 25 | Debug interface |
| RUN | 26 | Active-low reset |
| USB DM /DP | 46 /47 | Through 27 Ω resistors to Data USB-C |

Keep ENABLE_N HIGH and SLEEP LOW during reset and initialization. The VM monitor is passive; GPIO27/pad 39 is unconnected. Use the revised ADC/startup contract below. Require active-low PG plus the calibrated bus in the accepted 15 V window before waking/enabling the motor.

**DATA_PRESENT LOW means host attached**; keep the USB device pull-up disconnected when the signal is HIGH/host absent. Confirm detector thresholds and polarity physically. Cable loss, timeout and brownout must disable the driver and require a new host command before resuming. Firmware does not absorb regenerated energy.

Motor full steps:400/revolution; fixed 1/16 microsteps:6400/revolution. Initial unloaded targets:5 rpm, 20 rpm/s ramp, 30 rpm ceiling. These are prototype settings, not guaranteed torque/speed limits.

J_DEBUG exposes 3V3, GND, SWCLK, SWDIO, RUN. J_BOOT pulls flash CS to GND through 1 kΩ during reset for ROM USB entry; remove the short afterward. Use [USB programming](usb-programming.md), then [bring-up acceptance](bringup-checklist.md).

## USB connector identification and cable access

Both USB-C openings face outward from the same **+Y edge**. **J_PD** is at X=−7 mm and supplies motor PD power; **J_DATA** is at X=+7 mm and connects the computer/programming interface. The 14 mm port-center pitch is screened against Tensility 10-06137 (PD) and 10-06139 (DATA) USB-C plug bodies. Their specified maximum 12.5 mm width leaves 1.5 mm nominal separation, or 1.3 mm after ±0.1 mm placement per port. Verify simultaneous insertion, shoulder registration, screw/carrier clearance and cable bending on the assembled prototype; see `mechanical-fit.md`.

## Revised startup and ADC contract

Removed VM switch/OE; CH32 PB7/pad 18 and RP2040 GPIO27/pad 39 are unconnected. Configure VM_SENSE as analog/high impedance, no pull-up/output. Convert `VM_V = ADC_pin_V ×223.7659574468`, use adequate acquisition/settling, calibration and averaging/hysteresis; 12-bit/3.3 V bus resolution≈0.180 V/count. Never use the historical×21 conversion. The divider remains bounded below 0.160034 V at the 35 V screening corner even through instantaneous logic collapse;35 V is not an operating bus allowance.

Initialize STEP low, ENABLE_N high and SLEEP low. Require stable 3.0–3.6 V logic, valid PG-low PD contract, calibrated bus 14.25–15.75 V and an explicit host command. Release SLEEP, wait≥2 ms, then enable. Disable immediately on PG/rail/command loss and never resume after reset without a new command. Qualify acquisition thresholds against ADC resolution/error. Firmware is not regenerative overvoltage protection; preserve the operating-envelope energy/current/temperature limits. USB ROM programming and application firmware remain untested/unimplemented hardware contracts.
