# NEMA14_RP2040 1.11.0 — hardware prototype

**CAD qualified for hardware-prototype publication and JLCPCB engineering/order review.** All 63 physical nets are connected; native DRC has zero errors and warnings. Fresh default and order-review CAM audits pass. Native passive-orientation advice retains its actual command status and requires supplier pickup confirmation.

35 × 35 × 1.6 mm, four layers. Actual JSON and drills verify four Ø3.2 mm mounts at (±13, ±13) and minimum via drill/pad Ø0.30/Ø0.45 mm. Upright USB-C sockets occupy opposite edges, leaving 23.300 mm between the defined 10 mm plug housings. The nominal model screens maximum Ø6 × 3 mm heads within a Ø6.4 mm envelope and an Ø6 mm tool path.

All 81 fitted parts are TOP SMT; seven bare top test pads and three BOTTOM encoder/DNP parts are excluded from factory placement/paste. USB/PD, JST-SH A+/A−/B+/B−, TMP102, LEDs, buzzer, driver, flash and the short TOP oscillator are retained. Exact electrical source arrays and all 13 oscillator geometries match the GitHub baseline.

[Current evidence and blockers](docs/opposite-edge-review.md) · [23-check receipt](artifacts/resume-validation.json) · [Connectivity](artifacts/physical-connectivity.json) · [JLCPCB package](artifacts/jlcpcb-review/JLCPCB-OrderReview.zip) · [Six-sheet schematic](artifacts/schematic-a4.pdf).

Supplier/process/pickup approval, physical cable/screw/harness checks and firmware/electrical/thermal bench testing remain outstanding. Rear motor fit and encoder shaft/magnet/air gap are unverified. No order or payment was submitted.

Frozen board SHA-256: `67820851170068eb092c3b611949ce67218b58f1049365fd317e8c1a513645e6`.
