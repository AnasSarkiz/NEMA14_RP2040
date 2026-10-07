# Saved-board validation

Run `npm run typecheck`, `npm run source:check`, `npm run build`, `npm exec -- tsci check artifacts/board.circuit.json`, `npm exec -- tsci check schematic-placement artifacts/board.circuit.json`, `npm run export`, and `npm run shorts`. Source compilation writes its separate unrouted artifact; build/check/render use the saved delivery copper. `scripts/sync-presentation.py` merges source/schematic metadata with assertions that saved PCB records and physical pin/net identities are retained.

`artifacts/validation/` contains actual command outputs. `artifacts/drc-report.json` contains full checks including power/ground pin attributes. Passive connector/crystal footprints are classified by physical role for ERC. `artifacts/physical-connectivity.json` independently checks the copper islands with Shapely geometry. Gerber shorts are checked on every copper layer at 100 pixels/mm. These are software checks and do not establish physical flashing, assembly, rear fit or thermal behavior.

## Browser schematic review

Run `python3 scripts/schematic-review-ui.py` for a read-only browser UI that displays native tscircuit A4 SVG pages beside actual `tsci check schematic-placement` and DRC findings. The browser review visits every numbered A4 page; screenshots and its result JSON are in `artifacts/validation/`.

The standalone tscircuit IDE was also launched. In this environment its PCB pane cannot obtain a WebGPU adapter, and the Schematic tab is disabled for the saved circuit-JSON selection. The review UI provides the native SVGs and CLI analysis without requiring GPU access; it is a project review tool, not the IDE's disabled schematic analyzer pane. External telemetry/CDN requests blocked by the cloud allowlist are recorded as environmental limitations.

See [USB programming](usb-programming.md). All fitted components now have exact supplier imports and OBJ/STEP assets; consult the reference-level import report.
