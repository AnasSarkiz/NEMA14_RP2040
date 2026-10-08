# Exact motor compatibility: 14HM11-0404S

Both board variants target the same **STEPperONLINE 14HM11-0404S** bipolar four-wire motor. [Official full drawing](../references/motor/14hm11-0404s/14HM11-0404S_Full_Datasheet.pdf), [official STEP](../references/motor/14hm11-0404s/14HM11-0404S.STEP) and [provenance](../references/motor/14hm11-0404s/provenance.json) establish the motor identity. This review does not establish compatibility with other NEMA14 models.

| Requirement | Manufacturer evidence |
| --- | --- |
| Phase current | 0.40 A rated |
| Winding resistance | 25 Ω ±10% at 25 °C |
| Winding inductance | 24 mH ±20% at 1 kHz |
| Winding voltage | 10 V nominal = 0.40 A × 25 Ω; this is not the required chopper supply voltage |
| Step angle | 0.9°, 400 full steps/revolution |
| Holding torque | 0.11 N·m at rated excitation; reduced controller current does not guarantee this torque |
| Body | 35.2 mm maximum square, 28.2 mm maximum body length |
| Front mounting | Four M3 threads, 26 ±0.2 mm square pitch, ≥4 mm thread depth |
| Environment | −10 to +50 °C ambient, class B 130 °C insulation, maximum specified temperature rise 80 °C |
| Leads | A+ black, A− green, B+ red, B− blue; 300 ±10 mm drawing length |

Connect black/green to the A phase and red/blue to the B phase. Confirm winding pairs with an ohmmeter before soldering. Do not connect or disconnect the motor while the driver is powered.

## Current setting and tolerance

The review correction uses **3.9 kΩ / 1 kΩ** for the reference divider and **0.24 Ω, 1%** sense resistors. Both divider values are one tenth of the original 39 kΩ / 10 kΩ values, so nominal current remains unchanged:

`VREF = 3.3 × 1/(3.9+1) = 0.673469 V`

`Itrip = VREF / (8 × 0.24) = 0.350765 A`

The reference-input maximum ±3 µA through the corrected 796 Ω Thévenin resistance contributes ±2.39 mV; the old divider permitted ±23.88 mV. Sense-resistor nominal dissipation at the peak is 29.53 mW. The listed 125 mW resistor rating still needs manufacturer hot-temperature/pulse derating verification.

| Arithmetic envelope | Result | Meaning |
| --- | --- | --- |
| Minimum formula result | 0.337465 A | Rail low, resistor tolerances and REF leakage; excludes driver regulation error |
| Nominal formula result | 0.350765 A | 3.3 V rail, nominal resistors, zero REF leakage |
| Maximum formula result | 0.364518 A | Rail high, resistor tolerances and REF leakage; excludes driver regulation error |

Supply basis: **AP63203 CCM manufacturer range**, 3.270–3.330 V. These are formula bounds, **not qualified actual minimum/maximum phase currents**. Allegro specifies ±5% error only at VREF = 2 V for DAC 70.71%/100%, and ±15% at DAC 38.27%; the approximately 0.6735 V reference has no specified error bound in the verified document. Sense-ground voltage, resistor temperature drift, switching blanking and PCB noise add further uncertainty. Measure both phases over every microstep and temperature condition before accepting the 0.40 A limit. No increase to 0.40 A nominal is authorized by this analysis.

## Winding losses and supply requirements

With the valid sinusoidal 1/16-step sequence, `IA² + IB² ≈ Itrip²`. Thus expected total cold winding copper loss is approximately **3.076 W**, or 2.768–3.383 W at the specified resistance tolerance. Full-step mode also sets each phase to approximately 70.71% of Itrip: approximately **0.248 A per phase**, not 0.351 A in both phases.

A conservative hypothetical allocation with both phases simultaneously at peak is 6.152 W; it is a supply/thermal screening case, not the expected valid sine-table operating loss. Manufacturer full-current two-phase excitation at 0.40 A would dissipate 8 W cold. Assuming copper resistance coefficient 0.00393/°C, 85 °C winding temperature increases nominal sine-table loss to approximately 3.801 W; actual winding temperature is unmeasured.

Use a USB-C PD source advertising **15 V**, preferably at least **1 A source capacity**. The board input-current screening budget is 0.75 A; the charger capacity does not force that current through the board. Ideal coil-only input current is approximately 0.205 A at 15 V; add driver, logic, converter and mechanical-work losses. A 5 V fallback is insufficient for the A4988 operating range and must leave the motor disabled. The nominal 10 V winding rating is compatible with a 15 V **current-regulated** driver; connecting 15 V directly to a winding is not equivalent.

## Speed, acceleration and regeneration

Nominal `L/R = 0.96 ms`; independent L/R tolerance corners give **0.698–1.280 ms**. Ignoring back-EMF and semiconductor drops, a stationary phase driven by 15 V reaches nominal 0.3508 A in approximately 0.843 ms, or 1.079 ms for the slow L/R corner. These calculations do not establish maximum running speed or available torque.

Initial unloaded prototype targets are **5 rpm start**, a **20 rpm/s ramp**, and **30 rpm initial ceiling**. At fixed 1/16 stepping there are **6400 STEP pulses/revolution**: 533 pulses/s at 5 rpm and 3200 pulses/s at 30 rpm. Use ≥5 µs STEP high/low and DIR setup/hold targets, and wait ≥2 ms after releasing SLEEP; these exceed the driver minimum timing. Increase load/speed only after checking current tracking, missed steps, overshoot and temperature. The motor’s rated holding torque is not a speed/acceleration guarantee.

The selected native Panasonic bulk capacitor is 100 µF ±20%, 35 V, with 0.60 Arms rated ripple at 100 kHz / 105 °C and ≤0.16 Ω ESR at 100 kHz / 20 °C; see [manufacturer evidence](component-evidence.md). This improves energy storage and ripple margin but does not qualify the bus clamp.

Winding magnetic energy at nominal current is approximately 1.476 mJ for the valid sine-table state. Mechanical energy returned during deceleration can be much larger and depends on rotor/load inertia and speed. The exact SMF18A clamp/energy rating is not verified; capture bus regeneration and hot-plug overshoot. Firmware must gate driver enable on valid PD voltage, and safe stopping behavior must be developed and tested.

## Rear assembly qualification

The official drawing dimensions **front** threads. Their existence does not establish rear mounting threads. The STEP rear recesses model end-cap screw features; do not remove or repurpose those screws or modify the motor. See [mechanical-fit.md](mechanical-fit.md) for the separate front-thread carrier/standoff candidate, assembly views, insulation, wire exit and connector access. The official STEP header is dated 2018 while the drawing revision is 2025; compare the actual supplied motor with both before making a fit claim.

The rear PCB must remain electrically isolated from the motor casing, including screw hardware and copper/vias. The motor heat may place board components above their allowed local ambient even when room ambient is valid. Validate spacing, temperatures and motor-wire exit on a physical assembly.

All numerical results, assumptions and PCB Designer calculator invocations are recorded in [motor-electrical-calculations.json](../artifacts/validation/motor-electrical-calculations.json). **Compatibility is an engineering target; phase-current, thermal, USB/PD and physical-fit qualification remain unperformed.**
