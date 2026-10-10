# Variant comparison — 2026-10-10 routing revision

| Feature | CH32 | RP2040 |
|---|---|---|
| MCU | CH32X035G8U6 | RP2040, external flash and crystal |
| Board | 35 × 35 mm, 2 layers, top assembly | 35 × 35 mm, 4 layers, top assembly |
| Fitted parts | 45, including manual motor header | 68, including manual motor header |
| Main phases / PD | ≥0.45 mm, top/bottom wire segments only | Same |
| Phase routing vias, A+/A−/B+/B− | 1 / 1 / 2 / 3 | 1 / 1 / 1 / 1 |
| PD routing vias across all branches | 3 | 10 |
| Actual minimum PD via transitions to VBB1 / VBB2 | 2 / 0, from either VBUS pad | 2 / 2, from either VBUS pad |
| Sense wires | ≥0.30 mm, outer layers | Same |
| Sum of sense trace/barrel resistance / 240 mΩ shunt, A / B | 3.66% / 1.40% | 9.55% / 20.94% |
| Logic supply | HT7533-1: official 30 V operating / 33 V absolute; mounted thermal/transient qualification pending | AP63203, exact Bourns SRN4018-4R7M; bias-capacitance, stability and current qualification pending |
| Type VII filled/copper-capped SMT vias | 3 | 4, including C_USB GND |
| Ordinary 0.20 mm finished-drill vias | 22 | 17 |
| Close off-pad ordinary barrels requiring Type VI resin fill/mask cover | 3 | 4 |
| USB | Both openings face +Y, 14 mm pitch, selected Tensility plugs | Same |
| Motor | 14HM11-0404S, keyed PH four-pin header and mating housing fully inside PCB | Same |
| Mounting | Front M3 carrier, insulation, cable restraint and service loop | Same |
| Programming | ROM USB path and WCH debug, hardware unperformed | ROM BOOTSEL USB path and SWD, hardware unperformed |

Via counts and lengths over all branches are different from series-path transitions. The minimum transitions above come from actual parsed copper/drill topology. A strict zero-phase-via target is not met. Short native pin fanouts remain 0.20/0.30 mm within explicit bounds; only main routes use the 0.45 mm floor. See [outer-power-routing.md](outer-power-routing.md) and its source/archive-bound reports.

Sense resistance figures are conservative sums of source trace records and ideal plated barrels at 20 °C, excluding distributed overlap/current sharing and ground-return resistance. They are not measured values or a phase-current prediction. The RP2040 sense-path imbalance must be qualified for current balance and torque; revise the hardware if unacceptable. The A4988 has one shared analog reference and no per-phase current-setting register. The nominal 0.350765 A shunt-only formula and 0.379245 A component-only corner exclude PCB parasitics and driver error at low VREF.

CH32 has fewer parts/layers. Both designs have source/build/native DRC/connectivity, actual CAM/drill/stencil/shorts, A4 browser and mechanical-equivalence evidence for the bound revision. Native placement CLI retains supplier-orientation advisories; saved native DRC reports have zero errors. The installed CLI has no `pcb-style` command; its attempted exit and supported-command inventory are retained rather than represented as a passing style check.

The bulk capacitor uses the corrected Panasonic 7.7 ±0.3 mm body with an 8.3 mm maximum assembly screen including stand-off. JST row Y−14.1 mm gives 0.4 mm full-header and 0.5 mm mating-housing nominal edge margins; documented placement/outline allowances reduce those margins. Pin-row X is −1.5 mm CH32 / +1.7 mm RP2040. Exact internal mating/post profiles and the generic supplier model discrepancy require an actual coupon/sample fit.

The front-mounted carrier and full factory-lead service loop enlarge the host envelope beyond the PCB; follow the mechanical report and harness/carrier drawings for host clearance and mounting loads. Rear end-cap screws are not used. Minimum copper/plating, all Type VI/Type VII/fine-drill processes, pickup centers/rotations, material certificates and factory lead stock require supplier acceptance. Process costs and capability are unverified.

Neither design is released for manufacture or production. Hardware winding current/balance, USB programming/enumeration and 15 V PD, all power transitions, reset/brownout, regeneration/hot-plug, mounted temperatures and full physical fit/retention remain unperformed. Historical clean reports do not validate another changed revision; use the current engineering manifest.
