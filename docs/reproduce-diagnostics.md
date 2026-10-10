# Reproduce the diagnostic hardware review

Use the existing checkout; no worktree is needed. Pinned Bun/tscircuit/CLI and the repository lockfile are authoritative. The CAD/CAM Python environment requires CadQuery, Shapely, Gerbonara, PyGerber, CairoSVG, Matplotlib and pypdf. Browser checks use Playwright and Chromium. Current versions are recorded in manufacturing/software-versions.json.

`index.circuit.tsx` is the source entry. The final manually reviewed copper is saved in `artifacts/board.circuit.json` and byte-identical `index.circuit.json`; source-only autorouting does not reproduce that copper. `assembly.circuit.tsx` is a separate installed mechanical scene.

```sh
npm ci
npm run source:check
npm run typecheck
npm run build
/workspace/.routing-venv/bin/python scripts/verify-connectivity.py
npm run check:copper
npm run export
/workspace/.routing-venv/bin/python scripts/service-release-drawings.py
npm run check:manufacturing
/workspace/.routing-venv/bin/python scripts/inspect-via-paste.py
npm run shorts
python3 scripts/check-service-cli.py
python3 scripts/audit-functional-schematic.py
/workspace/.routing-venv/bin/python scripts/export-a4-pdf.py
python3 scripts/check-a4-browser.py
/workspace/.routing-venv/bin/python scripts/report-presentation.py
/workspace/.routing-venv/bin/python scripts/rebind-mechanical-review.py
/workspace/.routing-venv/bin/python scripts/rebind-assembly-assets.py
npm run assembly:build
npm run assembly:check
python3 scripts/check-assembly-browser.py
```

Run dependencies in order and freeze the saved board while checking/exporting. Full CAD regeneration uses review-mechanical.py and assembly:assets when physical geometry changes; metadata/copper rebinds strictly prove the full native physical frame and exact mounted STEP/mesh hashes. Do not update hash bindings to bypass a changed geometry check.

Routing history: native tscircuit was tried first; official FreeRouting2.0.1 followed where fixed legacy geometry blocked it, followed by explicit hand-selected copper repairs. The scripts named manual-diagnostics-* contain literal reviewed coordinates, not path-search routers. Native/FreeRouting reports and seed snapshots are diagnostics, not acceptance evidence. Seed-import helpers read exact Git baseline commits via diagnostics_baseline.py without /tmp dependencies. Historical routing steps require their recorded intermediate inputs; do not run them against the final saved board as a claimed idempotent build. Power pours must be normalized with holeless-pour-export.py if an actual CAM/source audit detects native clear-polarity erasure, then all changed-source checks/export must be repeated.

No firmware, measurements, ordering or publication is performed by these checks. Real hardware, supplier process/pickup acceptance and all qualification gates remain mandatory.
