# Motor and rear-board mechanical review

The controller PCB is **35 × 35 × 1.6 mm**, with fitted parts on the side facing away from the motor. This review uses every fitted component's unchanged, hash-verified JLCPCB STEP model at the saved circuit JSON CAD position, origin correction and rotation. The three bare PCB interfaces have no invented component bodies. The substrate includes the actual mounting holes and connector plated slots. Routed via bores, copper and solder fillets are not represented in the mechanical STEP assembly. View colors are illustrative material/component classes, not qualified supplier finishes.

## Exact motor evidence

The selected motor is **STEPPERONLINE 14HM11-0404S**, not a generic NEMA14 substitute. Its official cached STEP and full drawing are retained in `references/motor/14hm11-0404s/`, with provenance and SHA256. STEP SHA256 is `959f43e95b7840beae5ffbd56e997e23c5004a1b09e16b7caa40400296e46281`; drawing SHA256 is `d1cc1604b89947f6f0c2018d2b59c36194bc5e949796cd9af2d99be4effd4305`.

The drawing specifies a **35.2 mm maximum square body, 28.2 mm maximum body length, Ø5 mm front shaft with 24 ±1 mm projection**, and four **front M3 threads on a 26 ±0.2 mm square, minimum 4.0 mm thread depth**. STEP coordinates put the front mounting datum at Z=0, rear body at Z=28.2, and front shaft end at Z=−24. The model is one valid solid. Its blended surfaces give an XY envelope around 35.211 × 35.21 mm, a small CAD bounding-box deviation from the 35.2 mm drawing maximum; use the drawing for procurement. The STEP header dates to 2018, whereas the drawing revision record dates to 2025; physical motor revision compatibility is not established by the cache.

**Direct rear fastening remains unsupported.** Rear STEP features at X/Y=±13 are recessed endcap fasteners and a central bearing recess. Their matching apparent pitch does not establish independent, usable rear threads. Do not remove endcap screws or drill the motor. The four PCB holes are adapter mounting holes; they do not authorize direct fastening to the motor rear.

Lead identification is **A+ black, A− green, B+ red, B− blue**. The drawing specifies 300 ±10 mm leads; the STEP only contains a short visual lead stub exiting the −Y side near native Z≈24.25. The central −Y wire corridor remains open in the proposed carrier. Harness routing, solder-pad strain relief and bend radius need a physical sample.

![Exact official motor rear STEP; endcap features highlighted](../artifacts/mechanical/motor-rear-detail.png)
![Exact official motor front STEP; qualified front mounting drawing](../artifacts/mechanical/motor-front-detail.png)

## Separate front-flange carrier candidate

A separate machined carrier holds the PCB behind the motor using the motor's documented **front** M3 threads. It does not alter either board's hole pattern or the motor CAD. Proposed material is 6061-T6/T651 aluminium; it is a prototype candidate requiring load, heat, preload and installation testing.

| Feature | Proposed dimension |
|---|---|
| Front flange | 49.2 ×36.4 ×3 mm; Ø24 mm pilot opening |
| Front screw clearances | Four Ø3.8 mm holes, 26 mm square |
| Outside rails | Four 6 ×5 mm sections, X=±21.6 / Y=±13 mm |
| Rear returns | 13.85 ×5 ×4 mm, Z=−6.8..−2.8 mm |
| PCB supports | Ø4.5 mm bosses; upper support plane Z=−0.8 mm |
| PCB holes | Four Ø3.2 mm, 26 mm square, saved board geometry |
| Motor rear / front | Z=−8 / −36.2 mm in mounted assembly |
| Rear-to-PCB underside | 7.2 mm |
| Intended machining tolerance | ±0.05 mm, unqualified |

PCB fastener envelopes are **standard M2.5×6 socket cap, head ≤Ø4.5 ×2.5 mm, without an oversized metal washer**. Nominal engagement is 4.4 mm into a 6 mm through-tapped M2.5 support thickness. The existing Ø3.2 PCB hole permits 0.35 mm radial play: with the head radius 2.25 mm, the nominal head sweep is Ø5.2 mm, contained by the preserved **Ø5.4 mm circular keepout**. Machining/PCB tolerances, centering, preload and insulation still need verification. The supplier USB rectangular courtyard has conservative empty corner area that overlaps this circle; source excludes that narrow courtyard comparison only after exact unchanged native copper/body checks. Supplier footprints and the Ø5.4 mm head bounds remain unchanged. Routed copper must independently remain outside the circular keepouts. Front envelopes are M3×6, head ≤Ø5.5 ×3 mm and standard Ø7/Ø3.2 ×0.5 mm washer, giving nominal 2.5 mm motor-thread penetration within the drawing's ≥4 mm available depth. Generated cylinders represent bounded procurement envelopes; helical threads and actual purchased screws are not modeled. Nominal screw shanks overlap thread pilot bores intentionally to represent threaded engagement; those simplified mating overlaps do not establish thread/preload qualification. Carrier/front-motor and boss/PCB faces intentionally touch. Insulating washer/coating requirements, torque, retention and manufacturing tolerances need review before use.

The carrier uses front flange area and enlarges the motor assembly to 49.2 mm across X. It must fit the host machine and leave the front shaft usable; this is not a drop-in replacement for an existing flush front mounting.

Bare BOOT/debug/motor contacts remain PCB features with no invented fitted bodies. The report screens straight top access with a Ø0.5 mm probe at BOOT contacts and Ø1 mm probe at debug/motor contacts; this does not model a whole tweezers body, connector or final soldered harness. Use insulated fine tips and confirm actual programming/soldering-tool access. RP2040 BOOT probe centers are now **(13.85,9.1) and (15.35,9.1) mm**; both Ø0.5 mm straight top probe envelopes have no native-model intersections. The access plan below shows conservative measured native STEP bounding boxes and probe coordinates, not replacement component CAD.

Both native C165948 USB-C ports now face the **same +Y board edge**, with native PCB rotation 180° and supplier CAD rotation 0°. PD/data anchors are **X=−5.3/+5.3, Y=12.1499711 mm**; both mouth planes are **Y=17.5 mm**. Native footprint/CPL bbox centers are X=±5.3 / Y≈12.57501465 mm; supplier STEP body-bbox centers are X=±5.3 / Y=13.550 mm. These are distinct datums. The body center is **not** verified as the assembly-machine pickup point, and CAD origin correction is **not** JLC pickup calibration. Supplier pin 1/rotation interpretation still needs the actual JLC placement preview.

The native supplier footprints are unchanged. A focused rigid-transform screen verified the real shell and native pad copper against the full **Ø5.4 mm circular mounting keepouts** at X/Y=±13 mm: body-to-circle gap 0.530 mm, native outer-copper-to-circle gap ≥0.445342 mm, and body-to-swept Ø5.2 mm screw-head envelope (0.35 mm radial hole play) gap 0.630 mm. A conservative rectangular USB courtyard extends into unused circle-adjacent space; the narrow courtyard exception relies on this exact native body/copper proof, never on shrinking the imported footprint or mounting keepout. Final full-board poses and pad clearance are checked again below.

Each +Y port has a compact-cable procurement allowance of **30 mm insertion length ×10 mm maximum overmold width ×7 mm height**, centered Z=2.45 mm (supplier mouth-plane Z=0.08..3.22 mm plus PCB top datum 0.8 mm) and extending outward from Y=17.5 mm. The 10.6 mm center pitch leaves **0.6 mm between these two bounded compact overmolds**. The earlier 12 mm overmold allowance overlaps at this pitch (1.4 mm lateral overlap; 294 mm³ rectangular-envelope common volume) and is rejected. Actual two compact ≤10 mm cable MPNs/overmolds and simultaneous insertion remain **USER_REVIEW**. These boxes are engineering procurement bounds, not exact selected cable CAD. Confirm real dimensions, retention/insertion force and bending clearance before fabrication.

A provisional single-corner beam screen assigns an unqualified 20 N cable load to one 6 × 5 mm rail and one 5 × 4 mm return. With room-temperature aluminium E = 69 GPa, combined elastic deflection is about 0.084 mm; rail/return nominal bending stresses are 29.1/20.8 MPa. This excludes front-plate/joint flexibility, torsion, PCB flex, notches, screw preload/fatigue, hot-material strength and motor vibration. It is a dimensional sanity screen, not qualification or an allowable load rating.

## Evidence and findings

Final saved-board SHA256 is `d85469ebd8679aae5cb6dc012b8552db9f2bb5a4a3a459f8b5645419adfe31ea`. All **67 fitted components** have valid closed native supplier STEP solids and exact matching import hashes. The frozen physical-source audit is rebound to the final saved board with physical-fingerprint equality proof retained in the machine-readable report. Any later copper/metadata refresh must be rebound with `python scripts/rebind-mechanical-review.py`; a physical change requires a full rerun. Copper connectivity/DRC are separate checks.

Nominal native geometry has **zero component intersections, zero component gaps below 0.2 mm, zero PCB-head intersections, zero carrier intersections and zero compact USB-insertion-envelope intersections**. The lowest all-component PCB-head bounding-box separation after the 0.35 mm radial hole-play allowance is **0.395 mm**. Every native pad's outer copper clears all four Ø5.4 mm circles; the minimum is **0.284 mm at C_BULK**. Both unchanged supplier USB footprints clear these circles by **0.445 mm**, and connector bodies clear their circles by **0.530 mm**. These nominal checks exclude solder/placement tolerance and full routed copper, which needs its own keepout audit.

Both USB mouths lie at **Y=17.5 mm**, with centers X=±5.3 mm. The two compact 10 mm overmold envelopes have **0.600 mm nominal separation** and clear the carrier by **2.695 mm**. Rejected 12 mm overmold envelopes overlap by 1.4 mm (294 mm³ in this engineering box screen). Actual two-cable procurement/insertion remains **USER_REVIEW**. All BOOT/debug/motor straight top probe envelopes remain clear. USB tabs show only approximately 0.000030 mm³ residual intersection per port with the drilled substrate, attributable to micron-scale native CAD/slot geometry; physical insertion still requires a sample.

The separate manufacturer-maximum C_BULK envelope has **no potential component or fastener intersections**. Its left board-edge margin is **0.350 mm nominal / 0.150 mm after a 0.2 mm outline allowance**, before component-placement/solder tolerance. This narrow margin is not a guaranteed manufacturing fit. The nearest PCB head to that maximum envelope has a conservative remaining bounding-box margin of 0.900 mm after hole play.

C_BULK now uses **C178585 / Panasonic EEEFPV101XAP, 100 µF, 35 V, 6.3 × 7.7 ±0.3 mm**. Its exact unchanged native supplier STEP is only **5.82 mm tall**, so its world top is Z=6.62 mm; it is a short generic model and **does not reproduce the manufacturer's actual height**. Native import and hash identity establish provenance, not mechanical dimensional accuracy. This remains **USER_REVIEW**, with no silent replacement or stretching of the imported model.

![Native capacitor model and independent manufacturer maximum envelope](../artifacts/mechanical/bulk-capacitor-height-review.png)

The independent manufacturer-maximum envelope is **7.8 × 6.8 × 8.3 mm**, including D8 diameter/base tolerances, maximum lead span and an extra 0.3 mm vertical stand-off allowance. Its top can reach Z=9.1 mm above the board midplane. The report screens edge/PCB-head clearance and separately states remaining edge margin after 0.2 mm PCB-outline tolerance; placement/solder tolerances still require verification. The exact D8 dimensions and ordering row are in [Panasonic FP manufacturer data](../references/Panasonic-FP-2025.pdf), SHA256 `58f2ec610e03cbad28a61f8bc740521df5d03e27a6dfee92a583f2747b99c981`.

Complete native assemblies can exceed GitHub's 100 MB individual-file limit in uncompressed form (the RP2040 variant does). They are included as lossless ZIP archives; extract the contained STEP for a CAD viewer. No component model was simplified.

The machine-readable report binds the input board hash, each exact STEP/hash/transform, component intersections, near clearances, fastener envelopes, substrate penetration, carrier distances and USB insertion checks. Nominal intersections and tolerance/procurement issues must be resolved individually; a zero electrical DRC result cannot waive a mechanical finding.

- [Fitted board STEP](../artifacts/mechanical/board-fitted-components.step.zip)
- [Mounted motor + separate carrier + fitted board STEP](../artifacts/mechanical/mounted-front-carrier.step.zip)
- [Carrier-only STEP](../artifacts/mechanical/separate-front-carrier.step)
- [Fastener clearance envelopes](../artifacts/mechanical/fastener-clearance-envelopes.step)
- [Mechanical report](../artifacts/mechanical/mechanical-review.json)
- [Programming access plan](../artifacts/mechanical/programming-access-plan.svg)
- [Generated STEP reimport validation](../artifacts/mechanical/generated-step-validation.json)
- [Independent maximum capacitor envelope](../artifacts/mechanical/bulk-manufacturer-maximum-envelope.step)
- [Dimension drawing](../artifacts/mechanical/dimensions.svg)

![Programming access bounds and actual probe coordinates](../artifacts/mechanical/programming-access-plan.png)

![Top fitted board](../artifacts/mechanical/board-top.png)
![Bottom fitted board](../artifacts/mechanical/board-bottom.png)
![Fitted board isometric](../artifacts/mechanical/board-isometric.png)
![Mounted top](../artifacts/mechanical/mounted-top.png)
![Mounted bottom](../artifacts/mechanical/mounted-bottom.png)
![Mounted carrier isometric](../artifacts/mechanical/mounted-isometric.png)
![Mounted side view](../artifacts/mechanical/mounted-side.png)
![Mechanical dimensions](../artifacts/mechanical/dimensions.png)

Reproduce with `/workspace/.routing-venv/bin/python scripts/review-mechanical.py` from this project. It reads saved circuit JSON and supplier models; it never edits PCB source, routing or manufacturing files. Regenerate the supplementary bounds/probe plan with `/workspace/.routing-venv/bin/python scripts/render-mechanical-access.py`. Rerun on every saved placement/CAD change and bind the final output to the release revision. For changes confined to copper/metadata, `python scripts/rebind-mechanical-review.py` accepts the existing audit only when all physical inputs are proven identical; otherwise it rejects the refresh and requires a full rerun.

**Mechanical manufacturing release remains blocked** pending actual motor revision/fit, selected cable/fastener procurement, supplier CAD height mismatch, host front-flange compatibility, carrier strength/thermal/tolerance checks and prototype assembly. The proposed separate carrier removes the dependency on unknown rear mounting threads; it does not replace those qualifications.
