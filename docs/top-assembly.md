> Historical baseline document: this predates the opposite-edge v1.11.0 draft. See [current draft and blockers](opposite-edge-review.md) for current evidence.

# NEMA14_RP2040: top-side population and reference connectors

All fitted components populate the top face. The PCB remains 35 × 35 × 1.6 mm with four copper layers and four NPTH mounting holes exactly (±13, ±13), Ø3.2 mm.

Both upright GCT USB4145-03-0070-C C5815189 sockets are on the +Y side at nominal (−6.05, 15.15) and (6.05, 15.15) mm, with 12.1 mm pitch and +Z insertion. The accepted cable envelope is **10 mm housing width, 7 mm depth, 30 mm upward length**, giving a nominal 2.1 mm gap. M3 DIN 920 heads must be no larger than Ø4 mm; the mechanical screen uses Ø4.4 × 3 mm envelopes. Actual cables, tool access and assembly tolerances still require hardware qualification.

The USB drawings use native `connector standard="usb_c"` symbols. Every numbered physical contact, including the four separately grounded shell tabs, is retained in source, copper and CAM checks. DN aliases remain available; DM is the standard symbol label.

J_MOTOR uses the NEMA8 reference's imported SMT **BM04B-SRSS-TB(LF)(SN), C160390**, a top-entry JST-SH header. Proposed mating housing: SHR-04V-S with SSH-003T-P0.2-H contacts and AWG28 harness wires; verify the exact ordering suffix, crimping and harness with the supplier. See [the current connector review](jst-restoration.md). Pin order remains **1 A+, 2 A−, 3 B+, 4 B−**. The two SMT hold-down contacts are explicit NC mechanical pads. Native land patterns, imported courtyards and OBJ/STEP asset bytes remain intact. The supplier STEP fuses plastic and contacts; geometric landing-region checks cannot independently identify each metal terminal center.

The old rectangular debug/boot footprints are replaced by separate native Ø1.1 mm bare top-side test points. Their 1.4 mm square courtyards are defined probe-space envelopes, not imported component bodies. Debug supply reference, ground, SWD/WCH interfaces, reset where present and boot access are retained. Bare pads have no purchasing entry, CPL pickup or stencil paste. LED/status, TMP102 temperature sensing and buzzer functions remain present.

All fitted parts, including J_MOTOR, belong in the top-side SMT BOM/CPL. **Eight 0.7 mm USB shell stakes require supplier-approved TOP-side secondary soldering in the 1.6 mm board.** Single-face population does not remove that process step. The three exposed-pad thermal vias require the filled, capped, planarized process specified in the review handoff.

`assembly-preview.circuit.tsx` and `artifacts/top-assembly/assembly-preview.circuit.json` provide an **unrouted visual harness concept** using drawing dimensions for 14HM11-0404S: 35.2 mm maximum body width, 28.2 mm maximum body length, 26 mm front M3 hole pitch and a 24 mm × Ø5 mm shaft. It shows a proposed JST termination and a 6 mm board-to-motor space. The factory drawing specifies bare leads: A+ black, A− green, B+ red, B− blue. The procedural cable colors are illustrative; the pin/net and phase-color table defines the wiring contract. No rear holes or screws are invented, and the view does not verify rear threads, an adapter, stand-offs, fasteners or stock harness compatibility. The routed manufacturing board is `index.circuit.json`.

Before ordering, use the newly generated JLCPCB review files and current hash-bound receipts. The supplier must approve pickup datums/rotations, availability, stencil and secondary soldering. Firmware, USB/PD behavior, motor current, thermal limits and rear mounting remain untested in hardware.

The relocated 1.1 V decoupling network uses reviewed local inner1 paths with the same 15 mm maximum bound as other local MCU rail/clock escapes. The rail is screened at 0.10 A on 17.5 µm internal copper. This requires bench power-integrity verification. The isolated PD-controller R_PD branch is screened at 0.04 A: 35 V / (1 kΩ × 0.99) = 35.36 mA even for a shorted downstream load. This reduced budget is applied only when a physical copper cut isolates that single resistor terminal; shared motor feeders retain 0.75 A.

U_ENCODER (AS5600-ASOM C79815), C_ENCODER and C_ENCODER_BULK are on BOTTOM with Do Not Place set. All three are excluded from purchasing, factory CPL and stencil paste. The optional encoder shares the 3.3 V temperature I²C bus at address 0x36 (TMP102: 0x48). Shaft/magnet dimensions, centering and air gap are unverified; the DNP footprint does not establish rear-motor compatibility.
