# RP2040 firmware contract

Use the Pico SDK RP2040 target with 12 MHz XOSC and 2 MB flash. Select the generic JEDEC-compatible boot stage for GD25Q16E; do not assume a Winbond-specific quad-enable sequence. Flash boot and UF2 USB ROM boot require hardware validation.

| Function | RP2040 GPIO / physical pin |
| --- | --- |
| STEP | GPIO6 / 8 |
| DIR | GPIO7 / 9 |
| ENABLE_N | GPIO8 / 11 |
| SLEEP | GPIO9 / 12 |
| PD_GOOD (active low) | GPIO10 / 13 |
| VM_SENSE | ADC2 / GPIO28 / 40 |
| DATA_PRESENT | ADC3 / GPIO29 / 41 |
| SWCLK / SWDIO | 24 / 25 |
| RUN | 26 |
| USB DM / DP | 46 / 47, through 27 Ω resistors |

On reset, pull-ups/pull-downs disable the A4988. Initialize outputs disabled; require PG and measured VM within an accepted 15 V window, then wake the driver and respect its timing before enabling. Monitor supply loss and shut down immediately. Keep USB pull-up disconnected without DATA_PRESENT. Start with low speed; the 24 mH motor inductance and actual torque/load set speed limits.

Full steps: 400/revolution. Configured 1/16 microsteps: 6400/revolution. No USB protocol/application firmware is implemented.

J_DEBUG bottom-to-top in the top PCB view: 3V3, GND, SWCLK, SWDIO, RUN. J_BOOT shorts flash CS to GND through 1 kΩ: hold short while asserting/releasing RUN to enter ROM USB boot. Never leave the short during ordinary flash operation.
