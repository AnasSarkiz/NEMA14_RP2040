# Final local validation — RP2040,2026-10-10

Exact inspected baseline commit:`f3811f8a1722df5bad88abdf638cb14bca0c5d59`. Final saved circuit SHA256:`0d5c64228122dc31dace9bb30ffdf36574f049d332c72365e2a2fd1528a2bc6a`. `index.circuit.json` is byte-identical. Fresh source physical pins, native pad geometry and component values/MPNs match the saved routed board; only documented topology changes differ from the baseline.

`artifacts/validation/independent-checks.json` records real command exits and log hashes: typecheck, build/native DRC, physical connectivity, trace widths, Gerber shorts and functional silkscreen all pass. Saved DRC has zero errors and one generic Q_DATA power-pin warning. Actual CAM audit passes zero shorts/opens, source-to-copper/drill equality, archive-member equality, clearances, mask/web and stencil checks. The 35 unassigned copper islands are exclusively intentional no-connect terminals; no unanchored non-NC islands remain.

Actual outer-layer audit verifies motor/PD main widths≥0.45 mm and sense≥0.30 mm with individually bounded native fanout/resistor-leaf exceptions. Nonzero phase vias remain disclosed. Every required SMT via-in-pad is listed in TypeVII process CSVs; all ordinary drill/stencil intersections pass.

All 4 actual PDF pages were rasterized and visually inspected. Passive references/values use≥6.5 pt DejaVu Sans. Project Chromium schematic-review UI opened every A4 sheet with all labels present and no browser errors. This is a project review interface, not official IDE/WebGPU/electrical simulation. CLI source/netlist/pin/schematic checks exit 0; placement exits 1 with supplier orientation/pickup advisories while its Errors/Warnings counts are 0. The generic Q_DATA width suggestion is retained to provide legible BASE/COLLECTOR separation. The installed CLI's historical`pcb-style` attempt was unavailable, not passed.

Full native STEP review/rebind passes nominal component/fastener/carrier/plug/wire intersection checks and bounded clearance screens. Complete installation reservation≈49.204×157.480×102.771 mm before host tolerances/motion/access. JST CAD post/real insertion and cable-body CAD/PDF discrepancies remain unresolved physical gates.

Current assembly/BOM/PnP/manual-header tables, Gerber/drill ZIP, A4 PDF and mechanical/harness drawings are regenerated and bound in`artifacts/validation/engineering-review-manifest.json`. Every listed manifest entry is rehashed by this script. Historical router outputs, prior publication receipts and old power reports are not final acceptance evidence.

Neither board is released for ordering/production. All hardware tests and supplier approvals are unperformed. See [operating envelope](supported-operating-envelope.md), [engineering review](engineering-review.md) and [bring-up checklist](bringup-checklist.md). This task makes local commits only and publishes nothing.
