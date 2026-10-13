# NEMA14_RP2040 1.9.0: engineering fixes

Saved board SHA-256: `687a7d6026cd2deaa7f3f0bd21356bed7b025d0004cedc4ad058dcc3f6aa7436`. Starting GitHub revision: `e04df7a3b606b280389109405de96601e9430695`. Every original functional terminal, named/implicit net group, NC role, fitted MPN, LCSC number, component value and rating is preserved; see `artifacts/engineering-fixes/final-engineering-verification.json`.

The board is 35 × 35 × 1.6 mm, four layers, with four NPTH holes exactly (±13, ±13), Ø3.2 mm. USB mouths remain (−6.2, 17.5) and (6.2, 17.5), both facing +Y. Two defined 10 mm cable housings have 2.4 mm nominal separation. The fastener requirement remains maximum Ø4 mm heads; the STEP screen includes a Ø4.4 mm × 3 mm envelope. This verifies nominal CAD geometry, not physical assembly or rear motor attachment.

All 81 fitted parts and 7 separate bare test pads remain on top. Standard USB-C schematic symbols, both contact orientations, independent 5.1 kΩ data CC resistors, CH224K 15 V configuration, Schottky supply isolation, SMT JST-SH C160390 coil order, TMP102, LEDs and buzzer are retained. See [reference pin review](reference-feedback.md) and [motor connector/harness](jst-restoration.md).

## Routing and source fixes

ESD protection and local parts were moved to support coupled outer-layer USB trunks with explicit MCU/ESD/resistor fanouts. Affected copper and ground returns were rerouted; redundant stubs and duplicate records were removed. The RP2040 shared rail bridge is 0.25 mm on inner1 after its conservative thermal screen rejected 0.16 mm. The reviewed layer policy bounds low-current/control escapes and the short 0.3 mm phase bridge; clocks/flash retain a 15 mm section limit. Every trace, segment, via ownership and attached physical port is inventoried, with actual copper connectivity and thermal/clearance checks required separately.

| Reference | Previous XY mm | Current XY mm |
|---|---|---|
| C_IO49 | (2.857, 4.75) | (1.778, 4.75) |
| R_DP | (4.3, 5.3) | (4.371, 5.3) |
| R_CC2 | (10.4, 7.5) | (9, 4.4) |
| U_ESD | (13.15, 8.3) | (9, 7) |
| Q_STATUS_R | (9, 4.8) | (13.15, 8.3) |
| TP_SWCLK | (1.223, 5.24) | (-3, -6.6000000000000005) |

| Coupled core | Signal / reference layer | Length difference mm | Exact grounded reference coverage outside actual USB via antipads |
|---|---|---|---|
| connector_to_ESD | bottom / inner2 | 0.445 | 100.000%, 100.000% |
| ESD_to_series | bottom / inner2 | 0.171 | 100.000%, 100.000% |
| series_to_MCU | top / inner1 | 0.065 | 100.000%, 100.000% |

Core width/gap are 0.25/0.16 mm; local terminal fanouts are 0.16 mm. Every projected centerline is intersected geometrically with adjacent grounded copper. This is layout evidence; fabricator stackup/controlled impedance, USB signal integrity, EMC and hardware operation are unverified.

Display offsets are canonical strings and optional null IDs are omitted. Board-level silkscreen records have a valid metadata owner while retaining absolute coordinates. BZ1 uses the installed generic pinout classification with its real MPN, pins, nets, models and qualified schematic retained. Strict schema checks accept no inherited errors.

## Manufacturing output

The default `artifacts/nema14-gerbers.zip` now applies qualified source-derived BOM/CPL, top-only paste, 100 µm stencil apertures, four 60% exposed-pad windows and readable silkscreen with mask/drill/edge guards. Bare test pads and mounting holes are excluded from assembly purchasing and paste. Copper, masks, outline and drill bytes remain identical to the upstream native exporter. `artifacts/engineering-fixes/upstream-native-gerbers.zip` is retained for diagnosis; the default archive and the separate order-review CAM both pass their independent audits.

The actual drill/outline files verify the specified 35 mm square and (±13, ±13) Ø3.2 mm mounting holes. Source, placement and Gerber copper agree. Current counts: 593 trace records, 276 vias, 39 grounded regions; 63 physical net groups connected. Native DRC: zero errors/warnings. Placement orientation advice remains visible and is accepted only when every full flagged-component diagnostic is a recognized passive-orientation suggestion and placement DRC is clean.

| Required check | Result | Evidence |
|---|---|---|
| all_resistor_edge_clearances | PASS | `artifacts/validation-resume/all_resistor_edge_clearances.txt` |
| typescript | PASS | `artifacts/validation-resume/typescript.txt` |
| drc | PASS | `artifacts/validation-resume/drc.txt` |
| connectivity | PASS | `artifacts/validation-resume/connectivity.txt` |
| fitted_JST_and_actual_drills | PASS | `artifacts/validation-resume/fitted_JST_and_actual_drills.txt` |
| exact_mounts_and_actual_drills | PASS | `artifacts/validation-resume/exact_mounts_and_actual_drills.txt` |
| native_json_checks | PASS | `artifacts/validation-resume/native_json_checks.txt` |
| native_netlist | PASS | `artifacts/validation-resume/native_netlist.txt` |
| native_pin_specification | PASS | `artifacts/validation-resume/native_pin_specification.txt` |
| native_source | PASS | `artifacts/validation-resume/native_source.txt` |
| native_schematic-placement | PASS | `artifacts/validation-resume/native_schematic-placement.txt` |
| native_placement | Reviewed orientation advisories; placement DRC clean | `artifacts/validation-resume/native_placement.txt` |
| strict_Circuit_JSON_schema | PASS | `artifacts/validation-resume/strict_Circuit_JSON_schema.txt` |
| USB_coupled_copper_and_ground_reference | PASS | `artifacts/validation-resume/USB_coupled_copper_and_ground_reference.txt` |
| schematic_geometry_ERC | PASS | `artifacts/validation-resume/schematic_geometry_ERC.txt` |
| every_trace_review | PASS | `artifacts/validation-resume/every_trace_review.txt` |
| reference_feedback | PASS | `artifacts/validation-resume/reference_feedback.txt` |
| gerber_shorts | PASS | `artifacts/validation-resume/gerber_shorts.txt` |
| copper_widths | PASS | `artifacts/validation-resume/copper_widths.txt` |
| full_independent_CAM | PASS | `artifacts/validation-resume/full_independent_CAM.txt` |

## Remaining supplier and hardware blockers

JLCPCB must confirm exact stock/quote, pickup datums, pin 1/polarities and rotations, specified copper/plating/stackup, 100 µm stencil/reflow and the three filled/capped/planarized exposed-pad vias. Eight USB shell through-hole joints require quoted secondary soldering. The mating JST-SH pigtail and motor lead termination need supplier/assembler confirmation; the factory motor has bare leads.

Firmware, USB boot/data, 15 V PD negotiation, host-only regulator headroom, isolation/backfeed, current accuracy, regulator stability, switching/sense/ground behavior, temperature/thermal operation, buzzer/LEDs, motor regeneration and EMC need prototype bench validation. Real plugs, fastener SKU/tolerances, thread engagement, spacing/underside clearance and the rear motor/adapter must be checked physically. The manufacturer drawing supplies front mounting dimensions only. No rear compatibility, supplier order approval or production release is claimed; no order/payment has been submitted.
