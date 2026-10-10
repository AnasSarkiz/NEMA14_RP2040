# Proposed operating envelope — RP2040

This is a general-purpose **prototype qualification envelope**, chosen without assuming a host machine. It is the intended supported envelope after the acceptance tests below pass. Neither design has been built or qualified; these limits are requirements, not measured ratings. CAM success does not approve continuous operation, fabrication or production release. An application must establish its inertia, speed, stored spring/gravity energy and stopping behavior before operation.

| Parameter | Conservative limit | Evidence / qualification |
|---|---|---|
| Motor | STEPperONLINE 14HM11-0404S only; keyed black/green/red/blue harness | Exact motor drawing: 0.40 A/phase, 25 Ω ±10%, 24 mH ±20%. Other NEMA14 motors need separate review. |
| PD motor input | Requested 15 V; normal 14.25–15.75 V | Reject unexpected PD voltage. Confirm negotiation and safe power loss on a prototype. |
| Motor bus during stopping | **≤18 V**, including all switching/ESR/cable peaks | Oscilloscope acceptance requirement; TVS breakdown is higher and cannot enforce this operating limit. |
| Winding current | 6.2 kΩ / 1 kΩ reference, unchanged 0.24 Ω shunts: **0.238715 A nominal**. Accepted actual peak in each phase ≤0.25 A; never exceed manufacturer 0.40 A. | Divider/shunt tolerances and reference leakage can raise the formula. A4988 accuracy is specified at VREF2 V, not this ≈0.458 V reference; current must be measured. If actual peak exceeds 0.25 A, adjust the reference resistor and repeat qualification. Copper arithmetic is not used to compensate shunts. |
| Logic supply load | ≤100 mA total on 3V3, including all fitted loads; **no external loads** | A qualification load ceiling, not an established board-consumption measurement. Measure worst active USB/CPU/driver consumption. |
| Logic voltage | 3.0–3.6 V in every powered state | Acceptance window, not a guaranteed tolerance attributed to either regulator. Check start/stop and loaded ripple. |
| USB data input | USB2 host 5 V only;≤100 mA drawn from DATA before and after enumeration | No higher host budget assumed. No motor power from DATA. Verify enumeration and ROM/application programming. |
| Temperature | Room 0–40 °C, noncondensing; local air at regulators/PCB≤45 °C; motor case≤60 °C | Mounted motor heating may violate local 45 °C even in a cool room. Thermal-soak test determines duty/cooling. No continuous-duty or torque/speed guarantee yet. |
| Junction design target | ≤125 °C | A design target. Holtek actual maximum 150 °C; A4988/other individual manufacturer limits remain separate. |
| Returned mechanical energy | **≤0.10 mJ per stop**, including rotor/load kinetic energy, gravity and elastic energy; stops≤1 Hz | Energy budget below. Sustained or externally forced back-driving is outside this envelope. |
| Back-driving / brake | No continuous regenerative operation; no uncontrolled falling/overhauling load | No brake resistor/controller is fitted and no PD sink capability is assumed. Higher returned energy requires a separately qualified braking/clamping subsystem and revised protection review. |
| Environment | Indoor bench/light machine, protected from conductive debris, liquids and cable impact | Harness barrier/clamp/access and supplier fabrication remain qualification gates. |

## Regeneration calculation and application check

Use **all** returned energy, not only the attached load: `Emechanical = ½ Jtotal ω² + returned gravitational energy + returned elastic energy`, with total reflected inertia including the rotor. Gear efficiency is conservatively 100% when estimating energy returned to the board. Do not count winding dissipation, friction, firmware reaction or PD source absorption as a guaranteed sink.

At 0.25 A maximum actual phase current and 28.8mH maximum documented winding inductance, assume both windings simultaneously contain `½ L (IA² + IB²) = 1.800 mJ`. Adding the 0.10 mJ mechanical allocation gives **1.900 mJ per stop**. Panasonic's initial−20% capacitance and endurance-change−30% corner gives **56 µF**, rather than relying only on the 80 µF initial corner. This is an endurance-test screen; it is not a lifetime warranty or a verified effective-capacitance floor at every temperature/frequency.

From 15.75 V,56 µF stores **2.1263 mJ** before 18 V. The ideal capacitor-only peak is **17.774 V**. The remaining voltage margin must absorb ESR/ESL, switching and cable overshoot; the calculation does **not** certify that margin. Scope the actual bus with the PD source connected and disconnected, hottest mounted board, smallest qualified capacitor, worst microstep/decay and simultaneous stop. Reject any operating point exceeding 18 V. Maximum 1 Hz repetition is a proposed acceptance ceiling; confirm recovery, capacitor ripple/temperature and protection heating. TVS pulse ratings do not establish repetitive braking capacity.

For illustration, at 60 rpm, the 0.10 mJ kinetic-energy allocation permits at most `Jtotal = 2E/ω² ≈5.07×10⁻⁶kg·m²`, including the rotor. That is an energy example, **not** a qualified 60 rpm speed or guaranteed torque rating. A slower system can still violate the budget through gravity, springs or externally driven motion.

## ADC and power-transition requirements

The revised passive monitor is 100 kΩ feeding 10 kΩ∥470Ω to GND, with 10 nF to GND at the ADC. Nominal scale is **223.76596**;15 V is≈67.03 mV at the ADC. With 1% resistor corners,35 V gives≤**0.159559 V**, plus≈0.475 mV for a 1µA input-leakage screen. This remains below the powered-off+0.3 V pin limit without an enable signal, firmware, rail clamp or unqualified switch behavior. Stored capacitor voltage is bounded by the same low divider voltage through instantaneous logic collapse. Nominal RC≈4.47 µs. The 35 V calculation is pin-protection screening, **not authorization for 35 V bus operation**. Verify negative ringing and high-frequency coupling physically.

Firmware must configure the pin as a high-impedance analog input with no pull-up/output drive, apply the new scale, use sufficient acquisition time, and calibrate against a DMM. At a 3.3V12-bit ADC, bus resolution is≈0.180 V/count; use averaging and hysteresis, and do not claim precision overvoltage protection. On reset, keep STEP low, ENABLE_N high and SLEEP low. Arm the motor only after valid PD-good status, a measured 14.25–15.75 V bus and stable logic; disable on loss of these conditions. Firmware is not the regenerative clamp. Qualified brownout/reset behavior, PG transitions and power-source handover are still required.

## Prototype acceptance and limits that remain unproved

- Measure both phase peaks and balance across normal supply, microsteps and temperature. Acceptance≤0.25 A per phase; no motor 0.40 A exceedance. Record actual sense-return bounce with a differential/Kelvin measurement.
- Measure worst logic load against the 100 mA ceiling. Verify 3.0–3.6 V regulation, ripple, startup, ROM boot and USB activity at room 0/40 °C and motor-heated local 45 °C. The CH32 Holtek temperature coefficient is typical; a full-temperature regulation bound is not established from that typical value.
- Perform slow and fast power ramps, abrupt PD/data removal, all cable insertion orders, brownout/reset and source handover. Record ADC/3V3/PG/ENABLE/SLEEP and bus peaks. No unexpected motor drive or powered-off pin-limit violation is accepted.
- Test stopping energy/repetition at the envelope corners, including source disconnection. Verify≤18 V peak and no continuous TVS conduction; use qualified external braking for more energetic hosts.
- Validate buck capacitance at operating bias/temperature/age, stability, startup, load steps and inductor peak/heating. Typical supplier curves are screening data, not a guaranteed worst-case capacitor specification.
- Establish continuous-duty time/cooling only after steady-state mounted temperature testing. Check driver/regulator junction estimates against 125 °C design target and motor/harness/cable material limits.
- Test simultaneous exact USB plug insertion/removal, JST mating and insertion coupon, harness crimp/splice pull strength, strain relief, vibration, abrasion and insulation. Resolve material certificates and supplier fill/cap/slot/stencil/pickup acceptance.

Calculations are executable in `artifacts/engineering/supported-operating-envelope.json`. No hardware measurement or supplier approval has been performed. The installation remains the enlarged front-thread carrier documented in `mechanical-fit.md`; the 35×35mm PCB is not the host-machine envelope.
