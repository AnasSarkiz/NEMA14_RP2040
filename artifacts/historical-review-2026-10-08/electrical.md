# RP2040 electrical design review

Current source: **67 fitted components**, top-side assembly on four copper layers. The [engineering review](engineering-review.md) and [manufacturer evidence](component-evidence.md) record verified specifications, corrective decisions and remaining qualification gates. Latest final routed/copper/CAM checks are pending reconciliation; historical pass counts and trace temperatures are not carried forward as current results.

## Logic, clock and USB

All six RP2040 IOVDD pins, USB_VDD, ADC_AVDD and VREG_IN use 3.3 V. VREG_OUT and DVDD23/50 use the separate 1.1 V internal-regulator output. Required 100 nF bypasses and 1 µF regulator reservoirs are included; TESTEN and the exposed pad are grounded. RUN has a 10 kΩ pull-up and exposed reset pad.

The 12 MHz ABM8-272-T3 crystal specifies 10 pF load; two 15 pF capacitors assume 2.5 pF parasitic capacitance. The 1 kΩ XOUT resistor limits drive. Verify startup and drive level physically. GD25Q16EEIGR provides 2 MB external flash; select a compatible boot stage and quad-enable sequence. The separate Data USB-C port uses 27 Ω MCU series resistors. USB impedance, return continuity, enumeration and flashing require assembled-board tests.

## PD, regulator and motor power

CH224K requests 15 V with CFG1/2/3=0/1/1. PG is open-drain active low. PD-only wiring shorts chip DP/DM and leaves its optional VBUS-sense pin unconnected, avoiding its 13.5 V limit. The 1 kΩ/0.25 W feed and 1 µF bypass support its shunt VDD. A charger must advertise 15 V; 5 V fallback leaves the motor disabled.

Schottky diode ORing isolates PD from host VBUS while powering logic from either port. AP63203WU-7 uses FB1, EN2, VIN3, GND4, SW5, BST6; fixed 3.3 V output, 3.8–32 V input and 1.1 MHz typical switching. The actual native capacitors are **C13585 10 µF/50 V input**, **C45783 22 µF/25 V outputs**, and **C1525 100 nF/16 V bootstrap**. Bootstrap rating applies to BST−SW, not the motor bus. Manufacturer Table 2 specifies 3.9 µH; selected 4.7 µH lies within the general 2.2–10 µH range. Exact inductor saturation/RMS/DCR criteria, capacitor DC-bias capacitance, loop behavior and converter startup still require qualification.

Bulk C_BULK is **C178585 Panasonic EEEFPV101XAP, 100 µF ±20%, 35 V**: 0.60 Arms at 100 kHz/105 °C, 0.39 Arms at 120 Hz/105 °C and ESR≤0.16 Ω at 100 kHz/20 °C. Actual ripple sharing, rear-board heat and lifetime remain measurements. Exact selected SMF18A clamp/energy data and regeneration handling are unqualified; its 18 V name does not imply an 18 V clamp.

## Driver current and safe defaults

A4988 uses a **3.9 kΩ/1 kΩ** divider:

VREF=3.3×1/(3.9+1)=0.673469 V; Itrip=VREF/(8×0.24)=**0.350765 A nominal**.

The 0.24 Ω, 1% native sense resistors dissipate 29.53 mW at nominal peak current. Lowering divider impedance reduced the ±3 µA REF-leakage voltage contribution from 23.88 mV to 2.39 mV. The RP regulator/resistor/leakage formula envelope is 0.337465–0.364518 A, **excluding driver regulation error**. Allegro specifies trip accuracy at VREF=2 V; no guaranteed error bound was found at 0.6735 V. The obsolete 0.3969 A allowance is not a qualified maximum. Measure both phases over every microstep, transient and temperature condition before accepting the motor's 0.40 A limit.

ENABLE_N and SLEEP use 10 kΩ safe defaults. With±20 µA input leakage their maximum static offset is 0.2 V; original 100 kΩ defaults permitted 2 V. Firmware starts disabled/asleep and validates PG plus measured VM before enabling.

## Protected voltage and host sensing

R_VM_H/R_VM_L remains 100 kΩ/10 kΩ at **VM_DIV**, connected to VM_SENSE through native **C131992 SN74CBTLV1G125DCKR**. VM_SENSE has 10 kΩ bleed and 10 nF reservoir; switch VCC has 100 nF local bypass. OE_N is pulled to V3V3 by 10 kΩ and controlled by **GPIO27/physical 39**.

When ON, the two 10 kΩ returns are parallel: **VM=PD/21**, nominal 0.714286 V at 15 V, approximately 4.76 kΩ output source impedance. Firmware asserts OE LOW only after stable logic power and waits≥0.5 ms before sampling. TI Ioff≤10 µA at VCC0, ports 0..3.6 V, gives≤0.101 V steady OFF output with the bleed's 1% high corner. This DC bound does not qualify undefined sub 2.3 V ramp behavior or stored 10 nF output charge during fast rail collapse.

Host detection uses native **C94514 MMBT3904-7-F**, 10 kΩ base feed from DATA_VBUS and 10 kΩ collector pull to V3V3. **DATA_PRESENT LOW means host attached**, HIGH means absent when logic powered. UseGPIO29 as a digital input. Exact NPN leakage/saturation and unpowered collector behavior require primary evidence and measurements.

## Copper, assembly and release boundary

Screen actual saved segments and every copper layer, including package escapes, ground returns, sense offsets and switching loops. Source trace-width annotations do not certify delivered geometry. Current screening requires 35 µm external copper, 17.5 µm internal copper and 20 µm via-barrel plating on 1.6 mm FR-4. IPC-2221/30 °C-rise arithmetic is a screening model, not a motor-heated assembly thermal prediction. Final geometry and CAM evidence must be regenerated after current routing.

All fitted land patterns remain exact native supplier imports. Bare motor/debug/BOOT interfaces are excluded from placement BOM/CPL and paste; thermal-pad vias and USB shield-slot soldering need the documented process. See [manufacturing review](manufacturing-review.md) and [supplier CAD](supplier-cad.md).

Firmware, current accuracy, rail sequencing/fast collapse, USB flashing, PD/backfeed, regeneration, component temperatures and actual rear-carrier fit remain untested. Follow [bring-up](bringup-checklist.md). **Manufacturing release remains blocked.**

## USB connector identification and cable access

Both USB-C openings face outward from the same **+Y edge**. **J_PD** is at X=−5.3 mm and supplies motor PD power; **J_DATA** is at X=+5.3 mm and connects the computer/programming interface. Firmware roles and signal pin assignments are unchanged by this placement. The 10.6 mm port-center pitch requires compact overmolds **≤10 mm wide** as a screening gate; verify both selected cables fit simultaneously and clear the carrier, screw heads and bend path before operating the prototype.
