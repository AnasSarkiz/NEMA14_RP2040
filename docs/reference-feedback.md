# Reference feedback and electrical review — v1.5.0

The original delivered board had no fitted power/debug LED, RGB status LED, temperature sensor or buzzer. This revision adds all four using the live [Rishabh reference](https://tscircuit.com/imrishabh18/rp2040-motor-controller) release `e8d285f7-c3d8-46f5-9a54-344fdde0124e`. Reference section sources and release metadata are retained under `references/reference-feedback/`. Existing connected physical pins and passive values are compared with the frozen Git baseline in `artifacts/reference-feedback/preserved-electrical-interfaces.json`.

## Fitted circuits

- Power/debug LED: XL-1608SURC-06 C965799, 330 ohm C25104 from 3.3 V. This indicates power; software status is provided by the RGB LED.
- RGB status LED: LTST-C19HE1WT C458749, common anode on fixed programming USB 5 V (DATA_VBUS), three 1 kohm resistors and DTC114EU3HZGT106 C509876 digital NPN sinks. RGB requires the programming USB supply; PD-only power does not light this LED, matching the reference connection.
- Temperature: TMP102AIDRLR C99269, ADD0 grounded (7-bit address 0x48), 100 nF bypass, 4.7 kohm SDA/SCL pull-ups to 3.3 V. ALERT is unconnected as in the reference. Firmware must poll temperature and implement alarm/shutdown behavior. This sensor measures its PCB location; motor winding temperature is not measured.
- Buzzer: HYG-8503A C7544813 externally driven magnetic transducer, 3.3 V positive terminal, AO3400A C20917 low-side switch, 100 ohm gate resistor, 100 kohm reset-off pull-down and 10 uF local bypass. PWM firmware is required. The reference's PMEG6020ELRX C478000 (60 V / 2 A) power diode is reused as the flyback diode in place of B5819W_SL C8598: cathode to 3.3 V, anode to the switched negative terminal. This preserves the reference drive topology with a native smaller land pattern; the components are not all byte-identical to the reference.

AP63203WU-7 buck remains the 3.3 V supply.

## Firmware assignment

| Function | MCU assignment |
| --- | --- |
| RGB red | GPIO25 / pin 37 |
| RGB green | GPIO2 / pin 4 |
| RGB blue | GPIO3 / pin 5 |
| Buzzer PWM | GPIO16 / pin 27 |
| Temperature SDA | I2C1 GPIO26 / pin 38 |
| Temperature SCL | I2C1 GPIO27 / pin 39 |

CH32 PB6/PB7 are GPIOs, not a CH32X035 hardware I2C alternate-function pair. Software I2C preserves the existing USB and WCH debug pins. RGB channel firmware must use GPIO/software PWM as appropriate. RP2040 assignments match the reference. Neither repository includes qualified firmware for these accessories, and the reference firmware is not a drop-in replacement for this A4988 controller.

## External connection standard

The programming USB-C duplicates D+ and D− receptacle contacts onto USB_DP and USB_DM, presents separate 5.1 kohm CC sink resistors, connects its VBUS contacts to fixed DATA_VBUS, grounds shell/GND contacts and leaves SBU unconnected. The PD USB-C sends CC1/CC2 to CH224K, supplies negotiated PD_VBUS and leaves USB data/SBU contacts unconnected. Never apply negotiated PD voltage to DATA_VBUS or the RGB anode.

The fitted B4B-PH-K-S(LF)(SN) C131334 JST PH top-entry motor header uses physical pins **1 A+, 2 A−, 3 B+, 4 B−**, matching the reference's external coil order. Positive coil paths in the reference additionally pass through current-sense circuitry; this board retains its A4988 outputs and current setting. Confirm the cable pin order from the manufacturer pin-1 view before connecting a motor.

## Evidence and limits

`circuit-verification.json` checks 92 physical connector/accessory/MCU pins, actual MPNs/values and byte-verified native footprints, courtyards, OBJ and STEP models. `every-trace-review.csv` inventories every delivered trace; its JSON adds every segment and via net. Native DRC, independent physical connectivity, width/current screening, real Gerber copper/drill comparison and native STEP mechanical checks are separate required evidence.

The outline remains exactly 35 × 35 mm. Four NPTH mounts remain exactly (±13, ±13), diameter 3.2 mm. Both USB mouths remain flush on +Y at x = ±6.2 mm, with two 12 mm plug envelopes and only 0.4 mm between them. Maximum screw head diameter is 4 mm (DIN 920); the mechanical screen uses a 4.4 mm conservative envelope. Normal 5.4 mm M3 heads do not meet the layout constraint. The native top-entry JST and cable insertion space remain fitted and checked.

Static source agreement and a working reference do not establish that the assembled hardware works. USB signal integrity, regulator stability, buzzer supply transients/noise, RGB operation, temperature accuracy, phase current, PD negotiation, physical cables/threads and rear motor/adapter geometry require hardware verification. No rear-motor compatibility claim is made. Complete assembly CAM/stencil/silkscreen and pickup-angle qualification remains required before fabrication approval; see the actual current validation/CAM receipts.

RP2040 assembly: C_DV50, C_IO49, R_XOUT, C_XOUT and R_TEMP_SDA use their unchanged native supplier footprints on the bottom. The five bare debug test pads are also on the bottom; probe them before motor installation or with the PCB removed. The fixed USB-C and JST connectors remain on top. Bottom components require two-sided assembly and a verified underside gap; rear-motor fit remains unverified.

Inner1 carries the individually inventoried local signal and supply escapes, limited to 15 mm. The two blue LED feedback paths are separately reviewed low-frequency, low-current exceptions: LED_B is 15.858 mm with a conservative 1 mA budget; STATUS_B_K is 20.627 mm with a 6 mA budget covering 5.5 V / 0.99 kohm including tolerance. Their route bound is 25 mm. They do not carry USB, flash-clock, motor or bulk supply current. The ground pours are refilled around them, and ground continuity, actual CAM copper clearance and the remaining ground-plane area must pass again before prototype publication.
