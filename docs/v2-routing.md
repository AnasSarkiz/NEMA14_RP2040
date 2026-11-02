# V2 initial routing draft

The mistaken rotation trial was reverted in `ac234d7`. The WAGO 250-204 remains
outward-facing. Routing work is isolated from the ordered V1 files and from the
verified V2 placement seed.

The first saved routing candidate contains **343 trace sections and 16 through
vias (0.6 mm pad / 0.3 mm drill)**. Of 70 physical net groups, **18 are fully
connected and 52 remain open**. This is an unfinished draft, not order files.

[Top copper SVG](../artifacts/v2/routing/top.svg) ·
[Inner2 copper SVG](../artifacts/v2/routing/inner2.svg) ·
[Bottom copper SVG](../artifacts/v2/routing/bottom.svg) ·
[Standalone routing viewer](../artifacts/v2/routing/NEMA14-V2-routing-viewer.html)

## Placement refinement

Both 27 Ω USB series resistors are now within 4.5 mm Manhattan distance of their
RP2040 USB pins and within 2.5 mm of each other. A local placement solve moved
21 components while retaining full supplier courtyards, screw-head envelopes,
all fitted parts on top and every existing proximity constraint. This improves
the starting placement; it does not establish a finished USB pair or clock layout.
See [the physical moves](../artifacts/v2/routing/placement-refinement.json).

The updated source passes 33 topology checks, native schema checks, native
schematic placement checks, typechecking and all 65 independent proximity checks.
All 338 non-motor pin/net assignments match the pre-WAGO V2 baseline; all 342
connected physical pin/net assignments, including the WAGO poles, are preserved
between the current placement seed and routing candidate.

## Routing checks

The [independent physical audit](../artifacts/v2/routing/physical-routing-audit.json)
finds **zero foreign-net shorts, clearance violations, board-edge violations or
mount/NPTH copper overlaps in the present copper**. It also finds the 52 open
nets, so the audit correctly fails. Rounded pad boundaries use polygonal geometry;
final Gerber and drill qualification remains required.

The [native DRC](../artifacts/v2/routing/native-drc.json) reports **144 errors**:
135 unconnected-port errors and nine trace-connection/dangling-end errors. These errors
are retained and appended to the routing viewer's display data. They are not
suppressed or reclassified as a passing DRC result. The raw candidate remains
unchanged for independent checks.

The saved placement preview (`index.circuit.json` and the main V2 HTML) remains
the unrouted seed. The routed candidate and its diagnostics live under
`artifacts/v2/routing/`. SHA-256 values bind the source, DSN, SES, candidate and
receipts in [routing-status.json](../artifacts/v2/routing/routing-status.json).

## Router and reproduction

The initial native tscircuit autorouter hit its iteration limit and produced no
copper. The fallback uses the pinned Freerouting 2.0.1 JAR and actual supplier
pad contours, plated holes, restored USB locating slots and circular mounting
keepouts. Routing uses top, inner2 and bottom; **inner1 has no ground fill yet**.

This Freerouting version's batch loop reads `stop_pass_no`, while the legacy
`-mp` option only changes `maxPasses`. The runner explicitly sets
`--router.start_pass_no=1 --router.stop_pass_no=2`; the saved session comes from
that bounded two-pass run. It loads no V1 routing seeds or copper.

```sh
npm run build:v2
npm run route:v2
npm run check:v2:routing
npm run check:v2:routing:native
npm run render:v2:routing
```

`route:v2` saves the candidate and both failing audit receipts; it exits nonzero
while opens or DRC errors remain. More passes can be requested with
`npm run route:v2 -- --passes 5`. No command above publishes or exports order files.

Next work is to close the open nets, refine USB pairing/reference, oscillator,
Kelvin shunt branches and power loops, add ground fill/stitching, and complete
native/independent CAM checks. Motor-wire fit, shunt sourcing and hardware
calibration remain open. Manufacturing and public publication stay blocked.
