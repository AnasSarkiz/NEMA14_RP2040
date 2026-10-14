# NEMA14_RP2040 1.11.0 — WORK IN PROGRESS

**Not ready for fabrication or JLCPCB order review. This revision has failed electrical/routing checks and has not been republished. The current public release remains v1.10.2.**

35 × 35 × 1.6 mm, four-layer PCB. The upright USB-C connectors now occupy opposite edges, separated by 30.3 mm in Y. The nominal model screen uses two 10 mm cable housings, maximum Ø6 × 3 mm screw heads and a Ø6.4 mm screening envelope. The four NPTH mounts remain (±13, ±13), Ø3.2 mm; minimum via drill/pad is Ø0.30/Ø0.45 mm.

Factory fitted components remain TOP only; the AS5600 and two capacitors are BOTTOM doNotPlace. Intended component values, source ports, source nets and source traces match the latest GitHub baseline. Physical copper connectivity is incomplete.

See [current draft and blockers](docs/opposite-edge-review.md), [qualification receipts](artifacts/resume-validation.json), [physical connectivity](artifacts/physical-connectivity.json), [native DRC](artifacts/drc-report.json) and [nominal mechanical screen](artifacts/mechanical/opposite-edge-fit.png). Earlier reports and assembly concepts describe previous revisions and are not evidence for this draft.

The Gerbers, BOM/CPL and stencil data are diagnostic review assets. Do not order from this draft. Supplier process/pickup approval, bench testing, rear-motor mounting and encoder shaft/magnet fit remain unverified.
