# NEMA14 RP2040 motor controller

35 × 35 mm, four-layer, 15 V USB-PD stepper-controller prototype. All 81 fitted parts populate the top face; LEDs, TMP102 and buzzer remain present. The outward-facing USB-C mouths share the +Y edge at 12.4 mm pitch. Use two 10 mm cable housings (2.4 mm nominal gap) and M3 DIN 920 heads ≤Ø4 mm. Mount holes are exactly (±13, ±13), Ø3.2 mm.

The regenerated [JLCPCB order-review package](artifacts/jlcpcb-review/JLCPCB-OrderReview.zip) passes the independent CAM audit. It includes the reference SMT JST-SH header, exact supplier BOM/CPL, stencil and assembly maps, and the eight USB shell joints requiring secondary soldering. Supplier approval of pickup orientation, availability, stencil and filled/capped thermal-via processing remains required.

See [assembly and harness constraints](docs/top-assembly.md), the [five-sheet schematic](artifacts/schematic-a4.pdf), [order-review receipt](artifacts/jlcpcb-review/order-review-verification.json), and [current validation](artifacts/resume-validation.json). `assembly-preview.circuit.tsx` is a separate unrouted visual concept. Firmware/bench operation and rear-motor attachment remain unverified.
