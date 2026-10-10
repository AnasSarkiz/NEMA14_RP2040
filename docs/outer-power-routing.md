# Outer-layer motor and 15 V routing review — NEMA14_RP2040

Current saved-board SHA256: `ea02ea3d5e91a739f12403d7d11a7317891d531808426317c847906b4149e573`.

The old RP2040 review found motor wire segments and a long 15 V route on inner2, with main phase widths below the 0.45 mm source setting. Those main-width and wire-layer violations are corrected. Both boards retain the 35 × 35 mm outline and their existing layer counts. Main motor phases and PD_VBUS use **at least 0.45 mm on top/bottom only**. Sense-current wires use at least 0.30 mm on top/bottom. Ordinary motor/power/sense barrels have at least 0.25 mm finished drills; through-barrel annuli also appear on inner layers, but there are no motor/PD/sense wire segments there.

`npm run build` enforces the saved-copper rule. `npm run check:manufacturing` also enforces it, parses the actual Gerber/drill ZIP, and verifies approved wire strips against exported copper. The checks distinguish native pin escapes, resistor-only leaves and main routes. They fail on an inner-layer power wire or an unproved width reduction; nominal JSX settings alone cannot establish compliance.

| Net | Main minimum (mm) | Wire layers | Main branched length (mm) | Total routing vias across all branches |
|---|---:|---|---:|---:|
| A_PLUS | 0.45 | bottom, top | 8.95 | 1 |
| A_MINUS | 0.45 | bottom, top | 7.61 | 1 |
| B_PLUS | 0.45 | bottom, top | 15.60 | 1 |
| B_MINUS | 0.45 | bottom, top | 17.83 | 1 |
| PD_VBUS | 0.45 | bottom, top | 77.97 | 10 |
| SENSE1 | 0.30 | bottom, top | 11.82 | 2 |
| SENSE2 | 0.30 | bottom, top | 28.46 | 2 |

Lengths and counts above cover all routed branches. They are not a series-path resistance or a count of vias carrying the entire inlet current. The following minimum available transitions come from independently parsed copper islands and actual plated drill barrels. A native plated connector pin is not counted as a routing via. This graph counts available layer changes; it does not establish current division or temperature.

| Net | Native path | Minimum available routing-via transitions |
|---|---|---:|
| A_PLUS | U_DRV.OUT1A → J_MOTOR.A_PLUS | 1 |
| A_MINUS | U_DRV.OUT1B → J_MOTOR.A_MINUS | 1 |
| B_PLUS | U_DRV.OUT2A → J_MOTOR.B_PLUS | 1 |
| B_MINUS | U_DRV.OUT2B → J_MOTOR.B_MINUS | 1 |
| PD_VBUS | J_PD.VBUS1 → U_DRV.VBB1 | 2 |
| PD_VBUS | J_PD.VBUS1 → U_DRV.VBB2 | 2 |
| PD_VBUS | J_PD.VBUS2 → U_DRV.VBB1 | 2 |
| PD_VBUS | J_PD.VBUS2 → U_DRV.VBB2 | 2 |

The retained phase vias are a disclosed compromise of the exact fine-pitch A4988 footprint, fixed connector pin order and dense 35 mm board. They are reviewed standard barrels rather than fine quiet-net vias. Through-via parasitics and plated-barrel quality still require fabrication and hardware qualification. The designs do not meet a zero-phase-via target; a strict zero-via requirement would require another placement/routing revision.

Short native driver/USB pin escapes remain narrower than the main routes. Each is positively checked for the exact native starting pin, width, maximum length and a complete joint to either a standard 0.25/0.50 mm barrel or a full-width top-layer route. A barrel is removed only when the complete escape endcap is already covered by top main copper, every native power pad remains in one physical island and every remaining power trace/via remains anchored. The resistor-only 0.16 mm leaves are independently proven by removing their exact copper records: only the resistor input separates while both inlet and driver supply pins remain together.

| Native escape | Width (mm) | Actual / maximum length (mm) | End connection |
|---|---:|---:|---|
| U_DRV.OUT1A | 0.30 | 0.702 / 2.00 | standard_0p25_0p50_barrel |
| U_DRV.OUT2A | 0.30 | 0.702 / 2.00 | standard_0p25_0p50_barrel |
| U_DRV.OUT1B | 0.20 | 1.567 / 2.00 | standard_0p25_0p50_barrel |
| U_DRV.OUT2B | 0.30 | 1.051 / 2.00 | standard_0p25_0p50_barrel |
| U_DRV.VBB1 | 0.30 | 1.870 / 2.00 | standard_0p25_0p50_barrel |
| U_DRV.VBB2 | 0.30 | 0.749 / 2.00 | standard_0p25_0p50_barrel |
| C_VM.pin1 | 0.30 | 0.800 / 2.00 | standard_0p25_0p50_barrel |
| J_PD.VBUS1 | 0.30 | 1.250 / 1.25 | standard_0p25_0p50_barrel |
| J_PD.VBUS2 | 0.30 | 0.901 / 1.25 | full_endcap_direct_top_main |

The narrow OUT1B escape is 0.20 mm; other listed driver escapes are 0.30 mm. Driver escapes are bounded to 2 mm and USB VBUS escapes to 1.25 mm. The 0.40 A winding and 0.75 A PD arithmetic screens assume external copper at least 35 µm and barrel plating at least 20 µm. An IPC-2221 estimate below the 30 °C screen does not verify a mounted temperature, pulse current, regeneration or a fabrication stackup.

## Current-sense parasitics and remaining electrical qualification

The A4988 sense pins carry winding current. The nominal 0.350765 A and component-only 0.379245 A high-corner formulas use the 0.24 Ω shunts alone; they exclude PCB sense/return resistance, driver accuracy at the selected low VREF and the measured supply/temperature corners. Source-derived sums below conservatively count every trace record and via in each sense net. Overlapping pad/trace copper and current sharing are not modeled, so these are screening data rather than predicted measured phase currents.

| Sense net | Sum of trace resistance at 20 °C (mΩ) | Sum of ideal barrel resistance (mΩ) | Total / nominal 240 mΩ shunt |
|---|---:|---:|---:|
| SENSE1 | 19.415 | 3.512 | 9.55% |
| SENSE2 | 46.737 | 3.512 | 20.94% |

Measure effective shunt/sense/return resistance and peak current in both phases across decay modes, microsteps and mounted temperature. The RP2040 sense paths have larger, unequal arithmetic parasitics; qualify current balance and torque and revise their placement/routing if the measured imbalance is unacceptable. Do not compensate shunt values from unverified copper arithmetic. The A4988 has one shared analog reference and no per-phase current-setting register. Revise the hardware if measured phase balance is unacceptable; keep peak current within the motor's 0.40 A rating including measurement uncertainty and driver error.

New quiet-net fanouts use ordinary off-pad 0.20/0.40 mm vias. `ordinary_via_process.csv` specifies each drill, annulus, aspect ratio and SMT-land margin. Close off-pad barrels require Type VI resin fill and mask cover; the exposed-pad vias retain the separate Type VII copper-capped requirements. Obtain supplier capability, process pricing and coupon/X-ray acceptance before ordering. Native and actual CAM checks reject ordinary drill/paste or drill/SMT intersections; process requirements are not claims of a manufactured result.

Both USB openings still face the same edge, fitted components remain on top, and the entire JST housing/mating housing remains inside the PCB with the documented assembly-tolerance screen. All native component/pad/hole/model geometry is unchanged by this copper revision. The completed mechanical review is rebound only after proving that physical geometry equivalence. The disclosed generic JST-post model discrepancy and supplier pickup/rotation approval remain open.

Required hardware tests remain unperformed: winding current/balance/torque, USB ROM programming and enumeration, 15 V PD behavior, all power orders and brownout/reset, hot-plug and regenerative clamp energy, mounted temperatures, and actual carrier/harness/two-cable fit and retention. This review does not authorize production release.

Schematic-only refresh: all electrical/PCB/CAD records and CAM ZIP bytes are unchanged from the prior routing release. See `functional-schematic-evidence-binding.json`; fabrication checks remain applicable through exact input equivalence.
