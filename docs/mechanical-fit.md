# Service harness and carrier — 2026-10-09

The service revision retains a 35 × 35 × 1.6 mm PCB and top component assembly. Both USB mouths face +Y at X±7.0 mm, Y17.9 mm (14 mm pitch, 0.4 mm outside the outline). Lower PCB holes remain X±13,Y−13; upper holes are X±14.8,Y13, all Ø3.2 NPTH with Ø5.4 all-layer copper keepouts. These are carrier holes, not motor threads.

The exact motor drawing specifies **front** four M3 threads, 26±0.2 mm square, depth≥4 mm. Rear endcap screws remain untouched. The front-mounted carrier is an enlarged machined part, not a 35 mm square assembly. Its front plate is 49.2×36.4×4 mm, motor clearance holes Ø4.1±0.05, pattern tolerance±0.05, and locating pilot bore Ø22.15±0.05 mm with a motor-face root relief Ø23.4±0.05 ×0.40±0.05 mm deep for the documentedØ22+0/−0.052mm motorpilot (maximumradialplay0.126mm). Four M3×8 ISO4762 screws with Ø7/Ø3.2×0.5 washers give a bounded 3.2..3.8 mm motor engagement. Verify actual screws/washers and thread depth without bottoming. Host threads are four M3 at X±21.6,Y±13, usable depth6 mm; host screws must engage4.5..5.5 mm. Host face is8 mm ahead of the motor front, leaving about14.9..17.1 mm usable shaft projection. Host structure needs the front-fastener access and shaft opening; see the current STEP/dimension drawings and computed envelopes. Carrier material6061-T6/T651; strength, fatigue, torque, vibration and thermal effects remain qualification items.

**Motor connection:** J_MOTOR is JST **B4B-PH-K-S(LF)(SN)**, JLCPCB **C131334**, keyed friction-lock vertical PH header. Mate **PHR-4** with four **SPH-002T-P0.5S** contacts. JST specifies AWG30..24 and insulation OD0.8..1.5 mm for these contacts; rating2A atAWG24, operating−40..105°C including temperature rise. Friction retention is not a positive latch; carrier strain relief is mandatory. Do not hot-unplug a driven stepper.

The original 2 mm solder holes were not treated as compatible. The fresh exact supplier import is retained, but its 1.0 mm native holes conflict with JST's Ø0.7 +0.1/−0 drawing. The reviewed manufacturer-derived wrapper uses pad pitch2.0 mm, finished bore0.75±0.05 mm and padOD1.6 mm. Inspect header insertion in a fabrication coupon; specify finished bore explicitly. Original supplier OBJ/STEP remains unchanged; the installed model separately trims solder tails to ≤0.8 mm below PCB underside. No claim that every active footprint/model is an unchanged supplier import is made.

| Pin | Wire | Winding | Driver |
|---|---|---|---|
| 1 | Black | A+ | A4988 OUT1A |
| 2 | Green | A− | A4988 OUT1B |
| 3 | Red | B+ | A4988 OUT2A |
| 4 | Blue | B− | A4988 OUT2B |

![Motor connection](motor-wiring.svg)

Always use the printed pin1 mark and continuity test; do not infer pin order from an arbitrary view of the loose housing.

**HAR-001:** Four Belden83004 AWG24(7×32) PTFE silver-plated copper extensions, nominalOD1.1 mm,200°C rating. Order color stock **83004 010100** black, **83004 005100** darkgreen, **83004 002100** red, **83004 006100** lightblue (100ft stock reels; cut to drawing path length plus crimp/splice allowance). Manufacturer installation/stationary minimum bend radius11 mm; modeled bends12 mm, upper transition curvature is separately screened. Measure OD and accept1.05..1.20 mm for this clamp. Motor lead gauge, OD and insulation-temperature rating are undocumented: measure the actual motor leads; **do not assume they fit PH contacts**. Terminate the extension with the proper JST crimp tool/contact specification; no solder-tinned conductors in crimp barrels. Retain the factory leads and join using HAR-002 supported solder-lap splices, separated and insulated individually, with150°C-rated qualified heat-shrink plus a protective sleeve. Actual lead metallurgy/strip length/lap process, insulation part and pull strength require qualification before fabrication release.

**HC-001 positive restraint:** Two-piece PEEK24×14×6 mm clamp, VMQ silicone50±5ShoreA linerOD11.0 with four Ø0.95±0.05 through bores at X±3.5,Y−42±1.3; two M2.5×10 screws into carrier crossbar. The accepted minimum wireOD1.05 versus boremax1.00 gives positive compression; qualify preload and pull strength without damaging insulation. The carrier boreØ10.0 clears the bundle. Provide the modeled12 mm service loop and at least10 mm plug withdrawal/gripping access; release clamp if extra slack is needed during service. Neither crimp nor clamp retention has been measured.

**INS-001:** Captured Nomex410 sheet35×40×0.51 mm, four Ø4.8 holes, retained by PEEK support collars; no adhesive near hot motor. Procurement certificate must establish≥150°C continuous material suitability; certificate is not yet available. **INS-002:** Four PEEK lower supports1 mm,OD4.5/ID2.7 withOD6.5 collar, and four PEEK top washers0.5 mm,OD4.5/ID2.7. PCB M2.5×8 heads≤Ø4.5×2.5, nominal metal engagement4.9 mm. Solder fillet projection≤0.5 mm; trimmed header tails≤0.8 mm below PCB underside, covered by individually fitted≥150°C tail insulation. Modeled tail insulation/barrier gap0.59 mm, remaining0.34 mm after explicit0.15PCB/0.05carrier/0.05sheet allowances. Inspect and reject excess solder or protrusions. Sheet/PEEK are barriers, not a substitute for a gap/abrasion check at every exposed feature.

The STEP includes the header, drawing-derived PHR/contact installation envelopes, wire paths, tails, insulation, clamp, screws and motor. Factory internal key/spring CAD, detailed crimps/threads and measured tolerances are absent; they require actual parts. Factory lead/splice integration is an explicit unresolved gate, not an invented exact motor harness model.

**Actual selected cables:** PD **Tensility10-06137**, USB-C↔C3 m,20V3A,USB2; DATA **Tensility10-06139**, USB-A↔C1 m,USB2. Manufacturer PDF and original illustrative full cable STEP are retained. Extracted exact C-end geometry is transformed from the native shoulder datum; full native CAD is retained. Body width12±0.5 mm makes the former10.6 mm pitch unsound. At14 mm pitch the two12.5 mm maximum bodies have1.5 mm nominal separation,1.3 mm after±0.1 mm placement per port. Reserve body length32.5 mm and height7.6 mm; CAD height7.378 mm exceeds PDF7.3 mm maximum, so resolve supplier/sample discrepancy. Body shoulder registration and simultaneous insertion require a physical test.

CableOD3.8±0.15 mm,UL21104,80°C; keep this corridor within cable temperature limits. CAD reserves5 mm straight cable beyond the maximum body andR30 mm bend. No manufacturer minimum bend/fatigue radius was found; R30 is a host-space reservation, **not a verified cable bend-life rating**. Host must leave both insertion corridors clear and allow the positive-Y bend envelope. The installation STEP/checks show simultaneous plug envelopes and cable paths. Fitted components remain on top; visible top PD/15V andUSB/DATA labels occupy the clear center strip beside the actual mouths; full function and motorpin labels remain on the bottom/assemblydrawings.

## Assembly and service order

1. Fabricate from the current audited ZIP with the explicit finished-hole and filled/capped via requirements below. Compare supplier pickup/rotation preview with assembly drawings; no automatic placement convention is presumed verified.
2. Reflow top SMT components using the reviewed stencil; inspect polarity/pin1 and QFN joints/X-ray. No bottom component assembly. Manually solder USB shell slots and then J_MOTOR; trim tails and inspect both sides.
3. Crimp and continuity-test HAR-001/PHR-4 off-board, including each winding pair and color/pin mapping. Qualify HAR-002 connection to measured factory lead stock; individually insulate/stagger splices and pull-test them.
4. Attach carrier to documented front motor threads using M3×8+0.5mm washers; verify bounded engagement/no bottoming. Never loosen rear endcap screws. Host mounting uses independent outside M3 threads and needs access to the front hardware.
5. Capture INS-001, fit PEEK lower supports, seat PCB, fit PEEK top washers and M2.5×8 screws. Inspect all solder/metal/insulation clearances; do not tighten through an unseated support or use oversized conductive washers.
6. Mate PHR-4 while gripping housing, retain the12 mm loop, fit HC-001 liner/clamp and tighten to the qualified preload. Test cable pull without loading header. Install both USB cables and verify removal/access/bends. On service power down and discharge VM, release restraint if required, grip housing and withdraw vertically≥10 mm; never pull on wires or unplug with outputs energized.

Current exact nominal/tolerance screens and computed envelopes: [mechanical review](../artifacts/mechanical/mechanical-review.json), [harness review](../artifacts/mechanical/service-harness-review.json), [mounted STEP](../artifacts/mechanical/mounted-front-carrier.step.zip). Hardware fit is unperformed.

## Reference and host envelope

The public [imrishabh18 reference](https://tscircuit.com/imrishabh18/rp2040-motor-controller) uses the same top-entry PH housing concept. Its NEMA17 tie-screw mounting does not qualify NEMA14 rear threads. The exact reference README and comparison hashes are retained inreferences andjst-reference-comparison.json.

The complete nominal reserved motor/carrier/harness/two-cable envelope is 49.20 × 157.48 × 102.77 mm (X/Y/Z). Bounds relative to PCB midplane: X[-24.602,24.602], Y[-70.082,87.399], Z[-60.211,42.559]. Positive Y includes the reserved USB cable bend; negative Y includes the separate factory-lead loop. Host space must include these bounds plus manufacturing tolerances, cable motion and installation/removal access. Factory lead and splice integration remain physical qualification gates.

## Remaining exact-model discrepancy

PHR-4 external drawing dimensions are9.8×4.5×6.85mm; the model uses that outside envelope and1.5×2.08×5.7mm contact envelopes. Internal keys/springs are not factory CAD. The retained supplier header STEP has0.6mm square posts (0.849mm diagonal), incompatible with JST recommended0.7..0.8mm finished holes and producing0.0514mm³ modeled substrate penetration. This is a **known generic supplier-model discrepancy**, not proof that a real JST header cannot fit and not a passed exact-post CAD check. Do not enlarge the manufacturer drilling to match generic CAD or hide this collision. Obtain exact factory post dimensions/CAD or confirm real header/coupon fit before closing mechanical qualification.

Final tolerance correction: use the22.15±0.05mm locating bore and4.1±0.05mm front screw clearances. Pilot radialplay≤0.126mm +conservative0.354mm pattern mismatch isbelow0.525mm minimum screw clearance. Keep extension/splice ends atY≤−19.5mm, allowing motor/pilot/machining/wire variation; exact bounds are in the final mechanical review.

HAR-002 factory lead routing now continues the four actual native-CAD stub endpoints (modelOD0.945226mm) through a separate12mm-radius loop to the insulated splice envelopes. CAD-derived stock diameters/colors do not establish actual lead gauge/material; continuity and stock/bend/temperature/pull qualification remain required. Trim supplied300±10mm leads only after measuring the drawing path and retaining stripping/lap slack. Splice insulation candidate isTE RaychemRT-375-1/8-X with required150°C certificate and qualified recoveredassemblyOD≤2.8mm. HC-001 now24×14×6mm, linerOD11mm, borecentersX±3.5/Y−42±1.3, carrierboreØ10mm; seat bottomZ−2.8mm flush with crossbar and useM2.5×10 screws with4mm nominal metalengagement.

Final bounded clearance screen is in `artifacts/mechanical/service-tolerance-review.json`; all stated placement/routing/machining allowances are assembly requirements, not measurements. Complete harness/carrier drawings are in `artifacts/assembly/harness-carrier-drawings.pdf`.
