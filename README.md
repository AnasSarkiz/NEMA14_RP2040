# NEMA14_RP2040

Service revision for STEPperONLINE14HM11-0404S,35×35mmPCB,topcomponentassembly,fourcopperlayers. **Hardware qualification remains unperformed.**

- Two USB-C mouths face+Y,14mm pitch,0.4mm beyondPCB. PD requests15V; DATA is computerUSB. Selected Tensility cables and hostbend/access envelopes are documented.
- Keyed JSTB4B-PH-K-S(LF)(SN) /PHR-4 motor harness:1BlackA+,2GreenA−,3RedB+,4BlueB−. Includes restrained BeldenAWG24 extensions, service loop and captured insulating barrier. Factory lead/splice/material qualification remains pending.
- Enlarged front-M3 carrier uses the motor's documentedthreads; rearendcapscrews untouched. UpperPCBholes29.6mm/lower26mm pitch are carrier mounts.
- Panasonic bulk nominalCAD corrected to7.7±0.3mm with8.3mm maximumassembly allowance and originalsupplierassets retained.

Read [engineering review](docs/engineering-review.md), [assembly and mechanical instructions](docs/mechanical-fit.md), [manufacturing requirements](docs/fabrication-requirements.md), [bring-up checklist](docs/bringup-checklist.md) and [current verification](docs/validation.md).

Main source `index.circuit.tsx`; accepted saved copper `index.circuit.json` / `artifacts/board.circuit.json`. Manufacturing ZIP `artifacts/nema14-gerbers.zip`, fittedBOM/CPL/manualheader tables, assemblyPDF and specifiedVIPPOvia list are under `artifacts/`. Use the current engineering manifest for hashes. Historical publications/clean reports do not validate this revision.

```sh
npm run typecheck
npm run source:check
npm run build
npm run shorts
npm run check:copper
npm run check:manufacturing
```

Fabrication requires filled/copper-capped specified SMT vias and supplier placementpreview acceptance. Current, USB/PD, sequencing,regeneration,mountedtemperature and physicalfit are unperformed hardware tests; passingsoftware/CAM does not make this production ready.
