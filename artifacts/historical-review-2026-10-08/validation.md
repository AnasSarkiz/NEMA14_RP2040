# Saved-board validation

Run `npm run typecheck`, `npm run source:check`, `npm run build`, `npm exec -- tsci check artifacts/board.circuit.json`, `npm exec -- tsci check schematic-placement artifacts/board.circuit.json`, `npm run export`, and `npm run shorts`. Source compilation writes its separate unrouted artifact; build/check/render use the saved delivery copper. `scripts/sync-presentation.py` merges source/schematic metadata with assertions that saved PCB records and physical pin/net identities are retained.

`artifacts/validation/` contains actual command outputs. `artifacts/drc-report.json` contains full checks including power/ground pin attributes. Passive connector/crystal footprints are classified by physical role for ERC. `artifacts/physical-connectivity.json` independently checks the copper islands with Shapely geometry. Gerber shorts are checked on every copper layer at 100 pixels/mm. These are software checks and do not establish physical flashing, assembly, rear fit or thermal behavior.

## Browser schematic review

Run `python3 scripts/schematic-review-ui.py` for a read-only browser UI that displays native tscircuit A4 SVG pages beside actual `tsci check schematic-placement` and DRC findings. The browser review visits every numbered A4 page; screenshots and its result JSON are in `artifacts/validation/`.

The standalone tscircuit IDE was also launched. In this environment its PCB pane cannot obtain a WebGPU adapter, and the Schematic tab is disabled for the saved circuit-JSON selection. The review UI provides the native SVGs and CLI analysis without requiring GPU access; it is a project review tool, not the IDE's disabled schematic analyzer pane. External telemetry/CDN requests blocked by the cloud allowlist are recorded as environmental limitations.

See [USB programming](usb-programming.md). All fitted components now have exact supplier imports and OBJ/STEP assets; consult the reference-level import report.

## Final native CLI input and advisory results

The latest actual `tsci check netlist`, `pin_specification` and `source` checks on `index.circuit.tsx` exit 0. `tsci check placement` on the source JSON exits **1**, reporting **two courtyard overlaps and seven 180° orientation suggestions**, while its placement DRC summary reports **0 errors and 0 warnings**. Exact command/output/source binding is in [native-cli-final/results.json](../artifacts/validation/native-cli-final/results.json); the advisory result is retained, not rewritten as a pass.

The reported overlaps are J_BOOT/U_ESD (0.5 mm) and C_VM_SENSE/J_DEBUG (0.12 mm). J_BOOT/J_DEBUG are bare PCB contacts; automatic rectangular courtyard overlap is evaluated against actual native pad clearance, fitted STEP bodies and Ø0.5 mm top probe access. Native physical checks provide that separate geometry/access evidence, and actual pad/copper/CAM checks remain mandatory after any repair. No fitted body or access is assumed safe from the generic-box analysis alone. Airwire suggestions rotate C_IO10, C_IO22, C_IO42, C_FLASH, R_RUN, R_VM_BLEED and D_TVS; current actual routed paths, physical pads and final CAM determine connectivity instead of unrouted airwire orientation heuristics. No blanket zero-findings or official placement CLI exit 0 claim is made.
