# Functional A4 schematic review

The previous 14 numbered pages are replaced by 4 native A4 landscape sheets (297 × 210 mm). Sheet names describe their electrical function and appear directly in the tscircuit sheet selector:

1. USB-C PD & Logic Power
2. RP2040 & USB Control
3. Flash, Clock & MCU Supply
4. Motor Driver & Voltage Monitor

The layout follows the organization inspected in [Rishabh's RP2040 motor controller](https://tscircuit.com/imrishabh18/rp2040-motor-controller): named functional sheets, local sections, nearby chip-purpose notes, and grouped bypass circuits. It does not copy that design's electronics. Repeated page-wide chip lists are removed. Native schematic groups and section borders identify related circuits; actual schematic wires connect capacitor banks and local dividers. Named nets link the sections and sheets. Every symbol and numbered physical pin is retained, including NC marks, motor wire colors and the USB power/control distinction.

`npm run source:check` builds the electrical source and prepares the functional sheets. `bun scripts/refresh-functional-schematic.ts` applies the same presentation to saved routing; it fails if any non-schematic record differs from the committed release, if symbol pin identities change, or if preparation is not idempotent. The main `index.circuit.tsx`, saved root `index.circuit.json`, and native distribution remain part of publication.

Native `tsci check schematic-placement` reports zero findings on both the prepared source and saved board. The Chromium review opens every page, checks all reference labels and A4 dimensions, and reports zero browser errors. `python3 scripts/audit-functional-schematic.py` checks actual rendered SVG text bounding boxes for text collisions and foreign text/net labels entering native symbol-body rectangles. It reports zero overlaps. The PDF is `artifacts/schematic-a4.pdf`; individual native SVG/PNG pages remain available.

The PCB, all electrical/source/CAD records, fabrication ZIPs, Gerber/drill files, BOM and PnP are unchanged. `artifacts/validation/functional-schematic-invariance.json` and `functional-schematic-evidence-binding.json` prove the exact comparison against the prior engineering commit. Existing CAM/thermal/mechanical results are reused only through identical input evidence, with the original provenance preserved; schematic/native/browser checks are rerun. No fabricated board or hardware test is claimed. This project Chromium UI is separate from the official IDE/WebGPU analyzer.

The RP2040 RUN pull-up is placed in the programming/recovery section, away from the MCU body. The stronger rendered-body check detects the original misplaced V3V3 label before this correction; the RP2040 regression receipt is `artifacts/validation/functional-schematic-overlap-before.json`.
