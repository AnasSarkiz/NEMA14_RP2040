# NEMA14 assembly preview and fitted-side policy

The default tscircuit 3D preview is `assembly.circuit.json`: the complete qualified PCB plus a motor dimensional concept, four proposed screws, four proposed spacers and fixed motor leads with one board-end JST-SH plug. `index.circuit.json` and `artifacts/board.circuit.json` remain the qualified manufacturing board. **The preview does not establish rear-motor compatibility or physically qualified assembly.**

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

The source uses `assembly.device`, `assembly.motor`, board `mountedTo`/`mountGap`, and native `assembly.part` JSCAD records for hardware, fixed motor leads, insulated splices and the board-end plug. The installed `assembly.cable` implementation requires a connector on both ends and infers the PCB plug position from a generic header height. It cannot faithfully represent this motor’s bare leads; this preview therefore supplies the routed conductors and exposed plug as native assembly parts. The PCB stays at Z=0; its lower face is −0.8 mm. The model backface is −6.8 mm, leaving a nominal 6 mm gap. Hardware centres share the PCB's exact hole coordinates. The builder copies all qualified records verbatim and appends mechanical records only; no rerouting, footprint substitution or electrical remapping occurs.

Official references:

- https://docs.tscircuit.com/elements/assembly-motor
- https://docs.tscircuit.com/elements/assembly-cable
- https://docs.tscircuit.com/elements/assembly-part
- https://docs.tscircuit.com/guides/tscircuit-essentials/mounting-3d-models

`mountedTo` positions parts; it does not create fasteners or perform collision checking. The motor is rotated 180° around its square mounting pattern so its local −Y wire outlet faces the board’s +Y edge, beside J_MOTOR. The four fixed leads take a short loop outside the USB insertion envelope to the seated JST plug. After shortening the factory leads, join them to a 28-AWG precrimped JST-SH pigtail through four individually insulated splices. The motor drawing specifies 300 ±10 mm bare leads without a wire gauge; do not assume they fit SH contacts directly. SSH-003T-P0.2-H accepts AWG 32–28 with 0.4–0.8 mm insulation OD. The chosen pigtail model uses 0.6 mm OD; factory-lead and splice dimensions remain sample-dependent visual envelopes.

The actual board header is BM04B-SRSS-TB(LF)(SN), mating with SHR-04V-S and SSH-003T-P0.2-H contacts. JST’s [SH catalog](../references/jst/SH-connector.pdf), pages 1–3, specifies 1 mm pitch, a 5 × 2.8 × 5 mm housing and 6.3 mm total mated height above the PCB. The full housing bottom is 1.3 mm above the PCB surface. The preview renders only its exposed upper portion above the unchanged supplier header; concealed stem, contact and latch details are not invented.

The native header STEP contact regions lie at local X=0,1,2,3 / Y=0.35 mm. Their exact CAD origin correction and board rotation determine the four wire-entry locations. Only pins 1–4 define the electrical axis; the two mounting tabs are excluded. The old inferred pin-1 vector included those tabs and rotated the cable housing. The old cable also began above the header instead of at the seated mating height. Both assumptions are removed.

Factory and pigtail wiring is pin 1: black=A+, pin 2: green=A−, pin 3: red=B+, pin 4: blue=B−. Each rendered conductor is independently checked against its own native header contact region and the corresponding PCB net. There is no socket or detachable connector on the motor. The motor’s customized NEMA body remains a dimensional illustration; rear retention, rear shaft, encoder magnet and airgap remain unverified.

`scripts/check-harness-connection.py` verifies the actual rendered conductor endpoints, four-contact order, native STEP occupied contact regions, documented seating height, housing roll and pigtail/contact specification. `scripts/check-assembly-fit.py` checks each individual conductor and insulated splice against native supplier STEP geometry, the PCB, hardware, USB insertion envelopes and screwdriver columns. It also checks wire-to-wire separation. Only the small fixed-lead case feedthrough is intentional; the simplified motor envelope does not contain factory wire bores. These nominal checks do not qualify crimp workmanship, latch tolerances or physical motor retention.

## Reproduce and inspect

- `npm run assembly:build`: regenerate the native assembly JSON and electronic-pose preservation proof.
- `npm run assembly:check`: verify pin mapping and seated mating geometry, then check conductor/hardware clearances.
- `npm run assembly:export`: export native 3D GLB; model downloads are recorded with hashes.
- `artifacts/top-assembly/assembly-viewer.html`: interactive local viewer, alongside `assembly-viewer.js` and `assembled.glb`; serve the directory over HTTP.
- `artifacts/top-assembly/assembly-complete.png` and `assembly-top.png`: inspected renders.
- `assembly-build-verification.json`, `assembly-fit-verification.json`, `assembly-publication-verification.json`: current proofs.

Before ordering, obtain the rear motor drawing and a real retention design, confirm all hardware/harness SKUs and supplier PCBA processes, and qualify the physical assembly and operating prototype. A collision-free dimensional concept is not a completed rear mounting design.
