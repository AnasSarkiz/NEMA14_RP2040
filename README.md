# NEMA14_RP2040 1.10.2

35 × 35 × 1.6 mm, four-layer NEMA14 controller. Four NPTH holes are exactly (±13, ±13), Ø3.2 mm. Both USB-C sockets face upward; defined 10 mm housings have 2.1 mm nominal separation. Maximum Ø4 mm DIN 920 screw heads are required. Minimum via drill/pad: Ø0.30/Ø0.45 mm.

Factory component assembly is TOP only, with separate bare TOP test pads. AS5600 C79815 and its 100 nF/1 µF capacitors are BOTTOM **doNotPlace**, omitted from factory BOM/CPL and paste. TMP102, LEDs, buzzer, USB/PD and JST-SH motor interfaces are retained.

See [engineering fixes](docs/engineering-fixes.md), [six-sheet schematic](artifacts/schematic-a4.pdf), [current checks](artifacts/resume-validation.json), [JLCPCB order review](docs/jlcpcb-order-review.md) and [assembly/harness constraints](docs/top-assembly.md). The current Circuit JSON is `index.circuit.json` and the default fabrication archive is `artifacts/nema14-gerbers.zip`.

Supplier process/pickup approval and prototype bench tests remain outstanding. Rear mounting and encoder shaft/magnet fit are unverified. `assembly-preview.circuit.tsx` is an unrouted visual concept. No manufacturing order or production approval is implied.
