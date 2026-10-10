# Fitted diagnostics — prototype revision

Added a single green status LED, local temperature telemetry and an audible alarm. All parts use JLCPCB-imported footprints and STEP models; all fitted components stay on top. The motor header, two same-edge USB ports, mounting-hole pattern and 35 × 35 mm board target are retained. This feature requires firmware; no diagnostic firmware or hardware measurements are supplied by the PCB build.

| Reference | Exact part / JLCPCB | Purpose |
|---|---|---|
| D_STATUS | Everlight 19-217/GHC-YR1S2/3T / C72043 | Green LED; cathode at STATUS_N, anode fed through 1kΩ R_LED from 3V3. Low turns it on. |
| U_TEMP | TI TMP102AIDRLR / C99269 | SOT563 temperature sensor, address 0x48 with ADD0 grounded; 100nF C_TEMP. |
| R_TEMP_SCL / SDA / ALERT | 5.1kΩ / 5.1kΩ / 10kΩ | I2C and open-drain ALERT pull-ups to 3V3. |
| BZ_ALARM | Huaneng MLT-5020 / C94598 | Externally driven magnetic sounder; pin 1 positive, pin 2 negative, pin 3 NC. Primary drawing gives 5.0 ±0.3 mm body and 2.0 ±0.2 mm height; imported model nominal 5.2 ×5.2 ×2.01 mm fits these bounds. |
| Q_BUZZER | AOS AO3400A / C20917 | Logic-level low-side MOSFET: pin 1 gate, 2 source/GND, 3 drain/BUZZER_SINK. |
| D_BUZZER | 1N5819WS / C191023 | Coil flyback; cathode at 3V3, anode at BUZZER_SINK. |
| R_BUZZER_GATE / PD, C_BUZZER | 100Ω / 100kΩ, 22µF/25V C45783 | Gate series resistance, default-off pull-down, local supply bypass. |

D_PD and D_DATA also use exact 1N5819WS/C191023 to reduce their supplier courtyard and preserve 40V/1A rating. Primary PDF specifies VF ≤0.60V at1A, 0.5mA reverse leakage at25°C/40V and10mA at100°C/40V. Crossfeed is blocked in the diode sense, not galvanically isolated; measure hot reverse leakage and DATA-only dropout. Its 80°C/W thermal value is typical and not a mounted-board guarantee.

## Physical MCU pins

| Net | MCU pin | Firmware role |
|---|---|---|
| TEMP_SDA | GPIO16 / pad 27 | I2C0 SDA |
| TEMP_SCL | GPIO1 / pad 3 | I2C0 SCL |
| BUZZER_PWM | GPIO2 / pad 4 | PWM |
| STATUS_N | GPIO3 / pad 5 | active-low output |
| TEMP_ALERT_N | GPIO4 / pad 6 | input, active low |

CH32 uses software open-drain I2C at100kHz because the manufacturer's silicon-lot note does not guarantee hardware I2C on every CH32X035 lot. Do not enable USB/debug-remapping functions that conflict with the reviewed physical pins. RP2040 uses I2C0 at100kHz on GPIO16 SDA and GPIO1 SCL (both select I2C0); qualify rise time/noise and TMP102 transactions on the actual harness-mounted board.

## Reset and alarm behavior

At reset the MCU pins are inputs. The100kΩ gate pull-down holds the buzzer off; firmware must preload PWM low before configuring the output. STATUS_N input/high means off. Keep STEP low, ENABLE_N high and SLEEP low until PD-good, bus voltage and logic are valid.

Drive only4kHz,50% PWM, ≤100ms per burst, ≤1burst/second, with a valid15V PD contract. Disable the buzzer before or immediately on PD loss and throughout DATA-only USB operation. Never leave the coil continuously energized. Before USB enumeration, measured DATA input must stay≤100mA; afterwards also stay≤100mA, including PD loss during an alarm. No external3V3 load is supported.

Read TMP102, check communication/range errors and log its local PCB temperature. ALERT is an input to firmware; it does not independently gate A4988. Sensor placement and thermal lag do not establish winding, motor-case or driver-junction temperature. Proposed warning/trip thresholds require correlation and soak tests; do not claim a qualified thermal protection system.

The MLT-5020 manufacturer rates3.0Vo-p (unipolar zero-to-peak), operating2–4Vo-p,4kHz,50% duty,100mA maximum under that test and12Ω±3Ω winding resistance. Screening3.6V/9Ω gives400mA possible pulse; adding100mA logic allowance plus LED/I2C loads fits the proposed550mA peak/310mA average3V3 acceptance ceilings. This deliberately conservative DC screen does not predict the actual inductive waveform or sound pressure. Scope the coil, flyback drain, rail droop and input current at the permitted temperatures before accepting the envelope.

## Required prototype checks

- Verify physical GPIO pins, LED current/polarity/visibility and default states during reset, flashing and brownout.
- Validate TMP102 identity/address, conversion and alert configuration, I2C edges, accuracy against a calibrated reference and mounted thermal correlation.
- Measure PWM frequency/duty, sounder current and sound pressure, MOSFET/diode/coil temperatures and drain overshoot. Keep 3V3 between3.0 and3.6V in every accepted state.
- Test PD/data insertion/removal and power handover with alarms active; no unintended coil or motor drive is accepted.
- Both variants now use AP63203, exact Bourns4.7µH and reviewed biased-capacitor bank. Qualify startup/fault saturation, converter stability, ripple, hot dropout and all existing motor/USB/regeneration tests.

Primary evidence is retained under `references/`: TMP102-TI-primary.pdf, AO3400A-AOS-primary.pdf, MLT-5020-Huaneng-primary.pdf, C191023-primary.pdf and C72043-primary.pdf. The component import/catalog files retain supplier identities and geometry. Catalog sounder-height text disagrees with the manufacturer's drawing; the drawing is authoritative, and no custom footprint/model is substituted.

The six native DRC warnings concern generic power/ground semantics for the two transistors and switched sounder, plus AO3400A pin metadata. Their actual physical pin-to-net connections are separately asserted in scripts/check.ts; the warnings are retained. Supplier pickup centers and machine rotations remain pending assembler preview. No warning is hidden and no powered coil is modeled as a direct ground connection.
