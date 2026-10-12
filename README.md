# NEMA14 RP2040 controller — v1.5.0 prototype

A **35 × 35 × 1.6 mm**, four-layer controller with native JLCPCB parts, two USB-C ports on one edge and a fitted JST PH motor connector. This revision adds the reference power/debug LED, RGB status LED, TMP102 temperature sensor and PWM magnetic buzzer. USB-C and JST physical-pin roles match Rishabh’s reference, with board-specific MCU GPIOs documented in [reference feedback](docs/reference-feedback.md).

Four Ø3.2 mm mounting holes remain exactly (±13, ±13). The same-edge USB layout is screened for two 12 mm plug housings and M3 DIN 920 screw heads ≤Ø4 mm. Native STEP screening passes the defined envelopes. **Rear mounting compatibility remains unverified.**

The motor driver retains its 0.351 A nominal limit, reset defaults and 1/16 microstep configuration. Power USB-C requests 15 V through CH224K; programming USB-C supplies fixed 5 V and full-speed USB data, with independent CC pull-downs and USB ESD protection. Logic power uses the AP63203 3.3 V buck regulator.

This is **not a manufacturing release**. Electrical/copper verification, actual drill coordinates and mechanical evidence are recorded in [current verification](docs/mounting-usb-verification.md). Assembly/stencil findings, firmware, bench tests and the complete motor mounting assembly remain unqualified. A reference board working does not prove this layout or its firmware has been physically validated.

C_DV50, C_IO49, R_XOUT, C_XOUT and R_TEMP_SDA use native footprints on the bottom. Bare debug pads are also on the bottom. Two-sided assembly and a verified underside gap are required.

Useful commands: `npm run source:check`, `npm run check`, `npm run export`, `npm run check:mounts`, `npm run check:copper`, and `npm run publish:tscircuit`. Publishing is gated by current qualification receipts and independent CAM copper checks. Saved routing is delivered in `index.circuit.json`; `index.circuit.tsx` and `src/board.tsx` retain the editable circuit source.
