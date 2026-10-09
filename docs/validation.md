# Current validation — RP2040, service revision

The requested exact local commit `97d4248` was inspected before editing. The frozen delivery is `index.circuit.tsx` → `src/board.tsx`, with accepted copper in `artifacts/board.circuit.json` and an identical `index.circuit.json`. Source compilation regenerates separate `artifacts/final-source.circuit.json`; it must not overwrite accepted routing. The current manifest identifies hashes and current reports. All older SES/replay/publication/validation outputs are historical unless explicitly listed there.

| Check | Current result and scope |
|---|---|
| `npm run source:check`, `npm run typecheck`, `npm run build` | Pass. Source/schematic compilation and accepted saved-board rendering/DRC. |
| Native CLI netlist, pin specification, source | Exit0 on `index.circuit.tsx`; real exits/logs in `service-cli-results.json`. |
| Native CLI build | Routing-disabled source build/PCB PNG passes; not an accepted-routing regeneration. |
| Native CLI placement | Exit1 advisories retained; native placementDRC0 errors /0 warnings. See disposition below. |
| Prepared A4 schematic-placement | Exit0, zero findings on `artifacts/final-source.circuit.json`. |
| Saved native all-check DRC | 0 errors,1 warning: generic Q_DATA NPN symbol has no `requires_power` pin. This discrete transistor has no supply pin; warning retained. |
| Independent native connectivity | 52 named nets, all copper layers, no disconnected nets. |
| Trace/via width and current screen | No errors; 35µm outer /17.5µm inner and30°C IPC2221 rise assumptions. This does not prove temperatures or plane-current sharing. |
| Actual Gerber/drill/CAM audit | PASS: no named opens/shorts or unexpected unassigned copper; actual apertures/drills/paste/mask/outline and BOM/CPL compared against source. |
| `tsci check shorts ... --mode gerber --layer all --pixels-per-mm 100` | No shorts on any layer. Actual saved command output retained. |
| Functional silkscreen | All12 labels preserve their original strokes in exported final Gerber; no clipped functional text. |
| Via/paste/process inspection | PASS ordinary-via overlap screen; explicit filled/capped SMT vias require supplier process acceptance. |
| Browser schematic UI | All14 native A4 pages opened in Chromium, labels/A4 dimensions verified,0 browser errors. This project UI shows real CLI analysis; official IDE/WebGPU analyzer was not executed. |
| Mechanical BREP/access | Current model/hash report records checks, dimensions and disclosed generic-model discrepancy; hardware fit/tolerances remain unqualified. |

`tsci check netlist` supports the TSX entry, not a JSON array; the unsupported-input error from older work is not a board failure. Raw-entry schematic analysis precedes the native A4 preparation stage: the packaged prepared sheets are the reviewed schematic. Source-generated physical pads/holes/poses and numbered-pin/net semantics are compared to saved routing by the import/presentation check and `service-pin-net-invariance.json`.

Placement advisories use airwire/orientation/courtyard heuristics without considering accepted routes or probe-only bare interfaces. They are retained in `service-cli-placement.txt`, not suppressed or called a CLI pass. Actual pad connectivity, native placementDRC, copper/CAM and component/probe/access geometry are assessed separately. No failed physical placement is waived by this disposition. Review exact suggestions before future rerouting.

Reproduce current checks: `npm run typecheck`, `npm run source:check`, `npm run build`, `python3 scripts/check-service-cli.py`, `/workspace/.routing-venv/bin/python scripts/verify-connectivity.py`, `npm run check:copper`, `npm run export`, `npm run check:manufacturing`, `/workspace/.routing-venv/bin/python scripts/inspect-via-paste.py`, `npm run shorts`, `/workspace/.routing-venv/bin/python scripts/audit-functional-silk.py`, `/workspace/.routing-venv/bin/python scripts/review-mechanical.py`, `python3 scripts/check-a4-browser.py`. Export also uses the official CLI and validates unchanged native copper/drill files. Review manufacturing/assembly requirements before using any generated package.

Hardware tests unperformed: windingcurrent, USB enumeration/programming/PD, power transitions/brownout/backfeed, regeneration, mountedtemperatures and complete physicalfit. External effective-C, exact protection/model/material data, pickup/rotation preview and fabrication acceptance remain open. Software PASS is not production release.
