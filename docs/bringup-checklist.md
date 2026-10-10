# Bring-up and prototype qualification — all hardware tests unperformed

Use the proposed [supported operating envelope](supported-operating-envelope.md) and exact final source/hash. Record instruments, uncertainty, waveforms, environment, fitted part lots and pass/fail disposition. Do not mark boxes from calculations or CAM results.

- [ ] Supplier confirms actual stackup, finished drills/annuli, all TypeVI/TypeVII fill/cap/mask processes, cap flatness, plated USB slots and stencil. Reconcile automated BOM/PnP and manual motor-header scope; approve pickup/pin 1/polarity preview.
- [ ] Insertion coupon proves exact JST header fit in 0.75±0.05 mm bores; verify housing/contact compatibility, AWG/OD, crimp/splice pull strength and temperature/material certificates. Confirm front M3 mounting, thread engagement, tails/barrier/clamp/service slack and host envelope.
- [ ] With motor disconnected: continuity, winding/color mapping, insulation to metal carrier; current-limited DATA/PD supplies. Verify 3V3 and RP1V1, reset defaults, baseline 3V3 allowance≤100 mA; alarm total≤550 mA pulse/310 mA average, DATA draw≤100 mA and 3.0–3.6 V logic.
- [ ] PD analyzer confirms 15 V contract/fallback disables bridge. Demonstrate DATA USB enumeration, ROM programming and recovery/debug. Test both cable orders, insertion/removal, PD/source loss and command timeout; no unexpected steps/restart.
- [ ] Scope ADC−VDD,3V3,VM,LOGIC_IN,PG,ENABLE/SLEEP through slow/fast ramps and abrupt collapse. Bound negative/coupled ADC ringing and backfeed. Use revised ADC scale 223.76596 with calibrated thresholds.
- [ ] Measure both phase peaks across microsteps, decay, supply and mounted temperature. Acceptance≤0.25 A including uncertainty; manufacturer 0.40 A is a hard motor limit. Adjust VREF divider if required and requalify. Measure sense/ground bounce and effective copper/return resistance; no shunt compensation.
- [ ] Verify biased/temperature/endurance-conditioned buck capacitance in both variants≥4 µF input/24 µF output bank, startup/load-step/ripple/stability and inductor peak/heating. Test limited fault/startup safely; converter current limit may exceed inductor saturation screening rating.
- [ ] Validate actual returned energy including rotor, load, gravity and springs≤0.10 mJ mechanical per stop,≤1 Hz; no continuous back-drive. Scope worst stops with/without PD source, bus≤18 V including spikes, capacitor ripple/heating and no continuous TVS conduction. Higher-energy applications need a qualified braking/clamp redesign.
- [ ] Mounted steady-state soak: room 0–40 °C, local PCB air≤45 °C, motorcase≤60 °C, design junction≤125 °C; measure driver/regulator/inductor/bulk/shunts/USB/PH/insulation/carrier. Establish duty/cooling only after tests.
- [ ] Simultaneously insert/remove selected Tensility 10-06137/10-06139 plugs and JST, measure registration/gaps/bends/withdrawal, service/vibration/abrasion and clamp restraint. Resolve CAD/PDF cable-body discrepancy.

## Added diagnostic hardware — all tests unperformed

- [ ] Confirm the GPIO table in [diagnostics.md](diagnostics.md) against real MCU pads; verify LED polarity, visibility and sink current.
- [ ] Verify reset, ROM boot and brownout keep BZ_ALARM silent; the100k gate pull-down is fitted. Firmware must configure PWM low before enabling it.
- [ ] Check TMP102 address0x48, I2C rise time/noise, conversions and ALERT polarity. Compare to a calibrated temperature reference and correlate local PCB readings with driver/motor temperatures. Do not assume a winding-temperature measurement.
- [ ] With valid15V PD only, drive4kHz/50%, ≤100ms bursts at≤1/s. Scope coil/drain current, flyback voltage,3V3 droop and power handover. Accept≤550mA peak/310mA average3V3 load,3.0–3.6V rail and100mA baseline allowance; these are unmeasured qualification ceilings.
- [ ] Disable the buzzer on PD loss and in DATA-only mode. Measure USB input≤100mA before enumeration and ≤100 mA after enumeration and during PD loss.
- [ ] CH32 now uses AP63203 rather than HT7533-1. Both exact buck/inductor/capacitor banks require startup/load-step/stability, hot ripple/dropout, inductor saturation and mounted-temperature testing.
- [ ] Approve LED/MOSFET/temperature/sounder/diode pin1, polarity, pickup center and rotation in the supplier's assembly preview. Confirm reflow profiles, no-clean residue around the sensor and sound-port contamination controls.

Orders, publication and production release are outside this task. No hardware or supplier test has been performed.

DATA-only 3V3 target: ≤75 mA, with the buzzer disabled. Measured USB DATA input must remain ≤100 mA in all steady states and source transitions, including PD loss during an alarm; a failed handover gate requires a hardware/power revision. The assumed70% conversion-efficiency screen is not a measured guarantee.
