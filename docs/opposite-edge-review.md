# NEMA14 RP2040 — current engineering review

**CAD qualified for hardware-prototype publication and JLCPCB engineering/order review.** All 63 intended physical nets are connected. Native DRC reports zero errors and warnings. All 23 required checks ran; the actual results are listed below. Native placement orientation advice remains in its original log and exit status; only the complete recognized advisory class with clean placement DRC is accepted for prototype publication. Both the default and separate order-review CAM audits pass.

The PCB remains 35 × 35 × 1.6 mm with four copper layers. Actual Circuit JSON and Excellon checks verify four Ø3.2 mm NPTH mounts at (±13, ±13). Actual plated-via drills and copper pads meet the requested minimum Ø0.30/Ø0.45 mm.

Both GCT USB4145-03-0070-C C5815189 sockets are upright, with +Z cable insertion, on opposite edges. J_PD is at (0.6, 15.15) mm; J_DATA at (−4.6, −15.15) mm. Defined 10 × 7 × 30 mm plug housings have 23.300 mm nominal separation. The nominal native-model screen covers heads ≤Ø6 × 3 mm, a Ø6.4 mm tolerance envelope and an Ø6 mm tool path. Complete real cable/fastener tolerances and a physical assembly remain unverified.

All 81 fitted parts are TOP SMT. Seven distributed top test pads remain bare, with no purchased part or stencil paste. The BOTTOM AS5600 and two capacitors are doNotPlace and excluded from factory placement and paste. TMP102, status/power LEDs, buzzer, RP2040 flash/clock, driver, USB/PD and fitted JST remain.

The four complete source-component/port/net/trace arrays match GitHub baseline `7005dc2a3b0dd13bed858cae45059b757804eada` literally. All 13 saved oscillator geometries also match: short TOP signals with no signal vias. XIN totals 3.643 mm including its load branch; XOUT 4.795 mm; XTAL_OUT 2.675 mm including its load branch. Oscillator startup, loading and frequency are not bench verified.

Routing changes connect every intended land using actual supplier geometry. They include the moved flash decoupler, grouped USB-present divider, rotated SLEEP resistor, shortened phase transitions, repaired power feeders, genuine ground returns, and a USB ESD-to-series trunk terminal repair. Every saved trace, segment, via, net identity and attached pad is inventoried. USB full-width adjacent ground coverage is checked; fabricator impedance/stackup and real USB operation remain unverified.

JST-SH BM04B-SRSS-TB(LF)(SN), C160390, mates with SHR-04V-S and retains A+, A−, B+, B− order. It is not a physical JST-PH replacement for Rishabh's reference harness. Both port roles and physical USB/PD pins retain the reviewed electrical conventions.

Frozen Circuit JSON SHA-256: `67820851170068eb092c3b611949ce67218b58f1049365fd317e8c1a513645e6`.

| Check | Actual exit code | Evidence |
|---|---:|---|
| all_resistor_edge_clearances | 0 | [log](../artifacts/validation-resume/all_resistor_edge_clearances.txt) |
| typescript | 0 | [log](../artifacts/validation-resume/typescript.txt) |
| drc | 0 | [log](../artifacts/validation-resume/drc.txt) |
| connectivity | 0 | [log](../artifacts/validation-resume/connectivity.txt) |
| fitted_JST_and_actual_drills | 0 | [log](../artifacts/validation-resume/fitted_JST_and_actual_drills.txt) |
| exact_mounts_and_actual_drills | 0 | [log](../artifacts/validation-resume/exact_mounts_and_actual_drills.txt) |
| native_json_checks | 0 | [log](../artifacts/validation-resume/native_json_checks.txt) |
| native_netlist | 0 | [log](../artifacts/validation-resume/native_netlist.txt) |
| native_pin_specification | 0 | [log](../artifacts/validation-resume/native_pin_specification.txt) |
| native_source | 0 | [log](../artifacts/validation-resume/native_source.txt) |
| native_schematic-placement | 0 | [log](../artifacts/validation-resume/native_schematic-placement.txt) |
| native_placement | 1 | [log](../artifacts/validation-resume/native_placement.txt) |
| strict_Circuit_JSON_schema | 0 | [log](../artifacts/validation-resume/strict_Circuit_JSON_schema.txt) |
| USB_coupled_copper_and_ground_reference | 0 | [log](../artifacts/validation-resume/USB_coupled_copper_and_ground_reference.txt) |
| schematic_geometry_ERC | 0 | [log](../artifacts/validation-resume/schematic_geometry_ERC.txt) |
| every_trace_review | 0 | [log](../artifacts/validation-resume/every_trace_review.txt) |
| reference_feedback | 0 | [log](../artifacts/validation-resume/reference_feedback.txt) |
| gerber_shorts | 0 | [log](../artifacts/validation-resume/gerber_shorts.txt) |
| copper_widths | 0 | [log](../artifacts/validation-resume/copper_widths.txt) |
| full_independent_CAM | 0 | [log](../artifacts/validation-resume/full_independent_CAM.txt) |
| native_circular_keepout_regression | 0 | [log](../artifacts/validation-resume/native_circular_keepout_regression.txt) |
| actual_via_drills_and_JLCPCB_clearances | 0 | [log](../artifacts/validation-resume/actual_via_drills_and_JLCPCB_clearances.txt) |
| oscillator_layout | 0 | [log](../artifacts/validation-resume/oscillator_layout.txt) |

[Physical connectivity](../artifacts/physical-connectivity.json) · [Native DRC](../artifacts/drc-report.json) · [Every-trace inventory](../artifacts/reference-feedback/every-trace-review.csv) · [JLCPCB order-review package](../artifacts/jlcpcb-review/JLCPCB-OrderReview.zip) · [Six-sheet schematic PDF](../artifacts/schematic-a4.pdf) · [Nominal mechanical screen](../artifacts/mechanical/opposite-edge-fit.png).

## Remaining external blockers

- Supplier stock/quote and exact BOM, CPL pickup datum, pin 1, polarity and rotations need confirmation in the assembly preview. No substitutes are authorized.
- Require supplier approval of three filled/capped/planarized thermal vias, the 100 µm stencil/reflow process, ≥35 µm outer/17.5 µm inner copper and ≥20 µm via plating.
- Eight short USB shell stakes require agreed TOP secondary soldering; service tier/panel acceptance remains unconfirmed.
- Check the actual 10 mm cable housings, screw/tool tolerances and JST harness wire/coil continuity on physical hardware.
- Firmware, USB data, 15 V PD, regulator isolation, current/thermal limits, regeneration/EMC and oscillator startup require prototype bench validation.
- Rear motor mounting, rear shaft/magnet dimensions, thread engagement and encoder air gap have no verified mechanical evidence. Rear-motor compatibility is not claimed.

No order or payment was submitted. CAD checks do not establish production or supplier approval. Earlier construction plans and reports are historical; use this hash and the linked current receipts for this revision.
