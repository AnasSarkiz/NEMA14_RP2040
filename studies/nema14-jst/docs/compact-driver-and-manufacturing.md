# NEMA14 JST compact placement and manufacturing diagnostic

The accepted source is unchanged. This is a distinct top-side placement and authored-copper experiment, **not a promoted controller or a fabrication-ready board**. It starts from `455a8ae`. The same personal draft remains the destination. Original boards, main and NEMA14 WAGO are untouched.

## What the old routing errors actually establish

`artifacts/iteration-5/native-error-groups.json` groups the pinned native objects by unique physical port, electrical net and copper island:

- 319 messages refer to **319 unique ports**, with no duplicate messages.
- 316 are unrouted after the aggregate abort. Three ports—U_DRV.GND18, MS1 and MS2—touch same-net copper physically but lack a direct trace/port association.
- MS3 and RESET_N are in the same physical island and neither is in the remaining port-error set. The old static MS3/RESET failure is absent. The remaining native error is `aJ ran out of iterations (capacity-autorouter@0.0.958)`.
- The largest groups are GND (85), V3V3 (52) and PD_VBUS (14). The artifact retains all port identities and island memberships. These are missing-copper diagnostics; they do not prove 319 blocked exits or identify a unique next obstruction.

Three bounded native probes retain every one of the old input's 879 obstacles and 11 preloaded traces. The old MS3/RESET pair solves without new copper (14.259 s), MS1/MS2 solves (15.903 s), and the mode via to VDD solves (18.654 s). The last probe changes the mode trace and physically connects VDD to that island, but full-board opens remain **66**. It is diagnostic only: the old mode via fails the tolerance screen below. A fourth accumulated probe process was killed with exit 137; it has no result, and the exact termination cause is unverified.

No aggregate routing was rerun this pass.

## Distinct compact geometry

`experiments/compact/candidate.tsx` applies a 28-component top-side pose delta to the original source at render time. The driver is flipped toward the upper-right; shunts anchor a central current-measurement cluster, amplifiers sit beside them, driver capacitors surround the driver, and the buck stage moves west. The source keeps the 35 × 35 mm outline, four layers/1.6 mm thickness, both USB poses, side-facing JST, bottom encoder, top encoder DNP capacitor poses and all four physical screw exclusions fixed. No fitted part moves to the bottom.

The 53-part diagnostic scope retains the fixed mechanical parts, MCU, clock and decoupling, USB protection, and power/current cluster. It omits the other controller parts deliberately. Its placement screen passes for 52 top courtyards; this is not a whole-controller packing result.

A bounded integer-packing search for the remaining parts returned UNKNOWN after 120 s at an earlier cluster checkpoint. No complete solution was produced. The report identifies constraints as requirements, not passes. This does not prove that every all-top arrangement is impossible. The final full candidate leaves unsolved parts at their original locations and is explicitly rejected:

| Full-controller measurement | Control | Unpacked compact candidate |
| --- | ---: | ---: |
| Locality passes / total | 25 / 59 | 40 / 59 |
| Failed targets | 34 | 19 |
| Targets gained / regressed | — | 16 / 1 |
| Independent shorts | 0 | 33 |
| Independent spacing findings, including shorts | 0 | 39 |
| Open nets | 66 | 66 |

The regressed previously passing target is C_BOOTSTRAP.pin2 to U_BUCK.SW: 28.670 mm against 4 mm. Some still-passing high-priority distances also worsen: C_VM→VBB1 increases 1.691→1.974 mm and C_VM→VBB2 increases 3.771→4.976 mm. Sense input placement improves: R_SA→SENSE1 is 6.691→3.649 mm; R_SB→SENSE2 is 9.678→5.999 mm, still above 4 mm. Those regressions prevent promotion regardless of the aggregate locality counter.

## Actual copper and physical shunt pickups

The authored scope contains **28 native PCB trace fragments and 18 real four-layer through vias**. Eight logical Kelvin/power paths retain their actual terminal pairs; coordinates are regenerated from moved supplier pad geometry. Each 0.16 mm Kelvin branch leaves the real body-facing shunt-pad edge; the corresponding 0.45 mm current branch leaves the opposite edge. All four actual-pad cut tests pass. Independent overlap checks include the real barrels and find no shared winding-current copper outside those pads.

The two ground returns are actual three-fragment native paths with 0.60 mm wires and two through barrels per phase. The strict continuity test permits only that phase's three traces, two barrels, resistor ground pad and EP; other GND pads cannot provide a shortcut. Removing the source barrel or narrowing a wire rejects each phase.

| Copper measurement | Control | Compact authored scope | Compact native nine-net output |
| --- | ---: | ---: | ---: |
| A driver→shunt wire | 3.685 | 8.950 | 9.066 |
| A shunt→connector wire | 20.756 | 14.930 | 14.930 |
| A two power-branch sum | 24.441 | 23.880 | 23.996 |
| B driver→shunt wire | 26.895 | 9.950 | 10.288 |
| B shunt→connector wire | 25.705 | 11.346 | 11.506 |
| B two power-branch sum | 52.600 | 21.295 | 21.794 |
| A Kelvin + / − | 25.545 / 43.517 | 6.131 / 6.595 | 6.131 / 6.595 |
| B Kelvin + / − | 12.321 / 10.307 | 6.319 / 6.502 | 6.176 / 6.609 |

Values are mm of planar native wire, excluding via barrels, winding and IC conduction; branch sums are not a complete motor-current loop or inductance/thermal result. The A driver leg regresses despite a shorter phase sum. Existing control source/copper stays intact.

Actual source-pad-center to EP-center ground wire sums are **4.608754 / 4.728842 mm**, compared with the old 6.601309 / 14.264937 mm source-to-star sums plus their common 1.775127 mm EP-center segment. The compact numbers include travel inside the endpoint pads; they are distinct from the separate corridor-reservation estimates in `cluster-critical.json`.

The stack has not been selected. Actual return length is `planar wire + 2 × top-to-inner1 depth`, so the 5 mm total requires depths no greater than **0.195623 / 0.135579 mm** respectively. No complete 3D ≤5 mm acceptance is claimed. Barrels also have a different cross-section from 0.60 mm wires.

The return and bypass priorities follow [Allegro's layout guidance, page 12](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf#page=12), and the real-pad Kelvin checks follow [TI's layout guidance, page 24](https://www.ti.com/lit/ds/symlink/ina240.pdf#page=24). Both ceramics remain closer to their VBB pins than the bulk capacitor. This alone does not validate supply-loop copper.

## Native entry point and bounded routing

The unchanged pin is Core 0.0.2110 / router 0.0.958 / CLI 0.1.2261 / checks 0.0.283 / schema 0.0.562, Bun 1.4.2. There is no board dependency bump.

`XDG_CONFIG_HOME=.config tsci build experiments/compact/cluster.tsx --routing-disabled --disable-parts-engine` exits **0**. The CLI's source and PCB arrays match the independently checked native artifact exactly. Its schematic warnings remain in `native-cli.log`. This is a routing-disabled subset entry, not a complete controller routing pass.

The authored subset has zero independent shorts, spacing, edge, drill, hole or screw violations; twelve selected native checks also return zero. It still has **38 open subset nets**. These opens cannot be compared directly to the control's 66 because components were omitted.

One final bounded nine-net diagnostic runs through **native Core materialization**, not just a hand-translated SRJ. It retains all 293 native scope obstacles and 28 preloaded traces. The router reports solved in **25.830 s**, producing **52 traces / 31 through vias**, but the output is rejected:

- Independent checks: **1 short, 14 spacing segment findings, 15 board-edge segment findings, 32 open subset nets**; zero drill/hole/screw findings. Spacing includes the short. Counts are segment findings, not 14 unique failures.
- The hard short is the SENSE2 via to U_DRV.VBB2. Native pad/trace clearances also fail at VBB2/SENSE2 (0.134318 mm), NC7/VCP (0.108443 mm) and VCP/CP2 (0.065205 mm), against 0.15 mm.
- Native selected checks report 3 pad/trace findings, 1 overlapping-trace finding, 1 via/pad finding and 3 via-in-pad findings. All-routing diagnostics retain 186 port errors, 15 trace errors, 3 pad/trace errors and 1 pad/pad error.
- Six authored wire shapes change, so the requirement to freeze all eight logical paths fails. The six ground fragments keep their wire shapes and strict width/continuity, and all four real pad-cut checks still pass. Those partial successes do not qualify the output.
- Some automatic driver supply branches neck down to 0.16 mm. There are zero native thickness-check findings, but that is not proof of supply-current, barrel or thermal capacity. No warning is suppressed.

An earlier 36.148 s raw SRJ comparison is retained locally for diagnosis; it is not substituted for this actual Core result. Full-board native routing remains the old incomplete result with 66 open nets.

## Manufacturing screen and smallest unresolved process decision

The screen distinguishes nominal drill-edge-to-SMT gap, annulus-to-foreign-copper gap, and a conservative hole-position-adjusted gap on each physical layer. It applies the published inner via rule separately from the component PTH inner rule, and separately records via-hole-to-track spacing. The reference is [JLCPCB's capability table](https://jlcpcb.com/capabilities/Capabilities), retrieved 2026-11-27; these figures are not supplier acceptance.

The old MS3 escape has a nominal hole-to-SMT gap of **0.024517 mm**, becoming **−0.050483 mm** under ±0.075 mm hole-position sensitivity alone. It remains diagnostic, not fab-qualified. Its inner1 hole-to-foreign-copper gap is 0.245837 mm nominal, 0.170837 mm position-adjusted: nominally above the separate 0.20 mm via rule, but below it after this sensitivity.

The compact authored scope has one position-only SMT non-overlap failure and no position-adjusted inner-via rule failures. All eight component PTH holes pass the separately screened 0.30 mm inner rule at nominal and position-adjusted geometry. Two via-to-track adjusted gaps sit essentially on the 0.20 mm boundary, providing no additional budget. The routed subset has four position-only SMT non-overlap failures and eight position-adjusted inner-via rule failures; see its full per-via report.

The star landings expose an intrinsic package/process tradeoff in this placement. The actual EP-to-ground-pad row gaps are **0.450126 / 0.449872 mm**. A perfectly centered 0.30 mm drill leaves **0.075063 / 0.074936 mm** nominal gap, and **+0.000063 / −0.000064 mm** after position tolerance alone. The surrounding annulus-to-foreign-pad gaps remain about 0.254 mm; those larger copper gaps do not fix the hole-to-SMT budget. A bounded driver-only 0.01 mm grid found 399 nominal landings, with best sampled adjusted hole gap still negative. This is not proof against all curved stubs or other top-side layouts.

Keeping the same 0.45 mm via pad while evaluating a 0.25 or 0.20 mm drill would add 0.025 or 0.050 mm hole clearance per side. **Neither is adopted:** the board's 0.30 mm minimum remains fixed, and the via tool/finished-hole tolerance, registration, mask/tenting, current capacity and supplier process require a real decision and review. Filled/capped via-in-pad is another process-dependent alternative, not an assumed escape.

Only four layers and 1.6 mm thickness are defined. A selected stack, copper weights, via process and drill/registration/assembly tolerances are missing. The generic +0.13/−0.08 mm PTH size range is shown only as an extra sensitivity; its applicability and tool compensation for these vias are unverified. The nominal radial annulus of 0.075 mm is likewise not qualified merely by quoting a generic capability table. No manufacturing gate, minimum width, spacing or mechanical reserve is relaxed.

## Mechanical and reproducible evidence

All changed fitted supplier OBJ bounds are transformed from the pinned assets and conservatively screened against four radius-3.2 mm screw projections and the catalog seated, withdrawal and service-grip envelopes. They clear: smallest changed-body screw gap is **0.526246 mm** and plug-envelope gap **1.984943 mm**. Fixed body transforms retain the prior exact-pose evidence. A fresh STEP-kernel check could not run because CadQuery is unavailable; no large dependency install was attempted. Motor/magnet, fastener stack, physical mating, wire bend, tolerance and handling remain unverified.

`npm run test:compact` regenerates the scoped TSX and checks exact source/PCB replay, full-width copper, four pad cuts, both isolated returns and five negative controls. Typecheck, 14 existing copper regressions, 6 placement regressions and the existing plug regressions pass. Hosted replay exposed a single derived `pcb_trace.trace_length` cache difference of 4.44×10⁻¹⁶ mm, with all actual coordinates, widths, layers and identities identical. The guard checks that cache within 10⁻¹² mm against independently recomputed wire length; all physical fields still compare exactly. Three controls reject a larger cache error and even one-ULP coordinate or width changes. This does not change any layout or DRC gate. The production locality gate is unchanged and continues to block routing.

`artifacts/iteration-5/verification.json`, `core-driver/verification.json`, the raw native error objects and `copper-review.png` bind the claims to actual artifacts. Large raw inputs are gzip-compressed without changing their contents; `python3 experiments/compact/expand-artifacts.py` expands them for the diagnostic commands. Rebuild TSX for portable CAD URLs. An archived evaluator's absolute model URL is not a fabrication input.
