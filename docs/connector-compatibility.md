# USB-C and JST connection review — 2026-10-11

Both NEMA14 variants use the same connector contact assignments. Compared with the actual registry release [imrishabh18/rp2040-motor-controller@1.0.42](https://tscircuit.com/imrishabh18/rp2040-motor-controller), the DATA USB interface, PD CC connections and keyed JST phase order agree. No swapped contacts were found in the reviewed saved PCB or a fresh source build. The power port intentionally retains WCH's **PD-only, fixed 15 V** configuration rather than the reference's configurable 5–20 V/legacy charging behavior.

Reference release `e8d285f7-c3d8-46f5-9a54-344fdde0124e` was retrieved on 2026-10-11. Its complete `dist/index/circuit.json` SHA256 is `34707c3ea003cc69b89c381fcfc587d3797e14e8f6cdaee665689d08d022adeb`. The exact relevant source files and a connector/endpoint geometry extract are saved under `references/rishabh-connectors-1.0.42/`. The extract records its scope and original source hashes. This review does not qualify the reference board.

## USB contact assignments

Both connectors are HRO **TYPE-C-31-M-12 / JLCPCB C165948**. USB contact designations are authoritative; the supplier's numbered pads are implementation indices, not USB pin names. Rishabh's `usb-c-20v.tsx` remaps these indices to legacy schematic numbers. Copying those numbers directly into our supplier import would cause miswiring.

| USB contacts | Our supplier pads | DATA port | PD motor-power port |
|---|---|---|---|
| A1/B12, B1/A12 | 13, 14 | GND | GND |
| Four shell stakes | 1–4 | GND | GND |
| A4/B9, B4/A9 | 16, 15 | DATA_VBUS, nominal USB 5 V | PD_VBUS, requested 15 V |
| A5 / CC1 | 6 | Separate 5.1 kΩ Rd to GND | CH224K CC1, physical pin 7 |
| B5 / CC2 | 12 | Separate 5.1 kΩ Rd to GND | CH224K CC2, physical pin 6 |
| A6, B6 / D+ | 8, 10 | Joined USB_DP; ESD-protected, then MCU D+ | Explicitly unconnected |
| A7, B7 / D− | 9, 7 | Joined USB_DM; ESD-protected, then MCU D− | Explicitly unconnected |
| A8, B8 / SBU | 11, 5 | Explicitly unconnected | Explicitly unconnected |

CC1 and CC2 remain separate on each receptacle. The data port's two 5.1 kΩ terminations implement a sink/device port. The CH224K owns the PD port's CC termination and negotiation; do not add the DATA port's Rd resistors to its CC nets. Neither port is configured as a USB host or a power source. Both mouths face +Y, with 14 mm centre spacing, as documented in the mechanical review.

RP2040 D+/D− use separate 27 Ω series resistors to physical MCU pins 47/46, matching Rishabh's RP2040 interface. CH32 uses its WCH PHY/reference-download arrangement to physical pins 27/26. The USBLC6-2SC6 protects the DATA pairs and references DATA_VBUS, not the 15 V bus. The two VBUS nets remain distinct; separate 1N5819WS diodes feed LOGIC_IN and must be fitted with the documented polarity. Diode leakage, supply handover and absence of harmful backfeed still need measurement.

WCH **CH224DS1 v1F §5.5** explicitly requires disconnecting the connector's DP/DM, shorting the CH224's DP to DM, and permits CH224K VBUS pin 8 to be NC for PD-only use. That is the existing circuit. CFG1=GND and CFG2/CFG3=PD_VDD request 15 V under §5.2.2. Rishabh instead connects its power receptacle's D+/D− to CH224K for legacy protocols and senses VBUS. Those differences are deliberate; changing them would expand this design's supported charging protocols and voltage behavior.

## Keyed motor harness

| JST circuit number | 14HM11-0404S wire | Phase | A4988 physical output |
|---|---|---|---|
| 1 | Black | A+ | OUT1A, pin 24 |
| 2 | Green | A− | OUT1B, pin 21 |
| 3 | Red | B+ | OUT2A, pin 26 |
| 4 | Blue | B− | OUT2B, pin 1 |

This is Rishabh's **1=A+, 2=A−, 3=B+, 4=B−** convention. Its DRV8825 positive outputs also pass through current-telemetry shunts; those driver pin numbers and shunts are not part of our A4988 design. The footprint's mounting-side order, 2 mm pitch and native CAD terminal projection agree with the reference. Do not infer housing cavity numbers from an arbitrary photograph: the wire-entry and mating-face views reverse the apparent left/right order. Use the header pin-1 mark and confirm each mated contact with an ohmmeter.

Use **JST B4B-PH-K-S(LF)(SN)** top-entry header, **PHR-4** mating housing and four **SPH-002T-P0.5S** contacts. JST specifies AWG 30–24 and insulation OD 0.8–1.5 mm for this contact. The harness uses the documented AWG24 PTFE extensions; verify the factory motor lead size before splicing/crimping. The manufacturer-derived plated bores remain 0.75 ±0.05 mm. The header and mating housing remain inside the board outline; the carrier restraint and service loop are required. See [illustrated wiring](motor-wiring.svg) and [assembly instructions](mechanical-fit.md).

**JST PH standardizes the connector mechanics, not the motor winding pinout or wire colors.** An arbitrary commercial four-pin PH motor harness is not automatically interchangeable. Identify the two winding pairs and verify numbered continuity before applying power. Never insert/remove the motor plug while either USB source is connected; discharge the bus first.

## Verification and limits

Run `python3 scripts/audit-connector-pinout.py` for saved copper, and run it with `artifacts/final-source.circuit.json` after `npm run source:check` for source-built connectivity. The saved audit is also part of `npm run check`. Reports are [saved-PCB audit](../artifacts/validation/connector-pinout-audit.json) and [source audit](../artifacts/validation/connector-pinout-audit-source.json). They check all 32 numbered USB contacts, four motor contacts, separate CC/VBUS nets, exact connector identities, native pad positions, JST CAD orientation, ESD, PHY and PD endpoints. They verify the reference's actual endpoint relationships as well as its labels.

The supplier revisions differ in shell slot lengths: ours are approximately 0.8 ×1.2/1.5 mm; the reference uses 0.8 ×1.4/1.6 mm. Contact centres and copper outlines match. No footprint was silently substituted or drill changed during this connection review. Actual insertion, shell solder wetting and finished slot acceptance on the 1.6 mm PCB remain supplier/sample qualification items; electrical agreement does not prove mechanical interchangeability. Rishabh's cited HRO drawing could not be freshly retrieved in this session (HTTP403), so it is not claimed as newly verified manufacturer evidence.

Fresh source builds and typechecks, native DRC, independent copper connectivity and all-layer Gerber-mode shorts checks passed for both boards. Six existing metadata warnings per board remain documented; zero actionable DRC errors or disconnected nets were reported. Saved circuit JSON and fabrication outputs are unchanged by this review.

Prototype tests still required: DATA enumeration/ROM flashing with **both plug orientations**, PD negotiation/fallback with both orientations, all cable insertion orders, power-loss/reset behavior, VBUS/backfeed measurements, physical JST insertion/cavity continuity, and supplier slot/wetting acceptance. Passing CAD checks does not establish USB compliance, physical harness compatibility, or production readiness.
