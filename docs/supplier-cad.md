# Supplier CAD and printable schematics

The custom electrical footprints originally had no explicit `cadModel`. A footprint and manufacturer part number alone do not provide a supplier mesh to the 3D viewer.

`src/jlcpcb-catalog.json` identifies exact JLCPCB C-numbers, manufacturer part numbers, supplier CAD, and asset hashes. `imports/` preserves the cached supplier TSX, OBJ and STEP files. `src/jlcpcb.ts` adapts their sourcing/CAD properties to the checked electrical footprints and physical pin aliases. OBJ and STEP files are mirrored in this project's GitHub repository. The source and saved viewer records use these public asset URLs; viewers must be able to access raw.githubusercontent.com. This keeps the registry package within its upload limit.

**Supplier import coverage is incomplete.** See [the coverage report](../artifacts/jlcpcb-import-report.json) for every mapped and pending reference. No generic package mesh is presented as an exact supplier model. Fresh JLCPCB/EasyEDA search and model downloads are blocked by the current cloud network policy; supplier destinations have been added to the editable environment draft but that draft is not yet active.

Motor, debug and RP2040 BOOT interfaces are bare PCB solder interfaces. They have no fitted component, supplier part number, or component CAD model.

Both USB receptacles use JLCPCB **C165948 / TYPE-C-31-M-12**. The original supplier STEP is retained separately. Its mesh and exported STEP have been translated by 1.65 mm in local Y into the checked land-pattern frame; the CAD adapter compensates for the grouped pad bounding-box origin. The saved rotations put their mating openings exactly at X = −17.5 and +17.5 mm. The existing grouped shield/parallel contacts remain electrically unchanged. This coordinate verification is not an assembly fit test.

## A4 documentation

[The printable PDF](../artifacts/schematic-a4.pdf) contains numbered **297 × 210 mm landscape A4** sheets. Large MCU/driver symbols have dedicated sheets; remaining parts use generous two-column cells. Every numbered physical pin appears, connected pins terminate in named nets shared across pages, and unused pins are marked NC. Internal aliases of a grouped USB shield pin are represented by that physical pin, rather than extra connector pins. Each page includes notes describing every chip's purpose. Firmware functions described in the notes are requirements; firmware and bench validation remain pending.

The saved circuit JSON contains native `schematic_sheet` records for every page, usable in the tscircuit viewer. The SVG files retain physical A4 dimensions and a pixel viewBox; the PDF preserves vector text and linework at the exact paper size. The first-page PNG is a preview; the PDF contains every page.

```sh
npm run source:check
python3 scripts/sync-presentation.py
npm run render
/workspace/.routing-venv/bin/python scripts/export-a4-pdf.py
python3 scripts/report-presentation.py
npm run check
```

`prepare-schematic.ts` generates the sheet graphics from the electrical graph without changing that graph. `sync-presentation.py` asserts identical source pin identities and net keys and retains all saved PCB geometry records. `presentation-verification.json` records that preservation; `report-presentation.py` verifies supplier asset hashes, CAD assignments, USB opening planes, and schematic pin/net coverage. There is no need to reroute to update CAD or schematic presentation.

Purchasing availability, footprint fit, ratings, rotations and thermal behavior still require assembly review. These boards remain hardware prototypes.
