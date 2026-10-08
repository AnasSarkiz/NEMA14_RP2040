# RP2040 engineering review — 2026-10-08

This is an engineering-prototype review of the independent **NEMA14_RP2040** project for STEPperONLINE **14HM11-0404S**. The authoritative electrical source is `src/board.tsx`, exposed through `index.circuit.tsx`; authoritative saved copper is `artifacts/board.circuit.json`. Source/netlist changes require rebuilt saved copper, routing checks and regenerated fabrication outputs. A successful source build is not proof of current PCB geometry.

**Qualification status: prototype candidate only; physical operation and manufacturing release are not verified.** Firmware, exact selected TVS/inductor/capacitor qualification, assembled-board measurements and final rear-carrier fit remain outstanding. The engineering objective is to remove software-correctable defects and document the remaining boundaries.

## Findings and dispositions

| Severity / type | Finding and evidence | Resolution or required qualification |
| --- | --- | --- |
| Critical, proven defect | U_PD pin 8 was directly connected to 15 V. WCH CH224DS1 1F §4.3/7.2 specifies series input resistance and 13.5 V absolute limit. | PD-only configuration removes this connection and ties chip DP/DM together, disconnected from connector data, per §5.5. Confirm final source, saved copper and Gerber pin 8 isolation/DP-to-DM continuity. |
| Major, proven margin failure | 100 kΩ ENABLE_N/SLEEP pulls permit 2 V offset under A4988 ±20 µA input leakage; safe default not guaranteed at 3.3 V. | Use 10 kΩ enable pull-up and sleep pull-down; confirm hardware reset/brownout remains disabled and asleep. |
| Major, calculation/evidence defect | Earlier current screening assumed ±5% A4988 accuracy at VREF≈0.6735 V and omitted ±3 µA REF leakage. Allegro specifies accuracy only at VREF=2 V; low-VREF accuracy is not bounded. | Reduce reference-divider impedance to 3.9 kΩ/1 kΩ and retain nominal 0.3508 A. Remove qualified maximum-current claims. Final phase currents, sense offsets and temperature dependence must be measured. |
| Major, bulk sourcing/qualification | Old RVT bulk lacked verified primary ripple/ESR data and cached supplier ripple was only 54 mA at 120 Hz. | Replaced with native JLC C178585 Panasonic EEEFPV101XAP 100 µF / 35 V, rated 0.60 Arms at 100 kHz / 105 °C, 0.39 Arms at 120 Hz. Exact native pad geometry and polarity match. Measure actual ripple/heating; manufacturer limits do not qualify regeneration. |
| Major, layout risk | Driver charge-pump, VREG, motor-bypass and sense-return routes need close physical loops, beyond connectivity/DRC. Allegro application-layout section requires short sense paths and thick returns to the exposed-pad star ground. | Relocate support components and reroute using exact imported pads; review actual saved segment geometry and regenerated all-layer copper, then scope current/sense noise. |
| Major, layout risk | Buck VIN/GND, SW/L, BST and output/FB paths require compact placement and return loops. AP63203 PCB-layout section and Table 2 are authoritative. | Optimize buck cluster and trace/return geometry. Prove saved copper corresponds to new source placement; bench-check ripple, load steps and startup. |
| Major, evidence unknown | Exact SRN4018-4R7M saturation/RMS/DCR and C19077512 SMF18A clamp/energy ratings could not be fetched through the mandatory proxy. | Obtain exact selected manufacturer data and measure switching peaks/regeneration. Do not substitute generic same-name TVS figures. |
| Major, manufacturing defect | Generic export can treat bare PCB interfaces as placeable parts and create inappropriate motor-hole/bottom paste. | Use audited clean assembly BOM/CPL and the chosen USB-shield solder process. Refer to manufacturing-review.md and parsed fabrication evidence; retain interface copper/mask/drill. |
| Major, mechanical unknown | Front 26 mm M3 pattern does not prove rear mounting threads. STEP rear recesses model end-cap screw features. | Separate front-thread carrier/standoff solution; no motor drilling or end-cap screw repurposing. Verify actual motor revision, insulation, lead exit and USB access. |
| Minor, metadata defect | Exact supplier MPNs disagree with old generic capacitor-voltage annotations. | C13585=50 V, C45783=25 V, C1525=16 V, C52923=25 V, C14663=50 V. Record exact imported identity; DC-bias effective capacitance remains unverified. |
| Major, physical qualification unknown | USB pair continuity/short tests do not establish 90 Ω differential impedance, skew, reference continuity, enumeration or flashing. | Review route endpoints, paired sections, layers/vias and return paths; test all cable orientations and power combinations with real USB programming. No controlled-impedance claim. |
| Major, operating-system unknown | Motor-control firmware does not exist; firmware must enforce USB host-presence, PD validation and safe stop/recovery. | Implement and test the state machine described below before operating the motor. Hardware interface availability does not mean a programmed controller is supplied. |

The detailed manufacturer specifications, pin maps, dated source URLs, file hashes and limitations are in [component-evidence.md](component-evidence.md) and [manufacturer-review.json](../references/manufacturer-review.json). Corrective actions listed here must be reconciled against the final netlist/route validation record; this document does not turn an unexecuted test into a pass.

## Operating principle and power tree

Both USB-C openings face outward at the same +Y board edge (Y=17.5 mm), with PD at X=−5.3 mm and DATA at X=+5.3 mm. Their 10.6 mm center pitch requires compact cable overmolds ≤10 mm wide as a clearance-screening gate; check simultaneous straight insertion, retention and carrier/screw/bend clearance using actual selected cables. The PD receptacle is a dedicated sink-power interface. CH224K requests 15 V with CFG1/2/3=0/1/1; PG is open-drain active low. Motor VBUS feeds A4988 VBB1/VBB2 directly. The DATA receptacle supplies computer USB data and host 5 V; its CC1/CC2 each have an independent 5.1 kΩ Rd pull-down. Connector orientation and both duplicated D+/D− contacts must be checked from the native imported footprint.

PD VBUS and DATA VBUS each feed a Schottky diode to LOGIC_IN. The diode OR isolates computer VBUS from the 15 V source. AP63203 converts LOGIC_IN to fixed 3.3 V. RP2040’s internal regulator converts 3.3 V to a separate 1.1 V core rail. Grounds are shared; this is not galvanic isolation.

| Rail / signal | Normal condition | Consumers and limits |
| --- | --- | --- |
| PD_VBUS | Requested 15 V; initial/fallback may be 5 V | A4988 motor supply requires ≥8 V. Intended operating target remains 15 V; bus transients require qualification. |
| DATA_VBUS | Host nominal 5 V | USB ESD rail and diode-OR input; must not be driven by the PD source. |
| LOGIC_IN | Higher source after its Schottky drop | AP63203 recommended 3.8–32 V. Worst DATA-only VBUS/drop/startup must be measured. |
| PD_VDD | CH224K shunt 3.24–3.36 V | CH224 configuration pins; 1 kΩ feed/1 µF bypass, separate from MCU V3V3. |
| V3V3 | Approximately 3.30 V | RP2040 IOVDD/USB/ADC/VREG_IN, flash, driver logic and VREF divider. Buck CCM spec 3.27–3.33 V; RP2040 USB requires 3.135–3.63 V. |
| V1V1 | Approximately 1.10 V | RP2040 DVDD23/DVDD50 only; internal-regulator output must not be tied to 3.3 V. |
| VM_SENSE | Bus/21 while isolation switch ON | 100 kΩ/(10 kΩ || 10 kΩ) when VM switch is ON, with 10 nF output filter. At 15 V nominal 0.714 V; firmware factor21 plus calibration. |
| DATA_PRESENT | NPN collector, active low | LOW means host VBUS present; HIGH means absent when logic powered. Host-domain base feed is isolated from the GPIO voltage through the transistor. |
| VREF | Approximately 0.6735 V | Nominal driver current reference; measured current qualification required. |

## Component functions and pin review

| References | Purpose / governing check |
| --- | --- |
| J_PD, U_PD, R_PD, C_PD, R_PG | 15 V PD contract, CH224 shunt supply and active-low power-good. Physical pin 6 = CC2, pin 7 = CC1; pin8 is an optional protected sense input, not a motor-power pin. |
| J_DATA, R_CC1, R_CC2, U_ESD, R_DM, R_DP | USB sink identification, ESD network and RP2040 27 Ω USB resistors. U_ESD duplicated flow-through IO contacts remain on their correct nets. |
| D_PD, D_DATA, D_TVS, C_BULK | Supply OR isolation, bus surge limiter and 100 µF / 35 V native Panasonic EEEFPV101XAP bulk storage. Manufacturer ripple 0.60 Arms at 100 kHz / 105 °C, ESR ≤0.16 Ω at 100 kHz / 20 °C; actual mixed-frequency ripple/temperature/lifetime and selected TVS repetitive regeneration remain open. |
| U_BUCK, L_BUCK, C_BUCK_IN, C_BUCK_OUT1/2, C_BOOTSTRAP | AP63203 fixed 3.3 V converter. FB1=V3V3, EN2/VIN3=LOGIC_IN, GND4, SW5, BST6. BST capacitor is rated for BST−SW differential, not full bus. |
| U_MCU, C_IO1/10/22/33/42/49 | All six numbered IOVDD pins powered and individually bypassed. Native supplier QFN geometry retained. |
| C_DV23/50, C_VREG_IN/OUT, C_USB, C_ADC | Separate1.1V core bypasses, internal-regulator1µF input/output and USB/ADC bypasses. USB_VDD48 and ADC_AVDD43=3.3V; TESTEN19 and EP57=GND. |
| U_FLASH, C_FLASH, R_FLASH_CS, R_BOOT, J_BOOT | 2 MB GD25Q16EEIGR XIP memory, flash-CS default and ROM BOOTSEL jumper through1k. Flash IO2/IO3 connected for quad mode; boot2/QE configuration must match exact flash. |
| Y_MCU, C_XIN, C_XOUT, R_XOUT |12 MHz ABM8-272-T3; two 15 pF loads assume 2.5 pF stray capacitance for 10 pF effective load, plus 1 kΩ damping. Verify startup and crystal drive≤manufacturerlimit. |
| R_RUN, J_DEBUG | RUN default high, accessible RUN/SWD recovery and debug; programming can also use USB ROM. |
| R_USB_SENSE_H/L, Q_DATA, U_VM_ISO, R_VM_EN/BLEED, C_VM_ISO, R_VM_H/L, C_VM_SENSE | Host and motor-voltage detection, tolerance/calibration and acquisition-settling checks. |
| U_DRV, C_VM, C_DRV_LOGIC, C_CP, C_VCP, C_VREG | A4988 bridge and supply/charge-pump support. GND3/GND18/EP grounded, CP1/CP2=100 nF, VCP/VBB=100 nF, VREG/GND=220 nF; NC7/20/25 remain NC. |
| R_SA, R_SB, R_REF_H/L, C_REF | Two 0.24 Ω current senses and low-impedance current reference/filter. Sense returns must join driver star ground without motor/USB return offset. |
| R_ENABLE, R_SLEEP, J_MOTOR | Hardware disabled/sleep defaults and bare four-wire motor solder interface. MS1/2/3 high fixes1/16microsteps; RESET_N high, ROSC ground selects mixed decay. |

RP2040 control pin allocation: GPIO6 STEP, GPIO7 DIR, GPIO8 ENABLE_N, GPIO9 SLEEP, GPIO10 PD_GOOD, GPIO27 (physical39) VM_ENABLE_N, GPIO28 VM_SENSE and GPIO29 DATA_PRESENT (active low). Physical USB pins46/47 use MCU_DM/MCU_DP through27Ω to connector-side USB_DM/USB_DP. QSPI physical51..56 map SD3/SCLK/SD0/SD2/SD1/SS. Debug SWCLK24, SWDIO25, RUN26.

## Reset, boot and partial-power states

| State | Required behavior |
| --- | --- |
| No power | Driver inactive; no host/backfeed current source. |
| DATA-only | Logic power and USB programming available; motor VBB unpowered, driver remains disabled/asleep. |
| PD at initial/fallback5V | Logic can start; A4988 insufficient motor voltage, firmware keeps disabled. |
| PD15V without DATA | Logic available; motor allowed only after validated PG and calibrated VM. USB pull-up remains disabled without DATA_PRESENT. |
| PD15V plus DATA | Motor control available only with initialized firmware; computer never receives15V VBUS. |
| RUN held low / firmware absent |10k pulls guarantee intended enable-high/sleep-low leakage margin; motor off. |
| BOOTSEL | J_BOOT pulls flashCS via 1 kΩ during reset, RP2040 ROM USB mode; motor stays off. |
| Cable removal/brownout/reset | Stop accepting motion; return hardware to disabled/asleep. Regenerative-energy handling must be measured; abrupt disable is not automatically a qualified brake. |

The driver requires STEP high/low ≥1 µs, DIR/setup/hold ≥200 ns and ≥1 ms after leaving sleep. Initial firmware targets use 5 µs and 2 ms margins. USB firmware, host-power descriptors, missing-PD handling, ADC calibration, current/thermal protection policy and communication timeout behavior are not implemented by the PCB design.

## Calculations, physical routing and remaining boundaries

[Motor compatibility](motor-compatibility.md) records resistance/inductance corners, current formula bounds and initial motion targets. Expected valid sine-table cold winding copper loss is approximately 3.076W total; 6.15W is a conservative both-phases-at-peak allocation, not normal DAC behavior. 15 V current regulation is compatible with 10 V winding nameplate voltage; 15 V direct winding excitation would not be equivalent.

AP63203 Table 2 recommends3.9µH/10µF/2×22µF/100 nF.4.7µH falls within the manufacturer general 2.2–10µH guidance. Ideal CCM ripple at 15 → 3.3 V is 0.498 A peak-to-peak; actual light-load PFM/DCM peaks require measurement and exact inductor data. Manufacturer 89 °C/W thetaJA is for a single-layer 2 oz reference test board and cannot be treated as the thermal resistance of this actual motor-mounted assembly. Driver 32 °C/W thetaJA similarly refers to a JEDEC four-layer test board. Neither generic theta nor power loss arithmetic establishes actual junction temperature.

Copper width/current screening must use actual saved segments, assigned net currents, external/internal copper thickness and via barrels, not nominal JSX widths. The four-layer arrangement is top/inner1 GND/inner2 signals/bottom, with one explicit local V3V3 bypass on inner1 between IOVDD10 and C_IO10. The 0.16 mm bridge uses two ordinary 0.4/0.2 mm vias and avoids the former 48.821 mm supply detour. The source inner1 GND pour remains one connected 987.169 mm² region. The V3V3 bridge’s own source clearance slot is at least 2.436 mm from projected USB/QSPI copper; that figure does not cover every ground cut introduced by the full repair. The actual CAM bridge-containing ground-loss component, including its new via/refill contour, has a 2.348 mm minimum QSPI centerline distance. Independently parsed CAM, including physical drill geometry, reports one 979.038 mm² planar GND region and no USB/QSPI copper crossing any added cut. Across all repair cuts, the nearest QSPI_SD3 centerline is 0.222 mm away, with 0.142 mm trace-edge separation. These are cross-layer projection distances, not same-layer copper-clearance criteria or high-frequency return qualification. Pours and signal return paths must remain continuous through source/routing updates. USB 0.16 mm width and zero shorts do not establish differential impedance. Ground current sharing, sense offset, QSPI timing and copper thermal spreading require physical/system verification.

## Actual saved critical-route measurements

The following measurements bind to saved board SHA `d85469ebd8679aae5cb6dc012b8552db9f2bb5a4a3a459f8b5645419adfe31ea` and [critical-route-review.json](../artifacts/validation/critical-route-review.json). Direct-route lengths use the actual full saved polyline with both physical port IDs; composite lengths follow current same-net centerlines with native pad/via contacts. They exclude pad spreading and vertical via-barrel distance and do not measure switching-loop area, inductance, impedance or noise. The historical seed report is not treated as proof that a seed survived the final router.

| Physical connection | Planar length, mm | Actual width, mm | Layers / vias |
| --- | ---: | ---: | --- |
| U_DRV.CP1 → C_CP.pin1 | 2.097 | 0.160 | top; 0 vias |
| U_DRV.CP2 → C_CP.pin2 | 2.056 | 0.160 | top; 0 vias |
| U_DRV.VCP → C_VCP.pin1 | 2.155 | 0.160 | top; 0 vias |
| U_DRV.VREG → C_VREG.pin1 | 4.059 | 0.160 | top; 0 vias |
| U_DRV.SENSE1 → R_SA.pin1 | 2.304 | 0.300 | top; 0 vias |
| U_DRV.SENSE2 → R_SB.pin1 | 2.490 | 0.347 | top; 0 vias |
| U_DRV.VBB2 → C_VM.pin1 | 2.872 | 0.353 | top; 0 vias |
| U_DRV.VDD → C_DRV_LOGIC.pin1 | 3.376 | 0.160 | top; 0 vias |
| U_MCU.IOVDD10 → C_IO10.pin1 | 5.723 | 0.160–0.227 | inner1/top; 2 vias |
| U_BUCK.VIN → C_BUCK_IN.pin1 | 2.546 | 0.300 | top; 0 vias |
| U_BUCK.BST → C_BOOTSTRAP.pin1 | 1.775 | 0.160 | top; 0 vias |
| U_BUCK.SW → C_BOOTSTRAP.pin2 | 3.289 | 0.348 | top; 0 vias |
| U_BUCK.SW → L_BUCK.pin1 | 3.531 | 0.600 | top; 0 vias |
| L_BUCK.pin2 → C_BUCK_OUT1.pin1 | 4.953 | 0.300 | top; 0 vias |
| L_BUCK.pin2 → C_BUCK_OUT2.pin1 | 8.908 | 0.300 | top; 0 vias |
| U_BUCK.FB → C_BUCK_OUT1.pin1 | 11.889 | 0.204–0.300 | inner2/top; 2 vias |
| U_DRV.VBB1 → C_VM2.pin1 | 6.126 | 0.399 | bottom/top; 2 vias |
| U_DRV.GND → U_DRV.EP | 1.200 | 0.419 | top; 0 vias |
| U_DRV.GND18 → U_DRV.EP | 1.200 | 0.419 | top; 0 vias |

**Local bypass correction implemented:** the removed IOVDD10 seed has been replaced by the measured 5.723 mm top/inner1 path, with two ordinary 0.40/0.20 mm vias and actual 0.160–0.227 mm trace widths, replacing the former 48.821 mm supply detour. Only its bounded V3V3 bridge is allowed on inner1; [rp-iovdd10-local-clearance.json](../artifacts/validation/rp-iovdd10-local-clearance.json) records native clearance, the single connected 987.169 mm² source inner1 GND pour and at least 2.436 mm projected USB/QSPI separation from the bridge’s own clearance slot. The [independently parsed CAM comparison](../artifacts/manufacturing/inner1-local-bridge-review.json) separately distinguishes the actual bridge-containing cut (2.348 mm minimum QSPI centerline distance) from every added ground cut from the repair: no projected fast-signal copper crosses a cut, while QSPI_SD3 has the nearest centerline/edge distances of 0.222/0.142 mm. The guard preserves this exception rather than opening inner1 to general signals. Ground continuity and geometric separation do not qualify high-frequency return impedance. Buck FB sensing uses its actual rerouted path rather than the historical top-only seed. Scope regulator ripple/startup/load response and MCU rail transients after assembly.

Driver ground pins3/18 now have direct top copper to the exposed pad, approximately 1.2 mm long and 0.419 mm actual saved width. Earlier correction metadata used 0.3 mm before thermal width adjustment. Sense paths/ground-star noise and ground current sharing still need measurement.

## Official native CLI disposition

The latest actual `tsci check netlist`, `pin_specification` and `source` checks on `index.circuit.tsx` exit 0. `tsci check placement` on the source JSON exits **1**, reporting **two courtyard overlaps and seven 180° orientation suggestions**, while its placement DRC summary reports **0 errors and 0 warnings**. Exact command/output/source binding is in [native-cli-final/results.json](../artifacts/validation/native-cli-final/results.json); the advisory result is retained, not rewritten as a pass.

The reported overlaps are J_BOOT/U_ESD (0.5 mm) and C_VM_SENSE/J_DEBUG (0.12 mm). J_BOOT/J_DEBUG are bare PCB contacts; automatic rectangular courtyard overlap is evaluated against actual native pad clearance, fitted STEP bodies and Ø0.5 mm top probe access. Native physical checks provide that separate geometry/access evidence, and actual pad/copper/CAM checks remain mandatory after any repair. No fitted body or access is assumed safe from the generic-box analysis alone. Airwire suggestions rotate C_IO10, C_IO22, C_IO42, C_FLASH, R_RUN, R_VM_BLEED and D_TVS; current actual routed paths, physical pads and final CAM determine connectivity instead of unrouted airwire orientation heuristics. No blanket zero-findings or official placement CLI exit 0 claim is made.

## Validation evidence and prototype gate

Final software results must be taken from regenerated evidence for this review revision, including typecheck, source compilation, schematic placement, saved-board DRC/ERC, physical connectivity, every Gerber copper layer, copper/current audit, parsed mask/paste/drill/outline, BOM/CPL and 3D alignment. See [manufacturing-review.md](manufacturing-review.md), [validation.md](validation.md), and the current files in `artifacts/validation/`. Historical 2026-10-07 reports do not validate newly changed placement or connectivity.

The reproducible calculator evidence is [motor-electrical-calculations.json](../artifacts/validation/motor-electrical-calculations.json); manufacturer document hashes and unverified specs are in [manufacturer-review.json](../references/manufacturer-review.json). Current stock, prices, assembly-class fees and a final supplier order quote are not verified.

Actual USB enumeration/flashing, rails, current accuracy, PD/fallback/backfeed, thermal behavior, regeneration and rear-carrier fit remain **NOT EXECUTED**; [bringup-checklist.md](bringup-checklist.md) defines the measurements. **No production-readiness, issue-free-operation or physical-test claim is made.**

## MCU input protection correction and sequencing qualification

The original direct DATA/VM dividers could drive GPIO above its unpowered-rail absolute limit; current-limit resistors did not provide a published injection allowance. Current source corrects that topology with **native C94514 NPN host detection** and **native C131992 SN74CBTLV1G125DCKR VM isolation**, matching manufacturer pin assignments. See [power-sequencing-correction.json](../artifacts/validation/power-sequencing-correction.json) and retained [initial defect evidence](../artifacts/validation/power-sequencing-audit.json).

Q_DATA pin1 base receives DATA_VBUS through 10 kΩ, pin2 emitter is GND, and pin3 collector is DATA_PRESENT with a 10 kΩ pull to V3V3. **LOW now means host present**, HIGH means absent when logic is powered. Firmware must use this polarity. Switch pin1 OE_N receives VM_ENABLE_N, pin2 A=VM_DIV, pin3 GND, pin4 B=VM_SENSE, pin5 VCC=V3V3; 100 nF local bypass and a 10 kΩ OE pull-up are included. RP GPIO27 physical39 controls OE. Keep it high impedance/HIGH in ROM/reset; assert LOW only after stable V3V3, then wait ≥0.5 ms before ADC sampling. The ON-state bus divider is 100 kΩ over (10 kΩ || 10 kΩ), giving **factor21**, 15 V→0.7143 V and approximately 4.76 kΩ source impedance. Calibrate the actual switched circuit.

TI SCDS057H guarantees Ioff≤10 µA at VCC=0, ports0–3.6 V across −40..85 °C. At a 1% high 10 kΩ bleed this gives ≤0.101 V steady output, below the RP2040 unpowered 0.5 V absolute offset. A 35 V **input-voltage screening case**, not permitted motor operation, gives 3.240 V worst open input at 1% resistor corners and remains within the powered-off port test range. Manufacturer OE pull-up guidance is followed; the switch supply operating range is 2.3–3.6 V.

**Physical sequencing qualification remains a release gate.** Ioff at VCC=0 does not quantify the entire sub-2.3 V transition. The 10 nF output capacitor may retain voltage during fast V3V3 collapse: nominal OFF decay is 100 µs, with a 111.1 µs screening corner for 1% resistance and 10% capacitance. An ideal instantaneous rail collapse can temporarily leave VM_SENSE above IOVDD+0.5 V; DC leakage proof alone cannot clear this condition. Verify hardware reset releases OE before unsafe collapse, and firmware releases OE before planned shutdown/brownout. Scope V3V3, VM_DIV, VM_SENSE, VM_ENABLE_N and DATA_PRESENT during all power orders, attach/removal, fallback and reset, with probe-error margins. Verify unpowered NPN collector voltage, ghost-rail/backpower and host thresholds against exact NPN limits. Add qualified supervision or additional clamping if measured ramps or fast collapse violate pin limits. Firmware and physical tests remain unperformed.

A specific ghost-host boundary also requires testing: PD-only ROM or a USB pull-up may drive a rail-steering ESD path into unpowered DATA_VBUS, potentially asserting the low-threshold NPN detector without an external host. The exact selected ESD primary topology and actual voltages/currents are not yet established; this is a conditional circuit risk, not a measured outcome. Test PD-only reset/ROM/pull-up, host at 0 V connection, DATA_VBUS ghost power and DATA_PRESENT thresholds. Firmware gating does not qualify ROM behavior or a self-triggering detector; stronger guaranteed host-voltage detection or isolation is needed if the boundary fails.
