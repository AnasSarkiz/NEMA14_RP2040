# Mounting and USB verification — 2026-10-11

Baseline: GitHub main `003da97e355f9392e5e85f5762d08dda637ad6a8`. Review version: **1.2.0**.
Board SHA-256: `2cbf6ee9a465527ed7f40d7c818eeb72912a649ba8fb4d9125bf6aba64d7048a`.

The four mounting holes were already correct in the latest GitHub baseline. The native source now uses the declared 26 mm pitch and Ø3.2 mm diameter, and DRC additionally enforces every exact coordinate rather than only hole count. Fresh native source output, saved `artifacts/board.circuit.json`, delivered `index.circuit.json` and the actual `drill_npth.drl` member of the regenerated Gerber archive all prove (−13,−13), (−13,13), (13,−13), (13,13) mm, Ø3.2 mm, absolute metric origin at board centre. `artifacts/mount-drill-verification.json` records exact file/archive hashes. No offsets or mirroring were applied.

## USB and copper

The latest GitHub layout already clears the requested holes. Exact unchanged TYPE-C-31-M-12 STEP bodies face outward at X=±17.5 mm, Y=4.5 mm and retain connector accessibility. Native body clearance to each radius-2.7 mm mounting-head envelope is at least **1.33 mm**. Each bounded 12×30×7 mm plug envelope has zero component/head intersection; this is a defined cable procurement envelope, not a physical cable test. The complete **61 original fitted supplier STEP models** pass nominal component/component and fastener intersection checks with original SHA-256 hashes verified.

No component relocation or signal-trace rerouting was needed for a conflict absent from the latest GitHub commits. `artifacts/mounting-change-proof.json` proves all existing source pin/net/component records, pads, traces, vias and CAD transforms equal the baseline. RP2040 mounting keepouts now protect all four copper layers. CH32 ground-fill generation cleans rounded pinched BReps, splits disconnected pieces and retains only anchored regions; the previous 0.113156 mm² unintended top island is gone from the actual Gerbers.

Actual CAM/source copper and drill differences are zero within the documented parser tolerances, with no shorts, opens, unconnected pads or unexpected copper islands. Measured distinct-conductor spacings: top 0.150161 mm, bottom 0.150613 mm, inner1 0.155648 mm, inner2 0.150882 mm. Mount-hole edge clearance is at least 1.30 mm; copper-to-outline clearance is at least 0.35 mm. Raw export bytes and parsed evidence are retained in `artifacts/manufacturing/`.

## Actual checks

519 traces, 79 vias, 11 ground regions; 48 physical connectivity groups checked, none disconnected. Native DRC: zero errors and zero warnings. Source compilation completed with zero render errors. Source netlist passes. Native placement returns exit 1 for pre-existing suggested passive rotations (four RP2040 / three CH32); its placement DRC reports zero errors/warnings. These optimization suggestions are retained, and no unverified pad/placement change is applied to already connected copper. The netlist command's rejected JSON-input diagnostic is retained; the supported TSX-input check passed.

| Check | Result | Actual log |
|---|---|---|
| typescript | PASS | `artifacts/validation-resume/typescript.txt` |
| drc | PASS | `artifacts/validation-resume/drc.txt` |
| connectivity | PASS | `artifacts/validation-resume/connectivity.txt` |
| exact_mounts_and_actual_drills | PASS | `artifacts/validation-resume/exact_mounts_and_actual_drills.txt` |
| native_json_checks | PASS | `artifacts/validation-resume/native_json_checks.txt` |
| native_netlist | PASS | `artifacts/validation-resume/native_netlist_source.txt` |
| native_pin_specification | PASS | `artifacts/validation-resume/native_pin_specification.txt` |
| native_source | PASS | `artifacts/validation-resume/native_source.txt` |
| native_schematic-placement | PASS | `artifacts/validation-resume/native_schematic-placement.txt` |
| native_placement | FAIL — retained findings | `artifacts/validation-resume/native_placement.txt` |
| gerber_shorts | PASS | `artifacts/validation-resume/gerber_shorts.txt` |
| copper_widths | PASS | `artifacts/validation-resume/copper_widths.txt` |
| full_independent_CAM | FAIL — retained findings | `artifacts/validation-resume/full_independent_CAM.txt` |

Exact native mechanical screen: **PASS**, current board hash bound in `artifacts/mechanical/mount-usb-screen.json`. Top copper and every other copper layer were viewed; independent Gerber raster views are under `artifacts/manufacturing/independent-render/`.

## Remaining blockers

Full manufacturing audit: **FAIL**. Remaining finding classes: `BOM-source-identity`, `EP-stencil-coverage`, `assembly-paste-policy`, `assembly-table-policy`, `paste-source-mismatch`, `silkscreen-clearance`, `stencil-release-screen`. Raw assembly outputs include bare solder interfaces in BOM/CPL, paste-policy violations and fine-pitch/exposed-pad stencil issues; silkscreen overlaps mask openings. Exact assembler pickup/pin-1 rotations are unverified. These failures are in the published prototype evidence; no full manufacturing PASS is claimed.

Rear-motor compatibility is **unverified**. The manufacturer drawing establishes front mounting, not usable rear end-cap threads. This screen checks PCB components/fasteners and bounded cable envelopes only; it does not validate an attached motor, rear adapter/carrier, tolerance stack, cable sample or load-bearing hardware. Physical assembly, USB flashing/PD, startup, phase-current and thermal tests remain pending.

**PROTOTYPE FABRICATION READY: NO. Hardware unassembled and untested.**

Publication retains reviewed geometry and pins unchanged supplier CAD URLs to the pushed GitHub revision. `artifacts/publication-provenance.json` in the registry package records the original/released JSON hashes and proves only CAD URL metadata changed. Public publication receipts are recorded separately after remote verification.
