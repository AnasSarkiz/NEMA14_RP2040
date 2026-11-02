# WAGO rotation trial

The active V2 layout remains at commit `83664be`. Only the terminal was rotated
in the isolated trial; the board and surrounding components were held fixed.

| Orientation | Result |
|---|---|
| Current, 0° | Fits the existing placement; wire openings face the bottom edge. |
| 90° / 270° | No collision-free location exists in the unchanged placement, even before screw-head/access checks. A new placement is required. |
| 180° | The terminal can occupy the same rectangle after adjusting its anchor. Native generation and independent placement checks pass, but the openings face inward. tscircuit adds a connector-access orientation warning. |

The sideways example in the [comparison](../artifacts/v2/rotation-study/comparison.svg)
is the least-collision outward-facing 270° candidate on a 0.25 mm anchor grid,
retaining the full courtyard and screw-head envelopes. It overlaps 19 component
courtyards, including J_DATA. This is an illustration, not an accepted placement.
The fixed-layout no-fit result uses continuous rectangular exclusion regions;
it does not prove that a complete redesign is impossible.

[180° native 3D preview](../artifacts/v2/rotation-study/half-turn-3d.png) ·
[180° placement audit](../artifacts/v2/rotation-study/half-turn-placement-verification.json) ·
[Rotation evidence](../artifacts/v2/rotation-study/rotation-screen.json)

The half-turn has zero courtyard/edge/proximity errors, but that does not qualify
wire or screwdriver access. Keep the current outward-facing orientation until
a redesigned sideways layout is justified. Both layouts remain unrouted and
unsuitable for ordering. V1 and the public package are unchanged.

Reproduce the trial with:

```sh
/workspace/.routing-venv/bin/python scripts/study-v2-motor-rotation.py
bun scripts/preview-v2-motor-half-turn.tsx
/workspace/.routing-venv/bin/python scripts/study-v2-motor-rotation.py
/workspace/.routing-venv/bin/python scripts/verify-v2-placement.py \
  --source artifacts/v2/rotation-study/half-turn.circuit.json \
  --output artifacts/v2/rotation-study/half-turn-placement-verification.json
python scripts/make-v2-portable-viewer.py \
  --source artifacts/v2/rotation-study/half-turn.circuit.json \
  --output /tmp/NEMA14-V2-half-turn-viewer.html \
  --notice '180° terminal trial · Wires face inward · Unrouted · Not for ordering'
```
