## CH224A migration — 1.13.0 (hardware prototype)

**Order review, 17 October 2026: hold the assembled-board order.** The final review identifies regulator/driver layout corrections, screws that cannot reach the motor with the proposed stack, and feature/process decisions to resolve. See [the final order review](docs/final-order-review-2026-10-17.md). The passing short/DRC checks remain valid for their geometric scope.

U_PD is now CH224A C42459160. A 56 kΩ CFG1 resistor preserves the fixed 15 V request; R_PD is 0 Ω and C_PD remains 1 µF / 50 V. Existing placements, mounts, USB positions and the ESSOP10 pads are retained. See [electrical changes, validation and remaining limits](docs/ch224a-migration.md) and [current BOM](artifacts/jlcpcb-review/JLCPCB-BOM.csv).

The sections below describe the earlier baseline. Their byte-preservation claims and historical qualification receipts do not certify this migration. Use the current migration test receipts before manufacturing review.

## Schematic pin alignment — 1.12.2

The USB connector pin stems now meet their symbol boxes in both functional sheets. Only schematic display lengths changed; pin endpoints, wires, source connectivity, PCB geometry and the motor assembly geometry remain identical to 1.12.1. [Correction and preservation evidence](artifacts/schematic-pin-alignment/verification.json) · [Updated A4 schematic](artifacts/schematic-a4.pdf).

## Motor and hardware assembly preview

The 1.12.1 assembly rotates the motor’s fixed-wire outlet toward the board’s JST edge. Four colored leads take a short loop through insulated splices to a 28-AWG JST-SH pigtail. The SHR-04V-S plug seats in the BM04B-SRSS-TB header at the catalog’s 6.3 mm mated height. Pin order is black A+, green A−, red B+, blue B−. There is no motor-side socket.

[Assembly details](docs/top-assembly.md) · [Full assembly](artifacts/top-assembly/assembly-complete.png) · [JST connection](artifacts/top-assembly/assembly-jst-connection.png) · [Top view](artifacts/top-assembly/assembly-top.png) · [Native assembly JSON](assembly.circuit.json).

PCB geometry and fabrication files are preserved from 1.12.0; schematic pin display lengths were corrected in 1.12.2. Nominal CAD checks pass for conductor separation, component clearance and plug alignment. Rear motor retention and physical crimp/latch fit remain unverified.

# NEMA14_RP2040 — hardware prototype

**CAD qualified for hardware-prototype publication and JLCPCB engineering/order review.** All 63 physical nets are connected; native DRC has zero errors and warnings. Fresh default and order-review CAM audits pass. Native passive-orientation advice retains its actual command status and requires supplier pickup confirmation.

35 × 35 × 1.6 mm, four layers. Actual JSON and drills verify four Ø3.2 mm mounts at (±13, ±13) and minimum via drill/pad Ø0.30/Ø0.45 mm. Upright USB-C sockets occupy opposite edges, leaving 23.300 mm between the defined 10 mm plug housings. The nominal model screens maximum Ø6 × 3 mm heads within a Ø6.4 mm envelope and an Ø6 mm tool path.

All 81 fitted parts are TOP SMT; seven bare top test pads and three BOTTOM encoder/DNP parts are excluded from factory placement/paste. USB/PD, JST-SH A+/A−/B+/B−, TMP102, LEDs, buzzer, driver, flash and the short TOP oscillator are retained. Exact electrical source arrays and all 13 oscillator geometries match the GitHub baseline.

[Current evidence and blockers](docs/opposite-edge-review.md) · [23-check receipt](artifacts/resume-validation.json) · [Connectivity](artifacts/physical-connectivity.json) · [JLCPCB package](artifacts/jlcpcb-review/JLCPCB-OrderReview.zip) · [Six-sheet schematic](artifacts/schematic-a4.pdf).

Supplier/process/pickup approval, physical cable/screw/harness checks and firmware/electrical/thermal bench testing remain outstanding. Rear motor fit and encoder shaft/magnet/air gap are unverified. No order or payment was submitted.

Saved 1.12.0 board SHA-256: `f45cf8eac9c29d17873cfb8719b3996c870c2552bf8077f68041e46fed1c5e4d`.
