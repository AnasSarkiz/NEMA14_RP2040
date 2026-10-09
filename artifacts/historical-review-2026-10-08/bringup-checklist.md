# First prototype bring-up — RP2040

**Status: NOT EXECUTED.** This is a measurement plan, not a test report. Motor-control firmware is absent. Record PCB source revision, fabrication/assembly lot, motor revision, test firmware commit, instrument models, probes, temperature, cable/source identities and every measured result. Leave acceptance fields unpassed until measured.

Required equipment: DMM, protected USB/data breakout or USB power meter, current-limited bench supply, a PD source advertising 15 V, oscilloscope with short ground spring, preferably differential/current probes, thermocouples, and the specified 14HM11-0404S. Use a fused/protected breakout when injecting bench power; do not assume a bench supply negotiates USB PD.

## 1. Unpowered assembly inspection

- [ ] Verify exact fitted MPNs against the cleaned assembly BOM; check pin 1, flash/driver/MCU exposed pads, TVS/Schottky/capacitor polarity and USB orientation using assembly drawings.
- [ ] Verify both USB-C mouths face outward at the same +Y edge: PD at X−5.3 mm and DATA at X+5.3 mm. Select compact overmolds ≤10 mm wide; insert both actual plugs simultaneously and verify retention, screw/carrier clearance and cable bend access. Record cable MPNs and measured overmold dimensions; the 10.6 mm pitch is a clearance-screening constraint, not proof of fit.
- [ ] Inspect the eight USB shield slots and manual/approved shield solder joints. Confirm bare J_MOTOR/J_DEBUG/J_BOOT are unpopulated interfaces, not placement omissions.
- [ ] Inspect ordinary vias versus thermal-pad vias, solder wicking/bridges, and all QFN joints (X-ray where appropriate).
- [ ] With cables and motor disconnected, measure PD_VBUS, DATA_VBUS, LOGIC_IN, V3V3 and V1V1 resistance to GND. Capacitor charging is expected; investigate sustained near-zero resistance. Record readings rather than using a universal minimum-ohms rule.
- [ ] Confirm motor winding pairs and insulation from casing. Do not perform the drawing’s 500 VAC dielectric test using improvised equipment.
- [ ] Verify adapter, insulating spacers, mounting screws and wire/USB access against the actual motor; do not mount the PCB directly to unqualified rear screw features.

## 2. Logic-only power and safe states

- [ ] Keep the motor and PD cable disconnected. Apply 5 V through a protected DATA VBUS breakout with an initial 100 mA limit; stop on sustained limiting or unexpected heating and investigate before increasing it. Record inrush and steady current.
- [ ] Measure DATA_VBUS, voltage after D_DATA, AP63203 VIN/EN, V3V3 and V1V1. Record minimum rail voltage and ripple during startup, reset and boot.
- [ ] V3V3 target is approximately 3.30 V; AP63203 manufacturer CCM tolerance is 3.27–3.33 V, while light-load ripple/PFM behavior needs measurement. RP2040 USB_VDD must stay within 3.135–3.63 V and all 3.3 V devices within their own ranges.
- [ ] V1V1 target is 1.10 V, internal-regulator ±3% specification under applicable conditions; RP2040 core operating supply limits are 0.99–1.21 V. Verify both DVDD pads receive the rail.
- [ ] Hold RUN low and power cycle. Confirm ENABLE_N high and SLEEP low before firmware, while reset is held, and during supply removal. Verify outputs remain disabled; correct the hardware if these defaults fail.
- [ ] Scope RUN, the 12 MHz crystal (use a low-capacitance probe or buffered clock output), buck SW/BST differential and rails. Do not load the crystal enough to create a false failure.

## 3. USB programming and recovery

- [ ] Short J_BOOT BOOT-to-GND while releasing RUN/reset or applying DATA-only power. Confirm RP2040 ROM enumerates as **RPI-RP2**; remove the temporary boot short afterward.
- [ ] Flash a minimal USB test UF2 built for 2 MB GD25Q16EEIGR, using a flash boot stage compatible with that exact device (generic 03h SPI is a conservative starting point). Verify QE/status configuration before using quad-mode XIP.
- [ ] Reset and confirm firmware boot, USB enumeration, and a repeatable command response. Corrupt/erase application flash intentionally only on a recovery test unit, then prove BOOTSEL recovery works.
- [ ] Repeat with both Type-C orientations, intended cable lengths, direct host and intended hub. Capture USB errors and host logs; perform at least 20 cold-start/enumeration cycles per intended power configuration as an engineering target.
- [ ] Verify firmware obeys host power limits and asserts the USB pull-up only when DATA_PRESENT indicates host VBUS (DATA_PRESENT is active LOW). Measure DATA-only current before and after configuration; current limits are not established solely by the buck’s output rating.

## 4. PD negotiation and power combinations

- [ ] Motor remains disconnected. Connect a source advertising 15 V. Record the actual requested/granted PDO, VBUS waveform and PG polarity; verify PG low means the requested voltage is valid.
- [ ] Test a source lacking 15 V. Verify fallback voltage and that driver enable stays disabled. Do not intentionally force 20 V as a functional operating test.
- [ ] Test DATA-only, PD-only, both cables, each attach order, and removal of each cable. Capture LOGIC_IN/V3V3/V1V1 droop, resets and boot behavior.
- [ ] Measure host VBUS through a breakout when only PD is attached. Confirm 15 V cannot reach DATA_VBUS. Record diode leakage, unloaded and loaded values; a DMM reading alone does not quantify fault behavior.
- [ ] Keep VM_ENABLE_N high impedance/HIGH in ROM/reset; assert LOW on GPIO27 only after stable V3V3, then wait at least 0.5 ms. Calibrate VM_SENSE using the switched 100 kΩ/(10 kΩ || 10 kΩ) factor of 21. Allow ADC/filter settling and compare at 5 V, 9 V and 15 V bus values. Confirm DATA_PRESENT thresholds independently.
- [ ] Scope PD hot-plug and cable removal. An initial conservative abort/review threshold is any VM overshoot reaching 18 V; exact selected TVS clamp/energy behavior is still unverified. This threshold is a test target, not a measured clamp rating.

## 5. Motor-current verification

- [ ] Only connect/disconnect the motor while all power is removed. Solder black=A+, green=A−, red=B+, blue=B− and provide strain relief.
- [ ] Firmware initializes STEP/DIR and holds ENABLE_N high/SLEEP low; release SLEEP, wait at least 2 ms, and enable only after PG plus measured VM validate the intended 15 V supply.
- [ ] Use a current probe or differential sense-voltage measurement with short connections. Record current through both phases across the full microstep table and both directions. Do not infer chopped phase current from a USB input meter or ordinary DMM alone.
- [ ] Measure VREF, each sense voltage and sense-ground offset relative to the driver star ground. Nominal peak is approximately 0.3508 A, but manufacturer low-VREF regulation accuracy is unspecified. **Acceptance requires phase current below 0.40 A with measurement uncertainty and transient peaks considered.** If any unit fails, stop and revise the reference setting; do not hide a hardware overcurrent behind a software label.
- [ ] Start unloaded at 5 rpm, ramp 20 rpm/s to a 30 rpm initial ceiling. Record STEP timing, tracking/missed steps, winding-current shape, current decay and supply current before increasing load or speed.

## 6. Load, regeneration and thermal qualification

- [ ] Exercise holding, forward/reverse, acceleration/deceleration, controlled emergency disable and a brief stalled condition. Capture VM overshoot and phase-current peaks in each case.
- [ ] Begin with short runs; then soak until measured temperatures stabilize. Measure motor casing, driver, regulator, inductor, sense resistors, bulk capacitor and MCU near the actual rear assembly.
- [ ] Verify local ambient and inferred junction temperatures against exact manufacturer limits. Driver thermal shutdown is not an acceptable operating target. An initial case-temperature review trigger of 80 °C is a conservative prototype target, not a junction-temperature qualification.
- [ ] Repeat at the intended ambient up to the motor’s 50 °C rating, realistic load inertia and enclosure/cable configuration. Motor heat conducted through the carrier must be included.
- [ ] Measure buck rail ripple and load-step response; compare exact inductor saturation/RMS and capacitor effective-capacitance data once obtained. A no-reset run does not alone establish regulator stability or component lifetime.
- [ ] Recheck USB stability during motor activity, cable reconnect, stalls and resets. Confirm brownout/reset returns the driver to disabled/sleep state.

## Acceptance record

| Gate | Result / evidence | Current status |
| --- | --- | --- |
| Assembly/orientation | Photographs, inspection/X-ray, BOM/CPL reconciliation | Not executed |
| Rails/startup | Scope captures and current readings | Not executed |
| USB flashing/recovery | UF2, firmware commit, host logs and orientation tests | Not executed |
| 15 V PD/fallback/backfeed | PDO log and power-combination captures | Not executed |
| Both phase currents | Calibrated current/sense captures over all microsteps | Not executed |
| Regeneration/thermal | Load/inertia, soak log, VM and temperature captures | Not executed |
| Rear adapter fit/isolation | Motor revision, measured clearances, assembly photographs | Not executed |

Release requires these physical results plus resolved exact TVS, inductor, capacitor and assembly evidence. Passing CAD/DRC/short checks cannot substitute for this checklist.

## Additional unresolved sequencing acceptance gate

- [ ] Qualify the implemented NPN/CBTLV partial-power correction in `engineering-review.md`. Capture simultaneous rail and DATA_PRESENT/VM_SENSE voltages during cable attach/removal and all power orders, evaluate Vpin−VDD, ghost power and source currents against guaranteed limits. Verify OE is HIGH through reset, switched output capacitance discharges safely on rail collapse, NPN unpowered collector remains within limits, and Ioff/bleed bounds apply. See `artifacts/validation/power-sequencing-correction.json`.

- [ ] **ROM/pull-up ghost-VBUS test:** with PD power and no powered DATA host, exercise reset/ROM USB and deliberately enable the USB pull-up in test firmware. Measure DATA_VBUS and DATA_PRESENT before attaching any host. Rail-steering ESD diodes may raise the otherwise unpowered DATA rail from D+/D−; determine whether this falsely asserts the active-low NPN detector. Then connect a protected host breakout at 0 V and measure injection/backfeed. Qualify exact ESD topology and thresholds; if false detection or disallowed current occurs, revise hardware VBUS detection/isolation rather than accepting a firmware-only claim.
