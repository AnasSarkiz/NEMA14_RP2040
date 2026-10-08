# NEMA14_RP2040

Independent RP2040 hardware prototype for STEPperONLINE **14HM11-0404S**, with a dedicated **15 V USB-C PD power port** and separate **computer USB-C data port**.

[GitHub](https://github.com/AnasSarkiz/NEMA14_RP2040) · [tscircuit](https://tscircuit.com/AnasSarkiz/NEMA14_RP2040). These project links may show earlier published revisions; this review does not publish or order boards.

The 35 × 35 mm, four-layer board uses top-side component assembly and four Ø3.2 mm PCB holes on a 26 mm square. Motor mounting uses the separate front-thread carrier candidate described in [mechanical fit](docs/mechanical-fit.md); direct rear mounting is unqualified. Both USB-C openings face outward from the same +Y edge: PD at X−5.3 mm, DATA at X+5.3 mm. Use compact cable overmolds ≤10 mm wide and physically verify both plugs fit simultaneously without carrier or screw interference.

- RP2040, 2 MB GD25Q16EEIGR flash, 12 MHz crystal and the required 3.3 V/1.1 V supplies and bypasses.
- AP63203 fixed 3.3 V buck, diode-OR logic power from either USB port. Only PD powers the motor.
- A4988 fixed 1/16 stepping: **0.3508 A nominal peak**, 3.9 kΩ/1 kΩ reference divider and 0.24 Ω sense resistors. Low-VREF current accuracy must be measured.
- Native Panasonic **100 µF / 35 V C178585** bulk capacitor, verified manufacturer ripple/ESR ratings.
- Native VM isolation switch with default-off OE, **VM voltage conversion ×21**, and **active-low** transistor host detection.
- **67 fitted components**, each with exact JLCPCB imported footprint and native OBJ/STEP. J_MOTOR, J_DEBUG and J_BOOT are bare PCB interfaces; mounting holes are PCB features.

Motor wiring: black=A+, green=A−, red=B+, blue=B−. Keep ENABLE_N high/SLEEP low until valid PD voltage, initialized firmware and current qualification. Keep VM_ENABLE_N high impedance/HIGH in ROM/reset; GPIO27 (physical 39) asserts LOW only after stable logic power, then wait ≥0.5 ms before ADC sampling.

**Engineering prototype, not a fabrication release.** No motor-control firmware or physical USB/PD/current/thermal test results are supplied. Final software checks and parsed manufacturing outputs must be regenerated for the latest routing; earlier clean reports do not validate new copper.

See [engineering review](docs/engineering-review.md), [electrical design](docs/electrical.md), [firmware interface](docs/firmware-interface.md), [BOM source review](docs/bom.md), [supplier CAD](docs/supplier-cad.md), [bring-up checklist](docs/bringup-checklist.md) and [variant comparison](docs/variant-comparison.md). The native bulk CAD has a documented height mismatch; mechanical screening uses the manufacturer's maximum envelope.

The main source entry is index.circuit.tsx → src/board.tsx. Authoritative saved copper is artifacts/board.circuit.json; root index.circuit.json and exported Gerbers must match it. npm run typecheck, npm run source:check, npm run build, npm run export, npm run shorts and npm run check:copper provide software checks. npm run autoroute produces diagnostic routing; accepted routing and final manufacturing checks remain separate review steps. No publication command is executed by this review.
