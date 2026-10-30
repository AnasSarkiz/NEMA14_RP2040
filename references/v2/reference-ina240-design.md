# INA240 current-telemetry revision

**Local revision 1.0.31 retains the INA240 circuit and [DRV8825 in-pad thermal vias](drv8825-thermal-vias.md), and removes the [external thermal gate](thermal-gate-removal.md).**

Two INA240A1DR (JLCPCB C2060769) replace INA241A1IDDFR. Exact EasyEDA copper, package pin mapping, and CAD model were imported with `tsci import --jlcpcb --use-exact-footprint C2060769`. TI INA240 Table 6-1 permits pin 4 to be grounded; the imported do-not-connect annotation is corrected accordingly.

The two FRM121WFR050TM shunts (C7467249) are 0.05 ohm, 1 W, ±1%, ±50 ppm/°C (verified in the live JLC listing). The library import supplies the footprint/model; the wrapper declares the electrical resistor value because JLCsearch omitted its classification. The independent DRV8825 0.3-ohm regulation shunts and 1 A nominal current limit are unchanged.

20 V/V × 0.05 ohm = 1 V/A. REF1=3.3 V and REF2=GND retain a 1.65 V zero-current midpoint; ±1 A yields 0.65–2.65 V. The shunt dissipates 0.05 W at 1 A. Existing 1 kΩ/10 nF output filtering remains. Application current conversion must use this gain/shunt combination.

Board outline, mounting-hole locations, USB connectors, motor connector, and four-layer stack remain fixed. All parts remain on the top assembly side; the optional bottom encoder remains DNP. Other parts are repositioned to clear the larger SOIC packages. Mounting-hole chips are explicitly DNP so they cannot become assembly placements.

Routing was regenerated with 0.3 mm through-via drills and 0.5 mm pads for new routed vias. Ten earlier explicit MCU/driver vias retain 0.45 mm pads; ten new in-pad thermal vias use 0.50 mm pads. Rules include 0.2 mm via-drill spacing, 0.45 mm plated-hole drill spacing, 0.125 mm via-edge-to-pad clearance, and 0.1 mm trace-to-pad clearance. Independent checks also enforce 0.2 mm via-hole-to-foreign-track/inner-copper clearance. Local Freerouting supplied the initial topology; tscircuit power expansion and local geometry repairs produced the saved final plan. Four top-side Kelvin branches remain separate from load-current copper outside the shunt pads. All six winding-current paths have at least 0.35 mm copper width, with sub-0.5 mm necks shorter than 1.5 mm.

References: https://www.ti.com/lit/ds/symlink/ina240.pdf and https://jlcpcb.com/partdetail/INA240A1DR/C2060769 . Hardware qualification still requires zero-offset/gain calibration and checking motor-switching transients on a physical board.

## Verified final output

- Build and TypeScript: pass. Circuit tests: 21 pass, 0 fail, 2330 assertions.
- `tsci check`: 0 errors, 175 warnings. Native routing checks: 0 errors.
- Gerber-derived shorts check, all four layers: none detected.
- Independent physical audit: all 106 nets connected after permanent internal component contacts; zero shorts, drill-spacing violations, via-hole-to-copper violations, or unmapped copper elements.
- Ground: one physical network, eight retained pours. Removed 104 disconnected pour-only fragments. No ground pad, trace or via was discarded.
- Kelvin audit: all four sense branches pass separation checks.
- Assembly: 101 top-side parts, no bottom assembly; encoder DNP and mounting holes/test points excluded. Both current ICs are C2060769; both shunts are C7467249.

The 175 remaining warnings are 101 catalog lookups, 19 trace-length advisories, 34 imported pin/power/ground metadata warnings, 13 missing courtyards, 5 reference naming warnings, and 3 schematic styling warnings. They are retained in the reports. The trace-length advisories include supply/bypass routes and shared ground paths; zero DRC errors does not establish analog performance or power integrity. The full warning log and per-net physical audit accompany the fabrication files. Supplier assembly orientation must still be checked in the ordering preview; no physical hardware qualification or order has been performed.

The build and fabrication hashes are recorded in `revision-checks.json`. The saved route input and ground-pour geometry guards remain active. This revision has not been published to tscircuit.com.

## Earlier v1.0.29 bottom caution silkscreen (2026-09-28)

Added the exact two-line text `For evaluation only;` / `not FCC approved for resale` on the bottom in the user-marked left-edge strip (top/board coordinates): x=-18.95/-20.05 mm, y=1 mm, rotated 270 degrees, in 0.85 mm type. The two-line block is rotated 180 degrees from its first vertical placement so it reads from the outside edge, retaining the correct line order. It clears the board edge, holes and logo. The earlier horizontal placement between the USB mounting pads was removed. Electrical, component and mechanical geometry is identical to the preceding verified INA240 build. Build, typecheck, native DRC, all-layer Gerber short check and independent copper/drill/ground/Kelvin audits pass after the addition. The preceding circuit regression results remain applicable; they were not rerun for this silkscreen-only change.
