> Historical baseline document: this predates the opposite-edge v1.11.0 draft. See [current draft and blockers](opposite-edge-review.md) for current evidence.

# NEMA14_RP2040 1.10.2: engineering fixes

Saved board SHA-256: `a261317dc5ba675ad0bc012489fdf99ec7cd64299d3db6f8985828f6757781d6`. Starting GitHub revision: `db8bd58`. Original functional nets, NC roles, values and ratings are preserved, with the authorized USB4145 upright connector substitution and three added bottom DNP encoder components; see `artifacts/engineering-fixes/final-engineering-verification.json`.

The board is 35 × 35 × 1.6 mm, four layers, with four NPTH holes exactly (±13, ±13), Ø3.2 mm. USB4145-03-0070-C (C5815189) sockets are upright at nominal (−6.05, 15.15) and (6.05, 15.15), with insertion along +Z. Two defined 10 mm cable housings have 2.1 mm nominal separation. The fastener requirement remains maximum Ø4 mm heads; the STEP screen includes a Ø4.4 mm × 3 mm envelope. This verifies nominal CAD geometry, not physical assembly or rear motor attachment.

All 81 fitted parts and 7 separate bare test pads remain on top. Standard USB-C schematic symbols, both contact orientations, independent 5.1 kΩ data CC resistors, CH224A 15 V configuration, Schottky supply isolation, SMT JST-SH C160390 coil order, TMP102, LEDs and buzzer are retained. See [reference pin review](reference-feedback.md) and [motor connector/harness](jst-restoration.md).

The AS5600-ASOM (C79815) and its 100 nF/1 µF bypass capacitors are on the bottom with doNotPlace. It shares the existing 3.3 V I²C bus (address 0x36, distinct from TMP102 0x48). Its OUT and PGO remain NC. Rear shaft, magnet selection/air gap, encoder firmware and physical fit require later verification.

Minimum via drill/pad are Ø0.30/Ø0.45 mm. Exactly three grounded thermal barrels are required at the reviewed MCU, driver and PD exposed-pad sites; the RP2040 MCU site is shifted within its native EP to clear the bottom encoder lands. The actual process coordinates are in `Thermal-Via-Process.csv` and `src/thermal-via-offsets.json`. The source geometry and actual Excellon drills are checked, including drill-to-copper and drill-to-drill clearance. GCT’s native USB STEP is invalid in OCCT; the mechanical screen uses its complete bounding solid as a conservative envelope, retaining original supplier assets.

## Routing and source fixes

ESD protection and local parts were moved to support coupled outer-layer USB trunks with explicit MCU/ESD/resistor fanouts. Affected copper and ground returns were rerouted; redundant stubs and duplicate records were removed. Every rail bridge retains its actual downstream-load and copper-width screening; see `artifacts/trace-width-review.json`. The reviewed layer policy bounds low-current/control escapes; clocks/flash retain a 15 mm inner1 section limit. The current A− repair uses outer/inner2 copper. Every trace, segment, via ownership and attached physical port is inventoried, with actual copper connectivity and thermal/clearance checks required separately.

| Reference | Previous XY mm | Current XY mm |
|---|---|---|
| J_PD | (-6.2, 12.57501465) | (-6.05, 15.149999999999999) |
| J_DATA | (6.2, 12.57501465) | (6.05, 15.149999999999999) |
| Y_MCU | (1.1000000000000005, -6.219999999999999) | (1.1, -6.220000000000001) |
| R_XOUT | (-1.9399999999999997, -4.79) | (3.35, -7.32) |
| C_XIN | (-1.55, -7) | (-1.55, -4.85) |
| C_XOUT | (4.2, -7.27) | (4.9, -7.32) |
| U_DRV | (4.0001, -11.5001) | (4.0001, -12.1001) |
| C_CP | (1.640115, -16.679998) | (0, -13.05) |
| C_VCP | (5.210115, -15.249998) | (5.210115, -15.849998) |
| C_VREG | (2.070023, -15.430001) | (2.070023, -16.030001000000002) |
| C_DRV_LOGIC | (9.610115, -14.169998) | (9.610115, -13.7) |
| R_SA | (-0.151495, -9.763734) | (-0.151495, -10.163734) |
| R_REF_L | (6.81, -16.03) | (7.2, -16.45) |
| C_REF | (9.29, -15.42) | (9.29, -15.62) |
| TP_3V3 | (-0.32299999999999995, 14.906) | (0, 14.98) |
| TP_GND | (0.32200000000000006, 16.309) | (0, 16.42) |

| Coupled core | Signal / reference layer | Length difference mm | Exact grounded reference coverage outside actual USB via antipads |
|---|---|---|---|
| connector_to_ESD | bottom / inner2 | 0.141 | 100.000%, 100.000% |
| ESD_to_series | bottom / inner2 | 0.171 | 100.000%, 100.000% |
| series_to_MCU | top / inner1 | 0.065 | 100.000%, 100.000% |

Core width/gap are 0.25/0.16 mm; local terminal fanouts are 0.16 mm. Every projected centerline is intersected geometrically with adjacent grounded copper. This is layout evidence; fabricator stackup/controlled impedance, USB signal integrity, EMC and hardware operation are unverified.

Display offsets are canonical strings and optional null IDs are omitted. Board-level silkscreen records have a valid metadata owner while retaining absolute coordinates. BZ1 uses the installed generic pinout classification with its real MPN, pins, nets, models and qualified schematic retained. Strict schema checks accept no inherited errors.

## Manufacturing output

The default `artifacts/nema14-gerbers.zip` now applies qualified source-derived BOM/CPL, top-only paste, 100 µm stencil apertures, four 60% exposed-pad windows and readable silkscreen with mask/drill/edge guards. Bare test pads, mounting holes and the three bottom DNP encoder components are excluded from assembly purchasing and paste. Copper, masks, outline and drill bytes remain identical to the upstream native exporter. `artifacts/engineering-fixes/upstream-native-gerbers.zip` is retained for diagnosis; the default archive and the separate order-review CAM both pass their independent audits.

The actual drill/outline files verify the specified 35 mm square and (±13, ±13) Ø3.2 mm mounting holes. Source, placement and Gerber copper agree. Current counts: 691 trace records, 318 vias, 48 grounded regions; 63 physical net groups connected. Native DRC: zero errors/warnings. Placement orientation advice remains visible and is accepted only when every full flagged-component diagnostic is a recognized passive-orientation suggestion and placement DRC is clean.

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
| native_circular_keepout_regression | PASS | `artifacts/validation-resume/native_circular_keepout_regression.txt` |
| actual_via_drills_and_JLCPCB_clearances | PASS | `artifacts/validation-resume/actual_via_drills_and_JLCPCB_clearances.txt` |
| oscillator_layout | PASS | `artifacts/validation-resume/oscillator_layout.txt` |

## Remaining supplier and hardware blockers

JLCPCB must confirm exact stock/quote, pickup datums, pin 1/polarities and rotations, specified copper/plating/stackup, 100 µm stencil/reflow and the three filled/capped/planarized exposed-pad vias. The eight USB shell through-hole joints use the reference part’s 0.7 mm stakes in a 1.6 mm PCB; JLCPCB must quote and confirm a suitable top-side secondary solder process. No bottom-side fitted parts or bottom paste are specified. The mating JST-SH pigtail and motor lead termination need supplier/assembler confirmation; the factory motor has bare leads.

Firmware, USB boot/data, 15 V PD negotiation, host-only regulator headroom, isolation/backfeed, current accuracy, regulator stability, switching/sense/ground behavior, temperature/thermal operation, buzzer/LEDs, motor regeneration and EMC need prototype bench validation. Real plugs, fastener SKU/tolerances, thread engagement, spacing/underside clearance and the rear motor/adapter must be checked physically. The manufacturer drawing supplies front mounting dimensions only. No rear compatibility, supplier order approval or production release is claimed; no order/payment has been submitted.
