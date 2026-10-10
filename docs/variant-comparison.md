# NEMA14 diagnostic variants

Both preserve the motor/harness, 35 mm outline, same-edge two USB-C ports, inside-board JST and top assembly. Exact per-board files/hashes are in each engineering manifest.

| Feature | CH32X035G8U6 | RP2040 |
|---|---|---|
| MCU | CH32X035G8U6 | RP2040, external flash/crystal |
| Fitted parts |59 |79 |
| Copper |4 layers; upgraded from2 for diagnostics |4 layers retained |
| Logic converter |AP63203WU-7, SRN4018-4R7M, exact biased-capacitor review |Same |
| Added status |Green Everlight LED,1kΩ resistor |Same |
| Temperature |TMP102AIDRLR,0x48; software I2C PA5/PA6; ALERT PB1 |Same sensor; I2C0 GPIO1/16; ALERT GPIO4 |
| Buzzer |MLT-5020, AO3400A driver, flyback/default-off/bypass; PA7 TIM3CH2 |Same sounder circuit; GPIO2 PWM |
| Status GPIO |PB0 active low |GPIO3 active low |
| Schematic |4 functional A4 pages |5 functional A4 pages |
| Main motor/15V routing |≥0.45mm outer layers; native escapes individually bounded; phase vias remain |Same |
| Programming hardware |USB ROM boot path and WCH debug |USB ROM BOOTSEL and SWD |
| Firmware/physical hardware qualification |Not implemented/not tested |Same |

PD baseline 3V3 allowance 100 mA; pulse 550 mA / average 310 mA qualification ceilings, no external loads. DATA-only3V3 target 75 mA, measured USB DATA input≤100mA in every state, including loss of PD during an alarm. Buzzer only with valid 15 V PD, 4 kHz / 50% carrier,≤100ms bursts at≤1Hz. These are proposed requirements, not measured ratings. TMP102 reports local PCB temperature, not winding temperature; software alarms are not an independent thermal safety system.

Both use15V PD, accepted measured phase peaks≤0.25A, room0–40°C/local air≤45°C/motor case≤60°C, stop energy≤0.10mJ at≤1Hz and no continuous back-driving. Supply18V measured operating ceiling and all transient tests apply. Motor/cable installation reservation≈49.204×157.480×102.771mm precedes tolerances and service access. Front M3 motor threads only; rear end-cap screws untouched.

Both need supplier-approved TypeVII filled/copper-capped exposed-pad vias and listed TypeVI close off-pad barrels. Ordinary drill counts/coordinates, mask/paste and pickup datums are in current fabrication CSVs. Pickup conventions, crimp/splice/material certificates, physical fit, current, USB/PD, power transitions, regeneration, mounted temperatures and the new sensor/sounder behavior remain unqualified. Old DC return/thermal receipts describe earlier copper and are historical. No production readiness is claimed.
