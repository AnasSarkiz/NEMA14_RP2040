# Variant comparison — independent engineering revision, 2026-10-10

Both requested baseline commits were inspected locally: CH32 `d75e2c9b9cf83313d7fda65f32b942dcada092dd`, RP2040 `f3811f8a1722df5bad88abdf638cb14bca0c5d59`. Final source/artifact identities and exact validation receipts are in each current engineering manifest. Historical receipts do not validate these changed boards.

| Feature | CH32 | RP2040 |
|---|---|---|
| MCU | CH32X035G8U6 | RP2040 with external flash/crystal |
| PCB and assembly | 35 × 35 × 1.6 mm, 2 layers, top components | Same outline/thickness, 4 layers, top components |
| Fitted parts including manual JST header | 42 | 66 |
| Logic supply | HT7533-1; proposed total load ≤20 mA | AP63203; proposed total load ≤100 mA |
| Winding reference/shunts | 6.2 kΩ / 1 kΩ; unchanged 0.24 Ω | Same |
| Winding current | 0.238715 A nominal; measured/calibrated peak ≤0.25 A | Same |
| VM monitor | Passive; scale 223.76596, RC 4.47 µs, powered-off voltage screen <0.160034 V | Same |
| Exact protection | Littelfuse SMF4L16A, ST USBLC6-2SC6 | Same |
| Main phase/PD routes | ≥0.45 mm, top/bottom | Same |
| Phase vias A+/A−/B+/B− | 1 / 1 / 2 / 3 | 1 / 1 / 1 / 1 |
| PD vias, all branches | 3 | 10 |
| Actual minimum PD series transitions VBB1/VBB2 | 2 / 0 | 2 / 2 |
| Sense routing | ≥0.30 mm, outer layers; 2 / 0 vias | 2.099 / 2.098 mm, 0.30 mm top, no sense vias |
| Sense DC screening at 20 °C | Forward trace/barrel sum only; ground return not included | Forward wires 3.446 / 3.445 mΩ; including plane/barrel return 7.902 / 7.924 mΩ |
| Required Type VII filled/copper-capped SMT vias | 3 | 7 |
| Ordinary 0.20 mm finished-drill vias | 19 | 9 |
| Close off-pad ordinary barrels requiring Type VI resin fill/mask cover | 2 | 2 |
| USB | Both openings +Y; 14 mm pitch; specified Tensility PD/data cables | Same |
| Motor/harness | 14HM11-0404S; keyed JST-PH black/green/red/blue mapping | Same |
| Mounting | Front M3 threads, carrier, barrier, positive harness clamp/service loop | Same |
| Schematic | 3 functional A4 landscape sheets | 4 functional A4 landscape sheets |
| USB programming | ROM boot path/WCH debug; hardware untested | ROM BOOTSEL path/SWD; hardware untested |

The 3.6 V, 25 °C resistor/leakage component-only current screen is 0.268979 A. It excludes resistor temperature changes, unknown low-reference A4988 accuracy and switching ground error; it is not a guaranteed current bound. Measure each phase over microsteps, supply and temperature, and trim the reference if required to meet the 0.25 A acceptance ceiling. Neither shunt was changed to cancel calculated copper resistance.

RP2040 now has short balanced sense wires and direct filled/capped shunt-ground vias into the ground plane. Its DC return screen uses one 17.5 µm inner plane, full 1.6 mm/20 µm-plated barrels, and actual copper/drill geometry. Mesh refinement changes plane resistance by about 2.5%; this is a screening model, not a rigorous bound. The totals are about 3.3% of the 240 mΩ shunts at 20 °C and 11.16 / 11.19 mΩ at 125 °C. Solder/contact effects, shared switching currents, inductance and ground bounce remain unmodeled and require measurement.

Holtek primary Rev 2.81 ratings are 30 V operating input, 33 V absolute input and 150 °C absolute junction; 125 °C is the design target. With the proposed 20 mA ceiling/local 45 °C, the arithmetic screen is about 96 °C junction at 15.75 V, but actual load, full-temperature regulation, dropout and mounted temperature remain unproved. RP2040 uses exact Bourns SRN4018-4R7M, revised Samsung CL32B106KBJNNNE input and three CL21A226MAQNNNE output capacitors. Typical DC-bias curves and separate tolerance/temperature/endurance screens do not guarantee aged effective capacitance or converter stability.

Main power routes satisfy the outer-layer policy with individually bounded native pin escapes. Phase vias remain and are explicitly disclosed. Series transitions differ from all-branch via counts. Native routing and official FreeRouting attempts were followed by local copper repairs; final source and actual CAM connectivity, widths and clearances are the acceptance evidence.

Both boards pass fresh typecheck/build, zero-error native DRC, physical connectivity, trace widths, real Gerber shorts, actual CAM copper/drill/clearance/mask/paste audits, functional silkscreen, native mechanical review and project schematic-browser checks. One generic Q_DATA power-pin warning and supplier placement/pickup advisories remain disclosed. The installed CLI lacks `pcb-style`; official IDE/WebGPU/electrical simulation was not performed.

Both preserve the corrected Panasonic 7.7 ±0.3 mm bulk-capacitor body plus 0.3 mm assembly allowance. The keyed header/mating housing remain inside the board; manufacturer-derived bores are unchanged. Generic CAD post dimensions require exact factory evidence or a real insertion coupon. Full reserved host envelope is approximately 49.204 × 157.480 × 102.771 mm, before host tolerances, movement and access. Rear end-cap screws are not used.

The [operating envelope](supported-operating-envelope.md) is a prototype qualification target: 15 V PD, actual phase peaks ≤0.25 A, room 0–40 °C, local PCB air ≤45 °C, motor case ≤60 °C, mechanical returned energy ≤0.10 mJ per stop at ≤1 Hz, no sustained back-driving. No continuous duty, torque or speed is guaranteed. Higher-energy hosts need separately qualified braking/protection.

Neither design is ready to order. Winding current, USB/PD, all power transitions, regeneration, mounted temperatures, buck qualification and full physical fit remain unperformed. Supplier via-fill/cap/fine-drill/slots/stencil/pickup acceptance and material/crimp/splice certificates remain open. This task makes local commits and publishes nothing.
