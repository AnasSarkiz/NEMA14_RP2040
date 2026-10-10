# Bring-up and prototype qualification — all hardware tests unperformed

Use the proposed [supported operating envelope](supported-operating-envelope.md) and exact final source/hash. Record instruments, uncertainty, waveforms, environment, fitted part lots and pass/fail disposition. Do not mark boxes from calculations or CAM results.

- [ ] Supplier confirms actual stackup, finished drills/annuli, all TypeVI/TypeVII fill/cap/mask processes, cap flatness, plated USB slots and stencil. Reconcile automated BOM/PnP and manual motor-header scope; approve pickup/pin 1/polarity preview.
- [ ] Insertion coupon proves exact JST header fit in 0.75±0.05 mm bores; verify housing/contact compatibility, AWG/OD, crimp/splice pull strength and temperature/material certificates. Confirm front M3 mounting, thread engagement, tails/barrier/clamp/service slack and host envelope.
- [ ] With motor disconnected: continuity, winding/color mapping, insulation to metal carrier; current-limited DATA/PD supplies. Verify 3V3 and RP1V1, reset defaults, total 3V3 load≤20 mA CH32 /100 mA RP, DATA draw≤100 mA and 3.0–3.6 V logic.
- [ ] PD analyzer confirms 15 V contract/fallback disables bridge. Demonstrate DATA USB enumeration, ROM programming and recovery/debug. Test both cable orders, insertion/removal, PD/source loss and command timeout; no unexpected steps/restart.
- [ ] Scope ADC−VDD,3V3,VM,LOGIC_IN,PG,ENABLE/SLEEP through slow/fast ramps and abrupt collapse. Bound negative/coupled ADC ringing and backfeed. Use revised ADC scale 223.76596 with calibrated thresholds.
- [ ] Measure both phase peaks across microsteps, decay, supply and mounted temperature. Acceptance≤0.25 A including uncertainty; manufacturer 0.40 A is a hard motor limit. Adjust VREF divider if required and requalify. Measure sense/ground bounce and effective copper/return resistance; no shunt compensation.
- [ ] Verify biased/temperature/endurance-conditioned RP capacitance≥4 µF input/24 µF output bank, startup/load-step/ripple/stability and inductor peak/heating. Test limited fault/startup safely; converter current limit may exceed inductor saturation screening rating.
- [ ] Validate actual returned energy including rotor, load, gravity and springs≤0.10 mJ mechanical per stop,≤1 Hz; no continuous back-drive. Scope worst stops with/without PD source, bus≤18 V including spikes, capacitor ripple/heating and no continuous TVS conduction. Higher-energy applications need a qualified braking/clamp redesign.
- [ ] Mounted steady-state soak: room 0–40 °C, local PCB air≤45 °C, motorcase≤60 °C, design junction≤125 °C; measure driver/regulator/inductor/bulk/shunts/USB/PH/insulation/carrier. Establish duty/cooling only after tests.
- [ ] Simultaneously insert/remove selected Tensility 10-06137/10-06139 plugs and JST, measure registration/gaps/bends/withdrawal, service/vibration/abrasion and clamp restraint. Resolve CAD/PDF cable-body discrepancy.

Orders, publication and production release are outside this task. No hardware or supplier test has been performed.
