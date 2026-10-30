# NEMA14 RP2040 V2 engineering draft

V2 starts from ordered V1 source commit `b6e2de5`. It is not a manufacturing
release. The ordered board, its public tscircuit package and its JLCPCB order
remain V1. Old files under `artifacts/` are historical unless under `artifacts/v2/`.

## Requested changes

| Item | V2 source implementation |
|---|---|
| Outline | 34 × 34 × 1.6 mm, four layers; remove 0.5 mm from each edge. Mounting holes remain Ø3.2 mm on a 26 mm square. |
| Both winding currents | Two inline 50 mΩ shunts and INA240A1 amplifiers; outputs reach RP2040 ADC0/ADC1 through 100 Ω / 10 nF filters. |
| Motor terminal | Compact Phoenix 1770979, C3818616, imported with original footprint and CAD. Default draft candidate pending factory motor-wire fit. The pictured KEFA is retained as an alternative. |
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

The user suggested the KEFA KF208V-2.54-4P / C49173465. Its much larger courtyard
made the 34 mm placement difficult. The user confirmed a compact terminal and top-side-only assembly. The
provisional compact candidate is:
**Phoenix PTSM 0,5/4-2,5-V THR R44 / 1770979 / C3818616**.

The primary manufacturer datasheet is cached as `references/v2/phoenix-1770979.pdf`.
It specifies a 10.5 × 5 mm body and 10 mm height above the seating plane.
Pin length below that plane is 2.1 mm (about 0.5 mm nominal protrusion through
a 1.6 mm PCB, before manufacturing/solder tolerances).
Bare stranded conductor range is **0.2–0.5 mm²**, with **6 mm strip length**.
Its 6 A IEC / 5 A UL current ratings exceed the motor's 0.4 A phase rating.
The generic 26–20 AWG approval entry does not override the 0.2 mm² minimum for
bare stranded conductors. Indexed JLCPCB assembly data previously listed
Economic/Standard wave assembly with a fixture; recheck the quote and fixture. The current JLCsearch mirror returns stock 0 for C3818616.
This is not live JLCPCB confirmation, but the terminal must remain provisional
until stock/preorder or an available replacement is confirmed. The selected
current amplifiers and shunts have nonzero mirror stock; see
`references/v2/catalog-snapshot.json`.

The 14HM11-0404S factory drawing does not specify lead gauge or conductor CSA.
The previous 28 AWG JST pigtails are below this terminal's bare-stranded minimum.
Direct motor-wire fit therefore remains unconfirmed. No new order was placed.

The original manufacturer drill drawing and EasyEDA footprint show two contacts
per pole on 3.1 mm rows. Both contacts per pole are explicit in the generated
netlist and connect A+, A−, B+, B− in order. The wrapper changes port identities
only, preserving every supplier pad and drill. Verify wire insertion, release-tool
access, pin protrusion, motor clearance and bend radius in the mechanical review.

## Validation and remaining work

Run `npm run build:v2`, then `npm run check:v2:source` for source-generation
and electrical/drill checks. `artifacts/v2/source-review.json` reports the actual
generated source hash, native errors and routed-trace count. Passing its source
checks does not mean that placement or routing passes. `npm run check:v2` and
publication remain blocked while this is an unrouted draft.

`scripts/place-v2.py` searches using complete supplier courtyards, retained hole
positions and a conservative stepped cover of the Ø6.4 mm screw-head envelopes.
A timed-out search is recorded as UNKNOWN, never as proof of a fit or of
impossibility. The optional `--geometry-only` mode optimizes proximity but does
not enforce the local center-distance constraints; it is a packing study and
not an analog/clock-layout signoff. The receipt records that distinction. Verify
placement against native output and physical pad/loop geometry after any result.

The present PCB draft still has native placement, overlap and edge-clearance
errors, and contains no routed traces. Those errors are retained in the JSON
and review receipt, not suppressed. The bounded placement studies did not
produce a verified complete layout. Only the electrical schematic, outline
request and locating-slot restoration are implemented at this stage.

Before a new order: complete placement and mechanical access, route the new
board with Kelvin branches and corrected drill keepouts, check every physical
net, DRC/clearances, all-layer Gerber shorts, actual drills and assembly angles,
then verify current accuracy and switching behavior on the new prototype.

Primary component reference: [TI INA240 datasheet](https://www.ti.com/lit/ds/symlink/ina240.pdf).
The earlier related design is retained in `references/v2/reference-ina240-design.md`;
its qualification results apply to that board, not to V2.
