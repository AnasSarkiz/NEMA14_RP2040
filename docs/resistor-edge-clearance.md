# RP2040 resistor edge clearance — v1.7.0

Every resistor is reviewed on all four board edges, including top and bottom assembly sides. The nominal pad-to-profile target is **at least 0.75 mm**. A 1 mm placement attempt was assessed; the delivered layout uses the 0.75 mm target within the fixed 35 × 35 mm outline, fixed connectors, native courtyards and screw envelopes.

9 resistors move or rotate. Native land patterns, original JLCPCB OBJ/STEP files, resistor values, physical pin identities and all net assignments are retained. Other component placements, both USB mouths, the JST, the four exact (±13, ±13) Ø3.2 mm holes and PCB outline remain unchanged. Affected copper is rerouted and the ground regions refilled; obsolete trace ends are removed only when the live-pad connectivity partitions remain identical.

The [independent clearance receipt](../artifacts/edge-resistors/clearance-verification.json) matches every resistor pad to its actual regenerated Gerber flash and measures all four edges. The [CSV](../artifacts/edge-resistors/clearance-verification.csv) lists every resistor; the [placement plan](../artifacts/edge-resistors/placement-plan.json) and [translation/rip-up receipt](../artifacts/edge-resistors/translation-and-ripup.json) record construction. The editable `src/supplier-placement.json` contains the final locations and rotations. Freshly compiled native footprints were compared with the translated geometry and canonicalized only for sub-micrometre floating-point differences.

Native DRC, independent physical connectivity, every-trace/net review, copper width/current screening, actual Gerber copper/drill analysis and STEP mechanical screening qualify the final board revision. The [full qualification receipt](../artifacts/resume-validation.json) retains actual exit codes. The five-sheet schematic and electrical source remain unchanged.

The 12 mm USB plug envelopes and M3 DIN 920 maximum Ø4 mm head requirement remain in force. Mechanical screening is nominal CAD evidence. Manufacturing assembly BOM/CPL, paste/stencil and silkscreen findings, firmware/bench tests and rear motor fit remain unqualified; this is a prototype publication.

| Resistor | Previous centre (mm) | New centre (mm) | Rotation | New nominal minimum pad-to-edge (mm) |
|---|---|---|---|---|
| R_RUN | (-16.860, 13.886) | (-16.475, 13.885) | 90° | 0.755 |
| R_USB_SENSE_H | (-16.500, -0.500) | (-16.475, -0.500) | 90° | 0.755 |
| R_USB_SENSE_L | (16.246, 13.930) | (16.030, 13.930) | 0° | 0.754 |
| R_VM_H | (16.236, 15.790) | (16.235, 15.790) | 90° | 0.994 |
| R_REF_H | (4.857, -16.698) | (12.085, -16.315) | 0° | 0.753 |
| R_REF_L | (6.810, -16.234) | (6.810, -16.030) | 90° | 0.754 |
| R_TEMP_SCL | (-16.500, -9.250) | (-16.475, -9.250) | 90° | 0.755 |
| R_PWR_LED | (12.990, -16.414) | (14.025, -16.030) | 90° | 0.754 |
| R_STATUS_B | (-15.614, 16.860) | (-15.615, 16.475) | 180° | 0.755 |
