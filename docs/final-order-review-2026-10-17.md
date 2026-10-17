# RP2040 final order review — 17 October 2026

**Recommendation: HOLD the assembled-board order for v1.13.0.** Resolve the power-layout findings, the mounting hardware and the supplier assembly plan before submitting an order. This is a review of NEMA14_RP2040 with the 14HM11-0404S motor, not the proposed NEMA11 project.

Reviewed board SHA-256: `16a605a565a272ce12a5194f28e1d9d8359c183d6110d117a4771d2b8ec91d2d`.

The fresh short/DRC review remains valid: zero DRC errors/warnings, zero all-layer Gerber shorts, 64 connected nets, and passing independent native/order CAM audits. The public v1.13.0 board and both public Gerber archives match the checked files. Those results verify connectivity and geometric rules; they do not establish regulator stability, current-sense quality, screw engagement or supplier process approval.

## 1. Regulator and driver layout — correct before ordering

The schematic contains the expected regulator and driver components, but their placement and interconnects require correction against the manufacturer layout guidance:

| Connection | Current measured evidence | Recommended correction |
|---|---|---|
| AP63203 VIN to C_BUCK_IN positive pad | 7.405 mm between pad centres; input capacitor is below the IC with its positive terminal facing away | Place the input bypass directly across VIN/GND and minimize the high-frequency loop; review the bootstrap, inductor, output capacitors and feedback pickup together |
| RP2040 VREG_OUT to its 1 µF capacitor | 3.560 mm pad-centre separation; an approximately 12.20 mm routed trace chain goes through BOTTOM and returns to TOP via the DVDD capacitor branch | Put C_VREG_OUT next to pin 45 with a direct short connection and short ground return; likewise tighten C_VREG_IN at pin 44 |
| A4988 SENSE1 to R_SA | 7.132 mm pad-centre separation; approximately 8.48 mm routed trace chain through inner2 | Move R_SA close to SENSE1; use a short current path and low-impedance return to the driver ground/star region |
| A4988 SENSE2 to R_SB | 6.970 mm pad-centre separation; approximately 9.67 mm routed trace chain through inner2 | Move R_SB close to SENSE2 with the same return strategy |
| A4988 local supply bypass | VBB1 to C_VM positive pad is 6.114 mm between pad centres; the found routed trace chain is about 17.79 mm. C_BULK positive pad is 16.557 mm from VBB1 | Put the ceramic supply bypass at the supply pins and bring the bulk bypass into the local driver supply loop |

These are engineering layout concerns, not newly detected shorts or assertions of observed hardware failure. The manufacturers do not give a universal numeric maximum trace length here. The recommendation is based on the measured departures from their close-bypass/short-sense layout guidance. DC trace-width screening does not qualify switching-loop inductance or regulator stability.

Sources: [Diodes AP63203 datasheet, page 15](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf#page=15); [Raspberry Pi hardware design guide, pages 8–9](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf#page=8); [Allegro A4988 datasheet, page 12](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf#page=12).

Measurements and trace-chain coordinates are in `artifacts/final-order-review-2026-10-17/critical-copper-paths.json`. Its graph models saved centre lines and real vias, not all thickness-based overlaps or parasitics. Found paths are witnesses, not guaranteed shortest physical current paths. A null path in this diagnostic is not an open; the independent full-copper tests pass. Pad-centre distances are direct measurements from the saved native board.

## 2. The proposed mounting screws cannot reach the motor

The assembly source models a 6 mm under-head shaft, a 1.6 mm board and a 6 mm spacer. Reaching the motor face alone requires 7.6 mm before any thread engagement. In the native coordinates, the PCB top is Z=+0.8 mm, the screw tip is Z=−5.2 mm and the motor face is Z=−6.8 mm: **the screw tip stops 1.6 mm short of the motor face**.

The motor drawing documents four front M3 threads on 26 mm pitch, minimum depth 4 mm. It does not approve the proposed rear retention. Obtain the real rear mounting/retention geometry, choose fasteners using board + spacer + washer + required engagement, and check against bottoming. Do not choose a longer screw solely from this dimensional concept. The existing collision checks do not test engagement and cannot establish attachment.

Evidence: `assembly-preview.circuit.tsx`, `artifacts/top-assembly/assembly-build-verification.json`, and the manufacturer drawing `references/motor/14HM11-0404S.pdf`.

## 3. Confirm the intended feature behavior before freezing the PCB

- **RGB status is unavailable with PD power alone.** D_STATUS common anode connects to DATA_VBUS. The PD-powered logic supply does not create a programming-USB 5 V rail. If standalone motor status is required, change the LED supply/drive arrangement before ordering; firmware cannot create that missing supply.
- **Both coil shunts are used by A4988, but the MCU cannot read coil current.** SENSE1 connects only U_DRV.23/R_SA.1; SENSE2 connects only U_DRV.27/R_SB.1. No MCU input, amplifier or telemetry filter is connected. MCU-readable phase current would require a circuit change.
- PD voltage ADC and active-low POWER_GOOD are connected to the MCU. Motor current limit calculates to about 0.351 A nominal for the 0.4 A NEMA14 motor; this is not the NEMA11 0.67 A setting. The earlier 0.397 A tolerance budget is a screening estimate, not a qualified maximum.
- Microstepping is fixed at 1/16 by the hardware straps. AS5600 and its two bottom capacitors remain DNP. No motor-control application firmware is included.

## 4. Supplier requirements still need acceptance

- Order files contain 82 fitted TOP-side parts using 45 unique JLCPCB codes. BOM/CPL, DNP exclusions and order ZIP contents agree with the saved board. Live assembly stock and substitutions are not approved by this review.
- Three exposed-pad vias under U_MCU, U_PD and U_DRV require the specified filled, copper-capped, planarized process. Tenting is not an equivalent process. Obtain a quote for the actual four-layer service.
- The two USB4145-03-0070-C connectors have 0.7 mm shell stakes on a 1.6 mm PCB. The supplied paste omits their eight shell joints. Confirm an accepted soldering process for these joints, or qualify a suitable alternate stake variant; a standard bottom-wave operation cannot be assumed. See the existing `Through-Hole-Joint-Plan.csv`.
- Confirm every polarized device and pin 1 in JLCPCB's assembly preview, including the native CPL datum. The four native orientation suggestions are recorded; their placement DRC has zero errors/warnings, but they are not supplier pickup approval.
- Confirm four layers, 35 × 35 mm, 1.6 mm, F_Cu/In1_Cu/In2_Cu/B_Cu, ENIG, the requested copper/plating minima, and the exposed-pad stencil/via process. Via drill/pad minima remain 0.30/0.45 mm; supplier acceptance is required for the 0.075 mm nominal minimum annular ring. Use the supplier's approved panel/rail/fiducial plan if required.

Sources: [GCT USB4145 manufacturer drawing](https://www.mouser.com/catalog/specsheets/Global_Connector_Technology_usb4145.pdf); [JLCPCB via-covering processes](https://jlcpcb.com/help/article/pcb-via-covering); [JST SH catalog](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf). The JST header/SHR-04V-S mating combination is documented; procure a qualified 28-AWG pigtail and insulated motor-lead splices rather than assuming factory leads fit SH contacts.

## 5. Items already resolved and next acceptance steps

CH224A's 15 V resistor configuration, VHV feed, 50 V bypass part, PG pull-up and grounded exposed pad are recorded in the migration check. The old English VBUS-rating sentence is resolved by WCH V2.1 and is not a blocker.

Before ordering: correct the regulator/driver layout, resolve the intended RGB/current-telemetry behavior, complete a real retention/fastener design, and obtain the supplier's assembly/process/stock acceptance. After a layout change, regenerate the source, schematics, board, Gerbers, BOM/CPL and assembly, and rerun the checks on that new hash.

Then order a small prototype batch for bench bring-up. Firmware, USB flashing, PD negotiation/fallback, motor phase current, regulator startup/ripple, regeneration/TVS behavior, thermal operation and the real harness/mounting stack must be tested on prototypes before a production order. Bench testing is a post-prototype task, not something that can be completed before the first prototype exists.

This review does not modify the published PCB or release it for manufacture.
