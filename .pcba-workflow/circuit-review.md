# Circuit review: NEMA14_RP2040

Status: **BLOCKED for circuit qualification and manufacturing release**; engineering correction/review evidence is complete. No physical test, fabrication, assembly-placement, quote or order approval is inferred from software checks.

The authoritative circuit is `index.circuit.tsx` → `src/board.tsx`; accepted routed copper is `artifacts/board.circuit.json`. Both USB-C mouths face +Y; PD supplies the 15 V motor bus and DATA supplies computer USB and optional logic power. The diode OR supplies AP63203 / 3.3 V, followed by RP2040’s internal 1.1 V regulator, while A4988 regulates motor phase current at nominal 0.3508 A. A4988 low-VREF accuracy, exact inductor/effective-capacitance limits and actual power-transition/current/thermal performance remain unqualified.

Evidence and complete review tables:

- [Operating principle, component functions, physical pins, power domains, reset/boot states and finding dispositions](../docs/engineering-review.md).
- [Exact selected manufacturer specifications, pin maps, provenance and unresolved primary evidence](../docs/component-evidence.md), [manufacturer data](../references/manufacturer-review.json), [source BOM](../docs/bom.md).
- [Motor calculations and limitations](../docs/motor-compatibility.md), [deterministic calculator evidence](../artifacts/validation/motor-electrical-calculations.json).
- [Native fourteen-page A4 visual/browser/CLI review and unchanged electrical graph](../docs/schematic-review.md); official IDE analyzer unavailable is explicitly distinguished.
- [Actual copper/replay/CAM/STEP evidence](../artifacts/validation/engineering-review-manifest.json), [manufacturing](../docs/manufacturing-review.md), [mechanical fit](../docs/mechanical-fit.md).
- [Firmware-visible semantics](../docs/firmware-interface.md), [unexecuted prototype measurement plan](../docs/bringup-checklist.md).

[SPEC] A4988 STEP high/low ≥1 µs, setup/hold ≥200 ns, wake ≥1 ms; no driver ±5% accuracy claim at 0.6735 V VREF. [TARGET] 15 V PD operation and nominal 0.3508 A phase peak, with actual phase currents ≤0.40 A after uncertainty. [TBD-MEASURE] Low-reference accuracy, resistor temperature effects, fast rail collapse/OE release, NPN power-off levels, USB programming, regeneration, mounted thermal behavior and carrier/cable fit. Firmware uses active-low host detection and the enabled VM×21 conversion; safe OE/enable/sleep initialization is mandatory.

Native official netlist/pin/source CLI checks exit 0. PCB-placement CLI exits 1 for disclosed orientation/courtyard advisories while reporting 0 placement DRC errors and warnings; actual saved-copper/CAM connectivity has no opens/shorts. The generic NPN ERC no-VDD warning is disclosed. Exact source artifacts, supported inputs and software versions are recorded in the manifest. This resolves identified software-correctable defects while retaining the documented physical and manufacturer evidence gates.
