# Cloud startup

Use the existing `/workspace/NEMA17_Controller` and `/workspace/NEMA14_RP2040` checkouts. Install from lockfiles using `npm ci --legacy-peer-deps`; local scripts supply Bun. `scripts/cloud-install.sh` restores Python routing dependencies in `/workspace/.routing-venv`, verifies locked Git dependency source checksums and Freerouting 2.0.1. Retain TLS/checksum checks.

Run TypeScript, source compilation, saved-board build, native physical connectivity and all-layer Gerber shorts checks. The delivery has 351 trace sections/38 fitted supplier models on CH32 and 519 trace sections/61 fitted models on RP2040; DRC errors and warnings are zero. `npm run build` uses saved copper. `npm run autoroute` writes a separate diagnostic result and does not replace delivery copper.

Use `XDG_CONFIG_HOME=/workspace/.config` for authenticated CLI publication. Reuse configured authentication without printing secrets. Exact JLCPCB imports and OBJ/STEP assets are in `imports/supplier/`; CAD viewers load public GitHub URLs. Native A4 drawings have 9 CH32 and 13 RP2040 pages. The supplier report requires the routing Python environment: `/workspace/.routing-venv/bin/python scripts/report-presentation.py`.

`npm run dev -- --port 5173` starts the saved-board preview. `python3 scripts/schematic-review-ui.py` starts the read-only native A4/CLI findings review UI. Check local HTTP endpoints internally; share the public project links. The official IDE saved-JSON schematic pane is disabled and WebGPU is unavailable here. Restart servers in a fresh task.

Both designs remain unassembled prototypes. Rear-motor fit, physical USB flashing, PD/thermal testing and firmware implementation remain outstanding. The manufacturer drawing gives front mounting only; four 26 mm-pitch holes are for an unverified rear adapter. The CH32 GitHub identity remains AnasSarkiz/NEMA17_Controller because its requested rename returned HTTP 403. Environment draft saving does not activate its configuration; review/save/publish in environment settings. Fresh-task restoration has not been independently tested.

The inside-board JST routing repair uses `scipy==1.18.1` from `scripts/requirements-router.txt` for its nearest-goal routing heuristic. Reuse the saved accepted copper; source:check builds the separate unrouted source artifact. Any placement change requires a fresh native CAD/mechanical review, rerouting and complete source/actual-CAM gates.
