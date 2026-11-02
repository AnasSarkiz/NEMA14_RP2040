# NEMA14 RP2040 V2 engineering draft

V2 starts from ordered V1 source commit `b6e2de5`. It is not a manufacturing
release. The ordered board, its public tscircuit package and its JLCPCB order
remain V1. Old files under `artifacts/` are historical unless under `artifacts/v2/`.

## Requested changes

| Item | V2 source implementation |
|---|---|
| Outline | 34.5 × 34.5 × 1.6 mm, four layers; remove 0.25 mm from each original 35 mm edge. Mounting holes remain Ø3.2 mm on a 26 mm square. |
| Both winding currents | Two inline 50 mΩ shunts and INA240A1 amplifiers; outputs reach RP2040 ADC0/ADC1 through 100 Ω / 10 nF filters. |
| Motor terminal | One WAGO 250-204 / C2765063 four-pole spring terminal. Exact supplier footprint/CAD imported; housing within the outline. Procurement and factory lead fit remain unresolved. |
| Buzzer | Compact MLT-5020 / C94598, 5.2 × 5.2 mm, passive magnetic, 2–4 V / 100 mA, 4 kHz; smaller DMN2300UFB4 MOSFET and B5819WS flyback diode. Sound level differs from the original. |
| RGB drivers | Three DMN2300UFB4-7B MOSFETs replace the larger pre-biased BJTs. Existing 1 kΩ LED limiters remain; new 10 kΩ gate pull-downs keep the LEDs off during reset. |
| Debug pads | Five bare copper probe pads on bottom; both 0.8 mm BOOT recovery pads remain top. No bottom fitted assembly is added. |
| Encoder capacitors | C_ENCODER (100 nF) and C_ENCODER_BULK (1 µF) fitted on top; optional AS5600 IC remains bottom/DNP. |
| USB locating holes | Both USB4145 footprints retain the original round NPTH and now include the supplier's oval NPTH. All four soldered shell tabs remain. |

## Electrical design

The A4988's existing 0.24 Ω SENSE1/SENSE2 regulation resistors are unchanged.
They control the driver's approximately 0.351 A nominal peak phase current.
They are not substituted for the telemetry shunts.

Each new 0.05 Ω shunt is in series with one winding output, before the motor
terminal. This allows bidirectional winding-current sensing during driven and
recirculating current, subject to the amplifier's common-mode/transient limits.
The driver side connects to IN_POS; the terminal side connects to IN_NEG.
Dedicated Kelvin branches must join at the shunt pads, outside load-current
branches. Input common mode switches with the A4988 bridge.

The compact draft uses **INA240A1PWR / C93965 (TSSOP-8)** to save space.
Its pinout is 1 NC, 2 IN_POS, 3 IN_NEG, 4 GND, 5 VS, 6 REF2, 7 REF1, 8 OUT.
NC is explicitly unconnected. The physical pin map is independently checked in
the generated source; it differs from the larger SOIC INA240A1DR package.

The target remains a single top assembly side. The pictured KEFA terminal was
also evaluated with underside circuitry, without a verified fit in the bounded
searches. It is not the selected footprint in this compact draft. The smaller
INA240 package has a higher catalog price (about $2.15 single-part versus about
$1.02 for SOIC); these are snapshots, not a JLCPCB quote or guaranteed stock.

With VS and REF1 on 3.3 V and REF2 grounded, the nominal zero-current output
is 1.65 V. Gain is 20 V/V, giving **1 V/A** across a 50 mΩ shunt:

`I = (V_ADC - V_ZERO) / (20 × 0.05 Ω)`

At ±0.4 A, nominal output is 1.25–2.05 V. Shunt dissipation is 8 mW at 0.4 A.
Use measured zero offset and gain calibration rather than assuming exactly
3.300 V. The RP2040 channels are multiplexed, not sampled simultaneously.
Firmware must choose sample timing/filtering appropriate to PWM and microsteps;
the RC network is not a substitute for switching-transient validation.

| RP2040 pin | Function |
|---|---|
| GPIO26 / ADC0 | Winding A current |
| GPIO27 / ADC1 | Winding B current |
| GPIO28 / ADC2 | PD motor-supply voltage, existing 100 kΩ / 10 kΩ divider |
| GPIO29 / ADC3 | Existing programming-USB voltage/presence divider |
| GPIO4 / GPIO5 | Temperature/optional encoder I²C0 SDA/SCL, moved from GPIO26/27 on I²C1 |
| GPIO10 | Existing POWER_GOOD input |

RGB LED, buzzer, temperature sensor, flash, crystal, USB data and optional DNP
encoder are retained. Firmware must adopt GPIO4/5 and hardware I²C0 instead of the former I²C1 bus.

The optional encoder's **100 nF C_ENCODER** and **1 µF C_ENCODER_BULK** are
fitted on the top assembly side, across V3V3 and GND. Their top courtyards are
reserved in the placement search. U_ENCODER remains bottom/DNP; five bare probe pads also use bottom copper without a placement operation. Final
routing must keep the supply and ground paths short through vias to the bottom
sensor; the current draft has no routed copper.

## USB footprint evidence

The fresh exact-footprint import still omitted EasyEDA `SOLIDREGION` NPTH
`gge931`. The raw supplier data is retained in
`references/v2/usb-easyeda.json`, and the unmodified reimport text in
`references/v2/usb-reimport.tsx.txt`.

The slot is restored from that source path, not guessed from the factory photo:
width **1.5099792 mm**, height **0.7099808 mm**, local centre
**(4.1524872, 0.000127) mm**. The existing round locating hole is Ø0.7099808 mm
at **(-3.8474968, 0.000127) mm**. Pad geometry and the reviewed CAD transform
are preserved. The source audit checks both holes on both connectors and all
eight shell tabs. No existing physical board should be drilled to add the slots.

The installed importer is the fallback used for this restoration. Installing
latest CLI 0.1.2425 failed because its npm tarball returned HTTP 404. This work
does not establish whether an upstream converter fix is available elsewhere.

## Terminal selection and wire qualification

The selected layout uses **one WAGO 250-204 / C2765063**, with the
manufacturer's **15.5 × 12 mm body, 13.1 mm installed height**, 3.5 mm pole pitch,
and four staggered solder pins. The full imported courtyard is approximately
16 × 12.5 mm. Physical poles are **1 A+, 2 A−, 3 B+, 4 B−**. Both bottom-side
pole labels and the schematic identify this order. Detailed supplier OBJ/STEP
models replace the former Phoenix envelope models for the active motor terminal.

The terminal accepts bare stranded **0.2–1.5 mm² / 24–16 AWG**, stripped
**8.5–9.5 mm**, with 45° wire entry and push-button release. Its IEC 8 A rating
exceeds the 0.4 A/phase target. The actual factory motor wire gauge and insulation
fit are still unconfirmed. Catalog availability is not live stock assurance.
See [WAGO implementation, component changes and sourcing](v2-wago-repack.md).
The older [terminal selection research](../references/v2/terminal-selection.md)
remains historical evidence, not the current BOM.

The MLT-5020 buzzer has nonzero mirror stock. It operates from 2–4 V at up to
100 mA, preserving the 3.3 V supply and flyback diode. Its
nominal resonance is 4 kHz and catalog sound level is 75 dB; firmware and bench
checks must validate the desired tone/loudness. It saves space while retaining
the buzzer feature. This is a deliberate part change, not a volume-equivalent
substitution. Catalog snapshots are in `references/v2/compact-parts-snapshot.json`.

The buzzer MOSFET changes from AO3400A to DMN2300UFB4-7B / C154728
(X2-DFN1006-3, 1.0 × 0.6 mm body). The exact supplier land pattern has a
1.2 × 1.6 mm courtyard. Its 20 V drain rating and 240 mΩ maximum RDS(on)
at 2.5 V gate drive support the 3.3 V, 100 mA buzzer load: about 2.4 mW
conduction loss using that resistance. The flyback diode remains fitted.
The new physical pin order is **1=G, 2=D, 3=S**, different from the old MOSFET;
source connections and schematic symbol mapping follow the new order.
The mirror snapshot shows 11,980 pieces; this is not live stock assurance.
See [Diodes manufacturer datasheet](https://www.diodes.com/datasheet/download/DMN2300UFB4.pdf).

The RGB channels now use the same DMN2300UFB4-7B device, with source to ground,
gate to the existing active-high GPIO, drain to the existing LED current-limiter
net, and a new 10 kΩ gate pull-down. The 1 kΩ LED resistors and fixed 5 V
common-anode supply remain. The maximum possible current is below 5 mA per
channel, far below the MOSFET rating. Gate drive and firmware polarity are
unchanged; the new physical map is 1 G, 2 D, 3 S. Reusing the buzzer MOSFET
saves footprint area and avoids another unique assembly part.

D_BUZZER changes to B5819WS / C64886, SOD-323, 1 A / 40 V, for the 100 mA
buzzer load. Its cathode remains on 3.3 V and anode on the switched sink.
The exact imported courtyard is 3.845 × 1.8 mm; the snapshot shows 393,595 pieces.

Five **bare copper** probe pads (3V3, GND, SWCLK, SWDIO, RUN) are on the bottom,
beside the optional encoder courtyard and clear of through-board terminals.
They add no bottom-side part placement. They require underside access, normally
with the controller unmounted from the motor. The top BOOT/GND recovery pair
uses 0.8 mm pads, about 1.25 mm centre separation, for fine tweezers/probes.

## Validation and remaining work

Run `npm run build:v2`, then `npm run check:v2:source` for source-generation
and electrical/drill checks. `artifacts/v2/source-review.json` reports the actual
generated source hash, native errors and routed-trace count. Passing its source
checks does not mean that placement or routing passes. `npm run check:v2` and
publication remain blocked while this is an unrouted draft.

`src/v2-placement-anchors.json` records the complete placement seed.
`scripts/place-v2.py --anchor-plan --feasibility-only` checks full catalog
courtyards, retained mounting positions, and local clock/power/current-sense
proximity budgets. It preserves the Ø6.4 mm head envelopes. Fixed anchors use
exact circle-to-rectangle distance; optional movable parts use 32 conservative
supporting-line directions with outward quantization. The 0.025 mm anchor grid
and 0.001 mm coordinate quantum preserve usable edge positions. Complete
courtyards stay within the outline, and the independent audit separately
enforces 0.25 mm copper-to-edge clearance. No courtyard is shrunk.
A timed-out search is UNKNOWN, never proof of fit or impossibility.

The generated source has **zero native errors**. The independent Shapely audit
checks 99 top and six bottom courtyards, board bounds, head clearance, bottom
probe-pad/through-hole separation and terminal pad/drill dimensions; it reports
zero errors. Its receipt records the actual source SHA-256. The minimum gap
between top courtyards is about **0.005 mm**: this is a dense fit between full
courtyard margins, not a copper-clearance measurement.

The independent audit also checks 62 placement-proximity budgets using generated
physical ports, including the flash capacitor’s connected pad. Output isolation
resistors are near their INA240 output pins, with the ADC filter capacitors near
the RP2040. These are placement budgets, not measured trace lengths.

All 33 electrical/source checks pass, including physical MOSFET pin maps,
RGB reset pull-downs, both current channels, encoder capacitors and USB drills.
The native schema and seven-sheet schematic placement checks pass. Use
`npm run check:v2:schematic` for V2; `check:schematic` and its frozen CH224A/V1
preservation checks apply to historical V1 work. These
checks establish a collision-free **placement seed**, not a routed electrical
layout. In particular, USB series resistors, divider/filter networks, QSPI,
Kelvin branches, driver current paths and power/ground loops still need review
against the actual routing; distances in the placer are not measured trace
lengths. Detailed wire/tool/magnet access and supplier 3D assembly review remain.
The WAGO model is the exact supplier CAD import; this does not establish wire/tool access or assembled-motor clearance.

`npm run check:v2:placement` reruns the independent geometry audit.
`npm run render:v2:placement` regenerates the readable SVG from native JSON.
The native PCB SVG and Circuit JSON are also saved. There are **zero routed
traces**, so manufacturing export/publication remain blocked by `check:v2`.

Before a new order: finalize the routed layout and mechanical access, route the new
board with Kelvin branches and corrected drill keepouts, check every physical
net, DRC/clearances, all-layer Gerber shorts, actual drills and assembly angles,
then verify current accuracy and switching behavior on the new prototype.

Primary component reference: [TI INA240 datasheet](https://www.ti.com/lit/ds/symlink/ina240.pdf).
The earlier related design is retained in `references/v2/reference-ina240-design.md`;
its qualification results apply to that board, not to V2.
