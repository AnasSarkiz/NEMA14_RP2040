# Verified v1.12.0 assembly and fabrication publication

Public package: https://tscircuit.com/AnasSarkiz/NEMA14_RP2040#3d

The actual unauthenticated default preview endpoint selects `assembly.circuit.json` and returns the complete reviewed routed PCB plus nine mechanical parts (motor, four proposed screws and four proposed spacers) and one cable. The public root assembly, native dist assembly and preview response match. Verification completed at 2026-10-15T00:45:46.060642+00:00.

The fabrication `index.circuit.json`, its native dist file, actual Gerber/drill archive, supplier models and required qualification evidence were independently downloaded and verified at 2026-10-15T00:45:31.695253+00:00. The reviewed board SHA-256 remains `67820851170068eb092c3b611949ce67218b58f1049365fd317e8c1a513645e6`. The four Ø3.2 mm holes remain at (±13, ±13), all via drills are Ø0.30 mm and via pads are ≥Ø0.45 mm. Publication changes only supplier CAD URL metadata in the saved manufacturing board; the assembly appends mechanical records without changing any reviewed record.

Fresh assembly source render, strict schema, TypeScript, exact electronic poses, native CLI record preservation and nominal collision/tool-access checks passed. The collision check reads the actual serialized JSCAD hardware and positions, uses 81 fitted supplier STEP parts and evaluates the 50-segment cable with a conservative radius 1.8 mm envelope. Complete and TOP WebGL renders were inspected. The unchanged board retains the existing full PCB/DRC/connectivity/CAM qualification receipts.

The initial registry upload timed out. Recovery resumed the exact same release, compacted the standalone assembly JSON without changing its parsed records and limited batches to 24 files. No existing public file rows were replaced; the final native fabrication and actual default assembly preview were verified after recovery.

**This is a nominal dimensional assembly concept, not rear-motor or production approval.** The motor-side JST termination and wire exit are proposed. Rear retention/thread engagement, rear shaft/magnet/airgap, stock harness and hardware fit, actual tolerances and physical operation remain unverified. JLCPCB placement/process/quote approval and bench qualification are still pending; no order or merge was performed.

Receipts: `artifacts/publication-verification.json`, `artifacts/top-assembly/assembly-publication-verification.json`, `assembly-fit-verification.json`, `assembly-build-verification.json`, `assembly-schema-verification.json` and `assembly-render-verification.json`.
