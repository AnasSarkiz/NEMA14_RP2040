# NEMA14 assembly preview and fitted-side policy

The default tscircuit 3D preview is `assembly.circuit.json`: the complete qualified PCB plus a motor dimensional concept, four proposed screws, four proposed spacers and one JST-SH harness. `index.circuit.json` and `artifacts/board.circuit.json` remain the qualified manufacturing board. **The preview does not establish rear-motor compatibility or physically qualified assembly.**

## Actual board and connectors

The PCB is 35 × 35 × 1.6 mm with four Ø3.2 mm NPTH holes at (±13, ±13), 4 copper layers and Ø0.30/Ø0.45 mm minimum via drill/pad. Both GCT USB4145-03-0070-C C5815189 ports are upright, on opposite edges with +Z insertion. The motor header is BM04B-SRSS-TB(LF)(SN) C160390, JST-SH 1 mm, mating housing SHR-04V-S. Connector placement centres in this qualified board are:

{
  "J_PD": [
    0.6000000000000001,
    15.149999999999999
  ],
  "J_DATA": [
    -4.6,
    -15.149999999999999
  ],
  "J_MOTOR": [
    -6.8500000000000005,
    12.850000000000001
  ]
}

The mechanical screen uses 10 × 7 × 30 mm USB plug envelopes and Ø6 mm tool access columns. The actual preview hardware uses Ø4 × 3 mm screw heads, M3 × 6 mm shaft envelopes and Ø5 × 6 mm spacer rings with Ø3.2 mm bores. Threads are not rendered. These are proposed dimensions, not an approved fastener SKU, thread engagement or rear attachment design. Tightening torque, retention, stack tolerances and real plug/tool fit remain unqualified.

All fitted electronic components are TOP. The AS5600 and two encoder capacitors on BOTTOM are DNP; no bottom assembly or rear shaft/magnet compatibility is implied. Bare TOP debug test pads remain unfitted.

## Documented tscircuit assembly workflow

The source uses `assembly.device`, `assembly.motor`, board `mountedTo`/`mountGap`, `assembly.part` for hardware and `assembly.cable` between the motor wireside and the actual `J_MOTOR`. The PCB stays at Z=0; its lower face is −0.8 mm. The model backface is −6.8 mm, leaving a nominal 6 mm gap. Hardware centres share the PCB's exact hole coordinates. The builder copies all qualified records verbatim and appends mechanical records only; no rerouting, footprint substitution or electrical remapping occurs.

Official references:

- https://docs.tscircuit.com/elements/assembly-motor
- https://docs.tscircuit.com/elements/assembly-cable
- https://docs.tscircuit.com/elements/assembly-part
- https://docs.tscircuit.com/guides/tscircuit-essentials/mounting-3d-models

`mountedTo` positions parts; it does not create fasteners or perform collision checking. Native cable paths do not avoid obstacles. `scripts/check-assembly-fit.py` separately checks the actual generated path with a conservative radius 1.8 mm envelope around the four 0.6 mm wires at 1 mm pitch, the mating-housing envelope, screws, spacers, USB plug envelopes and screwdriver columns against native supplier STEP geometry. The final wire entry into its own housing is intentional. Invalid native USB STEP solids use complete bounding solids as conservative over-approximations.

The 14HM11-0404S drawing provides body maximums 35.2 × 28.2 mm, 26 mm FRONT M3 hole pitch and a 24 × Ø5 mm shaft. The customized NEMA model is a dimensional illustration, not supplier-exact CAD. Rear threads, rear protrusions/shaft, encoder magnet and airgap are unverified. The motor-side JST model and chosen 60° local wire exit are proposed harness geometry; neither is established by the factory drawing. The supplier motor has bare leads. Factory coil colors are A+ black, A− green, B+ red, B− blue; the procedural cable colors are illustrative. The electrical connector contract remains pins 1:A+, 2:A−, 3:B+, 4:B−.

## Reproduce and inspect

- `npm run assembly:build`: regenerate the native assembly JSON and electronic-pose preservation proof.
- `npm run assembly:check`: run the actual path/hardware nominal collision check.
- `npm run assembly:export`: export native 3D GLB; model downloads are recorded with hashes.
- `artifacts/top-assembly/assembly-viewer.html`: interactive local viewer, alongside `assembly-viewer.js` and `assembled.glb`; serve the directory over HTTP.
- `artifacts/top-assembly/assembly-complete.png` and `assembly-top.png`: inspected renders.
- `assembly-build-verification.json`, `assembly-fit-verification.json`, `assembly-publication-verification.json`: current proofs.

Before ordering, obtain the rear motor drawing and a real retention design, confirm all hardware/harness SKUs and supplier PCBA processes, and qualify the physical assembly and operating prototype. A collision-free dimensional concept is not a completed rear mounting design.
