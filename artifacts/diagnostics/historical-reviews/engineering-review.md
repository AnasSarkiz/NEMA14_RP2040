# Independent engineering revision — RP2040, 2026-10-10

Inspected the actual source, CAM/drill ZIP, BOM/PnP and reviews at local commit `f3811f8a1722df5bad88abdf638cb14bca0c5d59` on `fix/serviceable-harness-2026-10-09`. Both requested revisions existed locally. The baseline source and superseded reviews are retained in `artifacts/historical-independent-review-2026-10-10/`. This revision intentionally changes circuit topology and copper; old equivalence-only release claims do not apply.

The proposed [supported operating envelope](supported-operating-envelope.md) is a qualification target for the 14HM11-0404S motor. It supplies conservative limits without assuming an application: 15 V PD, measured phase peaks ≤0.25 A, room 0–40 °C, local PCB air ≤45 °C, motor case ≤60 °C, no external logic load, no continuous back-driving and ≤0.10 mJ mechanical energy per stop at ≤1 Hz. No hardware measurements or production readiness are claimed.

## Implemented electrical changes

- Both designs use 6.2 kΩ/1 kΩ VREF and unchanged 0.24 Ω shunts: 0.238715 A nominal, 0.268979 A component-only high formula at the 3.6 V accepted rail ceiling and 25 °C resistor tolerances. A4988 accuracy at this low reference is unspecified. Resistor temperature coefficients are not included in that 25 °C screen. Measure and adjust the divider if actual peaks exceed 0.25 A; never compensate the shunts for uncertain copper.
- Removed the VM isolation switch, its OE resistor and bypass capacitor. The always-passive 100 kΩ / (10 kΩ ∥470 Ω) monitor remains below 0.160034 V at the 35 V arithmetic screen including 1% resistor corners and 1 µA leakage, even at zero MCU supply. Nominal scale 223.76596 and RC4.47 µs replace the old scale 21/100 µs discharge. Firmware must use analog high impedance without pull-ups. Negative/coupled ringing and real transitions remain bench gates.
- Replaced untraceable TVS/ESD parts with exact Littelfuse SMF4L16A/C1973135 and ST USBLC6-2SC6/C7519 imported supplier footprint/model files. Corrected the TVS orientation for its reversed imported A/K pin order. Primary manufacturer PDFs are retained and hashed.
- TVS26 V maximum at 15.4 A/10–1000 µs/25 °C is a pulse condition, not a fixed operating ceiling. Its temperature coefficient is typical; a guaranteed hot clamp below every protected rating is not established. The operating bus must remain ≤18 V on measured stopping/hot-plug waveforms. A4988/regulator/cap ratings are not regenerative operating targets. Repetitive braking and higher energy need an external qualified subsystem.
- Bulk 100 µF: screen 56 µF after initial−20% and documented endurance−30%; 1.9 mJ winding+mechanical stop budget gives an ideal 17.774 V from 15.75 V. ESR/ESL/cable peaks/repeated stops still require testing. See executable calculation script and JSON.

RP2040 shunts moved next to the driver. SENSE1/2 are 2.099/2.098 mm,0.30 mm top, no sense vias; their ground pads use specified filled/copper-capped barrels into inner 1 GND and the driver EP return. Motor/PD main traces remain outer-layer ≥0.45 mm with individually checked native fanout exceptions. The official native router failed on preserved copper; official FreeRouting was used, then explicit local repairs were made. Router success alone did not establish connectivity or clearances.

The buck input is now exact Samsung CL32B106KBJNNNE10 µF50 V/X7R1210. A third exact CL21A226MAQNNNE22 µF output capacitor raises the nominal bank to 66 µF. Official curves give input≈6.201 µF at 18 V and output bank≈40.819 µF at 3.33 V/25 °C. Separately combining tolerance,±15% temperature characteristic and 12.5%/1000 h endurance change screens≈4.151/24.287 µF; this is not a jointly guaranteed or lifetime bound. Acceptance floors are 4 µF input/24 µF output at operating corners. Manufacturer confirmation or biased/aged sample measurements, startup, loop/load-step/ripple and transient testing remain required.

Bourns SRN4018-4R7M is 4.7 µH±20%, DCR≤84 mΩ,1.9 A Irms at 40 °C rise and 2 A Isat at 30% inductance loss. At 18 V/3.33 V,−20% L and typical 1.1 MHz−6% frequency, ripple screens 0.698 A. The specified 100 mA logic ceiling is not a measured consumption. AP63203 startup/short current limit can reach 3.1 A, above the inductor's 2 A saturation screen; do not qualify overload protection without measurements. Switching-frequency minimum is not guaranteed by the cited typical value.

## Mechanical, harness and fabrication

Preserved 35×35×1.6 mm, existing layer count, top fitted components, +Y USB openings and 14 mm pitch. JST header/mate stay inside the outline. Motor mapping is 1 blackA+/OUT1 A,2 greenA−/OUT1B,3 redB+/OUT2 A,4 blueB−/OUT2B. JSTB4B-PH-K-S(LF)(SN), PHR-4 and SPH-002T-P0.5S supportAWG30–24,OD0.8–1.5 mm. Harness uses specifiedAWG24 PTFE extension, measured factory-lead splice, positive carrier clamp and 12 mm service loop. Assembly order and illustrated mapping are in [mechanical-fit](mechanical-fit.md), [motor-wiring.svg](motor-wiring.svg) and assembly drawings.

Manufacturer-derived 0.75±0.05 mm bores remain unchanged. Generic supplier CAD's 0.6 mm square posts do not establish actual factory post dimensions; the factory mating code alone does not guarantee those manufacturing bounds. A real header insertion coupon/sample or dimensioned factory evidence remains required. No hole enlargement or disguised CAD correction was used to conceal this discrepancy.

Carrier uses motor front M3 threads only. The enlarged installation reservation is approximately 49.204×157.480×102.771 mm before additional host tolerances/motion; it includes both selected USB plugs, bends, harness and service access. Front shaft/fastener access and independent host M3 mounting are necessary. Physical fit, clamp preload/pull strength, solder-tail/barrier clearance, cable-body CAD/PDF disagreement and material certificates remain external qualification gates.

Every actual via process is listed in assembly CSVs. Grounded SMT via-in-pad requiresTypeVII resin fill/copper cap and a planar solderable land; close off-pad fine barrels require listedTypeVI fill/mask cover. USB shell slots are plated milling. Header is manual THT after top reflow; no stencil on THT holes. Supplier pickup centers, rotations, pin 1/polarity and stencil/slot/fill capability require actual preview/coupon acceptance, which is unperformed.

## Presentation and final evidence

PDF export removes background strokes that concealed references and enforces 6.5 pt passive references/values. Q_DATA is a wider pin box with BASE/COLLECTOR separated; TVS and transistor box flags are corrected. Every regenerated PDF page was rasterized and visually inspected. Current source, CAM/DRC/connectivity, mechanical review, archive notes and final manifest must agree; exact validation results are recorded in [validation](validation.md).

Unperformed hardware gates: both winding currents/balance, USB programming/control and PD, all power transitions/reset/brownout, regeneration/hot-plug, biased/aged capacitors and buck stability, mounted temperatures and complete physical harness/USB/carrier fit. Supplier acceptance and material/crimp/splice certificates remain pending. Local artifact checks cannot close these gates.

## Separate installed assembly preview

The additional [assembly entry](assembly-scene.md) uses the documented imported-CAD assembly primitives for the exact NEMA14 motor, carrier, fitted PCB and four-wire/cable hardware. It preserves the reviewed geometry and all electrical/manufacturing hashes. Fresh native CLI/typecheck and WebGL model/frame reviews are recorded separately. Prototype fit and supplier gates above remain open.
