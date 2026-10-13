# Current mounting, connector and copper verification

This is the v1.8.2 **hardware prototype**, not a manufacturing release. The historical v1.4 evidence is in [history](history/v1.4-mounting-usb-verification.md).

Board SHA-256: `567b45bd3737600dee1f833c4ee0692e6d50375be05031324674f744f09bd12e`. Saved copper: 573 traces, 281 plated vias and 41 ground regions. Native DRC reports 0 errors and 0 warnings. Independent Circuit JSON geometry checks 63 nets, with 0 disconnected nets. Independent parsing of the actual current Gerbers reports 0 opens and 0 shorts.

The all-edge resistor audit checks 28 resistors / 56 actual Gerber flashes. Minimum measured nominal pad-to-edge clearance is **0.753 mm**. See [resistor edge clearance](resistor-edge-clearance.md).

The PCB remains **35 × 35 × 1.6 mm**, four layers. Source, saved JSON and actual native Gerber Excellon agree on exactly **Ø3.2 mm NPTH at (±13, ±13)**. The actual drill member is `drill_npth.drl`; its SHA-256 is `ad6dd04eae0f5a99178326f04e1c8b13d9f28e3180116d4fdbb9375d05c98507`.

Both native USB-C mouths remain on +Y at X=±6.2 mm, Y=17.5 mm, with 12.4 mm pitch. Native STEP screening of 81 fitted models passes with the defined two 10 × 30 × 7 mm cable envelopes and Ø4.4 mm head envelopes. This requires **M3 DIN 920 heads ≤Ø4 mm**, with no unverified larger washer/head. Cable envelopes are procurement bounds, not tested cable samples. The native SMT JST-SH C160390 connector remains top-entry, with physical pins 1 A+, 2 A−, 3 B+, 4 B−. Connector physical pins and all reference feedback pins pass the independent source review.

Rear-motor compatibility is **unverified**. The available motor drawing establishes its front mounting pattern; it does not qualify a rear adapter, screw engagement, spacer or complete tolerance stack. The SMT JST has no through-hole tails. Underside copper, insulation, adapter clearance and the mounting stack still require a real assembly review.

## Recorded checks

| Check | Result | Evidence |
| --- | --- | --- |
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
| native_placement | FAIL / review required | `artifacts/validation-resume/native_placement.txt` |
| all_resistor_edge_clearances | PASS | `artifacts/validation-resume/all_resistor_edge_clearances.txt` |
| schematic_geometry_ERC | PASS | `artifacts/validation-resume/schematic_geometry_ERC.txt` |
| every_trace_review | PASS | `artifacts/validation-resume/every_trace_review.txt` |
| reference_feedback | PASS | `artifacts/validation-resume/reference_feedback.txt` |
| gerber_shorts | PASS | `artifacts/validation-resume/gerber_shorts.txt` |
| copper_widths | PASS | `artifacts/validation-resume/copper_widths.txt` |
| full_independent_CAM | FAIL / review required | `artifacts/validation-resume/full_independent_CAM.txt` |

Native placement suggestions remain visible in their log; their nonzero advisory result is not described as a blanket PASS. The raw-export CAM remains FAIL for the assembly findings below; the separately prepared corrected order CAM passes. Prototype publication accepts those disclosed assembly findings only after all electrical, copper, drill and mechanical checks pass. The publisher rejects actual CAM opens, shorts, copper-spacing failures, unassigned copper and stale evidence.

## Remaining release blockers

- BOM-source-identity
- EP-stencil-coverage
- assembly-paste-policy
- assembly-table-policy
- paste-source-mismatch
- silkscreen-clearance
- stencil-release-screen

The corrected order package fixes BOM/CPL, bare-pad purchasing/paste treatment, exposed-pad windows, stencil apertures and silkscreen; its CAM audit is PASS with zero findings. Pickup orientation, actual stencil/reflow capability, filled/capped vias and secondary shell soldering still need supplier acceptance. Firmware must implement the temperature polling/alarm policy, RGB GPIOs and PWM buzzer. No assembled hardware, USB/PD bench test, phase-current measurement, thermal run or rear-motor fit has been qualified. A generated Gerber archive is not manufacturing approval.

See [reference components and wiring](reference-feedback.md), `artifacts/resume-validation.json`, `artifacts/reference-feedback/every-trace-review.csv`, `artifacts/trace-width-review.json` and `artifacts/manufacturing/audit.json` for the actual evidence and limits.
