# NEMA14_RP2040

Separate RP2040 hardware prototype derived from the CH32X035 NEMA14 controller. This project has its own source, routing and package identity; it does not replace the CH32 project.

[GitHub](https://github.com/AnasSarkiz/NEMA14_RP2040) · [tscircuit](https://tscircuit.com/AnasSarkiz/NEMA14_RP2040)

For STEPperONLINE **14HM11-0404S**: 0.9° bipolar motor, 0.40 A/phase, 25 Ω windings, 35.2 mm maximum body width. The 35 × 35 mm four-layer PCB has four 3.2 mm holes at 26 mm pitch. The manufacturer specifies those dimensions for **front** mounting only; rear attachment uses an adapter and remains physically unverified.

- Two top-side USB-C receptacles, openings flush at opposite board edges: CH224K PD sink requests 15 V, separate USB 2.0 data connection to RP2040.
- RP2040 QFN56, 2 MB GD25Q16EEIGR external QSPI flash, 12 MHz ABM8-272-T3 crystal, 27 Ω USB resistors, all supply bypasses and 1.1 V core-regulator reservoirs.
- AP63203WU-7 3.3 V buck, diode-OR inputs from PD and data VBUS. Motor rail is supplied only by the PD port; data VBUS cannot supply the motor.
- A4988 chopper driver: 1/16 stepping, nominal peak phase-current setting 0.351 A. This setting uses 39k/10k VREF and 0.24 Ω sense resistors; 1% divider/sense resistors and the regulator tolerance must be included in the production current review.
- Top-side component assembly; top/inner2/bottom routing, inner1 ground plane and through-vias. The four-layer PCB costs more than the CH32 two-layer version. SWD/reset solder pads, BOOTSEL solder pads (short to GND while resetting), four motor wire solder holes. These pads avoid connector/button cost.

Motor connection: black A+, green A−, red B+, blue B−. Firmware must keep ENABLE_N high and SLEEP low until the negotiated supply is verified. Data-VBUS sensing is required to disconnect the USB device pull-up when the host cable is absent.

```sh
npm ci --legacy-peer-deps
npm run typecheck
npm run source:check
npm run autoroute       # diagnostic copper saved separately
npm run build           # render/check delivery copper, without rerouting
npm run export
npm run shorts
```

See [routing](docs/routing.md), [electrical review](docs/electrical.md), and [firmware interface](docs/firmware-interface.md). **Hardware prototype, not a fabrication release.** No firmware or bench-tested USB, PD, current or thermal behavior is included.

Saved validation: 0 DRC errors, 48 nets connected and no Gerber shorts detected across all four copper layers. Power/ground pin metadata and passive connector/crystal classifications are explicit; current DRC reports zero warnings. [BOM](artifacts/bom.csv), [Gerbers](artifacts/nema14-gerbers.zip) and [top preview](artifacts/pcb-top.png) are included. Exact passive purchasing identities, assembly rotations and the inductor footprint still require assembly review.

## Supplier models and A4 schematics

[Printable A4 schematic](artifacts/schematic-a4.pdf): 13 numbered landscape sheets with chip-purpose notes and every numbered physical pin. All **61/61 fitted components** use exact JLCPCB imports with native land patterns and OBJ/STEP models. Motor/debug/boot connections are bare PCB pads. See [supplier CAD details](docs/supplier-cad.md) and [the import report](artifacts/jlcpcb-import-report.json).

## USB and final validation

[USB programming procedure](docs/usb-programming.md) · [Validation details](docs/validation.md) · [Browser schematic analysis](artifacts/validation/schematic-analysis-ui.png). Both board variants support boot-mode entry through their Data USB-C port; flashing still requires assembled-hardware validation. Current software checks report zero DRC errors/warnings, zero schematic-placement findings and no Gerber shorts. Application firmware remains a separate task.
