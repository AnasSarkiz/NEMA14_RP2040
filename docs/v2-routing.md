# V2 routing work in progress

The mistaken rotation was reverted in `ac234d7`. The WAGO 250-204 remains
outward-facing. The ordered V1 and public tscircuit package are unchanged.

The current checkpoint has **342 traces, 279 through vias and 57 ground-fill
regions** across four copper layers. **51 of 70 physical net groups are connected;
19 remain open.** Native DRC retains **78 errors and six warnings**. Work continues;
these are not order files.

[Top copper SVG](../artifacts/v2/routing/top.svg) ·
[Inner1 SVG](../artifacts/v2/routing/inner1.svg) ·
[Inner2 SVG](../artifacts/v2/routing/inner2.svg) ·
[Bottom SVG](../artifacts/v2/routing/bottom.svg) ·
[Standalone routing viewer](../artifacts/v2/routing/NEMA14-V2-routing-viewer.html)

## Evidence and current limits

The independent physical audit checks every actual supplier pad, wire segment,
plated barrel and ground polygon on all four layers. It finds **zero shorts,
foreign-net clearance violations, board-edge violations, mount-hole clearance
violations, keepout overlaps or changed pin/net assignments**. All 342 connected
physical pin assignments and all source placement records match the current seed.
The 19 opens correctly keep the audit failing.

Native DRC retains 74 port-connection errors and four trace errors. Source checks,
schema, typechecking, USB locating-slot drills and independent full-courtyard
placement checks pass. The native DRC receipt and physical audit bind their
results to the candidate SHA-256 in `routing-status.json`.

The MCU crystal and load-capacitor placements were refined to permit five short
top-only oscillator traces without vias. USB and core flash signals now connect;
QSPI chip select still has an open boot-resistor branch. Three explicitly checked
0.50/0.30 mm grounded thermal vias occupy the MCU, PD and driver exposed pads.
All other vias remain subject to the strict native via-in-pad check. Ordinary
vias use at least 0.45 mm pads, 0.30 mm drills and 0.075 mm annuli.

The Ø6.4 mm screw-head envelopes apply on **both external surfaces**, and fitted
courtyards remain outside them. Inner-layer copper may pass under the insulated
FR4 mounting surface, with at least 0.25 mm copper clearance from the actual
Ø3.2 mm drilled holes on every layer. Through vias remain outside the surface
head envelopes. Supplier USB locating-hole lands retain their imported geometry;
the minimum 0.125 mm gap to a supplier plated land is reported separately from
mount-hole clearance and every NPTH overlap is still rejected.

## Repair tools

`route-v2-repair.py` searches actual physical copper islands using a conservative
construction grid. The exact independent audit, native DRC and final CAM checks
remain mandatory. `force-v2-escapes.py` can displace ordinary copper locally;
every displaced net remains an explicit open until reconnected. Neither tool
alters source nets or supplier pads. Contact/source identity refreshes change only
metadata based on actual copper intersections, never conductive geometry.

Ground fill is regenerated after foreign copper changes. Floating-copper cleanup
and dangling-tail trimming are accepted only when all physical-pad partitions
remain unchanged. Persisted plans and repair histories are under
`artifacts/v2/routing/`; no V1 copper is imported.

The original `route:v2` Freerouting command remains experimental and can replace
the working candidate. Use an isolated copy when experimenting. The main
`index.circuit.json` preview remains the unrouted placement seed during repairs.

Next work: close every open net; reach zero native DRC errors; verify main phase
widths, Kelvin branches, USB reference and thermal/power integrity; then rerun
Gerber/drill checks. Motor-wire fit, shunt sourcing and hardware calibration
remain unqualified. Publication and manufacturing remain blocked.
