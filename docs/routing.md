# Saved copper

`artifacts/board.circuit.json` is the reviewed delivery layout. `npm run build` renders and checks it without rerouting. The registry preview also uses this saved file. No CH32 copper is reused.

The pinned tscircuit 0.0.2759 local autorouter was attempted first. The four-layer run completed its process but returned no traces and 227 errors, including `TraceSimplificationSolver cannot preserve endpoints for duplicate route "source_net_12"`. The diagnostic result and log are retained separately; they are not delivery copper. An earlier two-layer attempt exceeded 120 seconds.

The permitted freerouting 2.0.1 fallback received actual pad geometry and explicit MCU/driver fanouts. Its archived `fixed8-input.dsn`, identity map, seed copper, unrouted input and `fixed8-board.ses` belong together. SES omits fixed wiring, so the importer restores it from the seeds. The importer also maps In2.Cu to inner2 and restores through-vias to all four physical layers. Plated component holes obstruct all routing layers. Four screw-head keepouts apply through the stack.

The final stack is top / inner1 ground / inner2 signals / bottom. Inner1 carries no signal traces. Ground fills use 0.20 mm clearance and 0.35 mm board-edge margin. Ordinary vias are 0.50/0.25 mm; the two C_IO22 escapes use 0.40/0.20 mm. Only three grounded exposed-pad thermal vias are allowed inside pads. All component assembly is on top. Through-hole joints are hand soldered; generated paste openings over drills and all bottom paste are removed.

The last local changes rotate C_IO22 to 270 degrees, replace its ground connection and complete USB CC2. `saved-copper-adjustments.json` stores every copper deletion/insertion relative to the imported session. Replaying those changes and refilling ground reproduced every final record exactly:

```sh
python3 scripts/import-session.py fixed8
python3 scripts/apply-saved-adjustments.py
/workspace/.routing-venv/bin/python scripts/fill-ground.py
npm run build
/workspace/.routing-venv/bin/python scripts/verify-connectivity.py
npm run export
npm run shorts
python3 scripts/report.py
```

The final layout has 479 traces, 0 native DRC errors, all 48 named nets physically connected, and no Gerber shorts detected at 100 pixels/mm across all copper layers. The 31 retained warnings concern source pin attributes and power/ground metadata. Check reports and SHA-256 hashes apply to the saved layout only.

For a new routing experiment, render the source, run `reserve-router-fanouts.py` and `export-router.py`, then invoke the checksum-verified Java router on the resulting DSN. Those operations overwrite the archived router inputs; work on a copy and recheck the result. `npm run autoroute` saves tscircuit diagnostic copper separately. A fresh routing run can change paths and is not automatically a validated release.

DRC, physical connectivity and raster short checks do not establish USB signal integrity, switch-mode power performance, rear fit or production readiness. Firmware and hardware bench validation remain outstanding.
