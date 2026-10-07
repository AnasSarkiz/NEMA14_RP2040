# Electrical design review

RP2040 is not a drop-in CH32 replacement. All six IOVDD pins, USB_VDD, ADC_AVDD and VREG_IN use 3.3 V. VREG_OUT and both DVDD pins use the separate internal 1.1 V rail. Each IOVDD/DVDD/USB/ADC supply has a 100 nF bypass; VREG input/output each have 1 μF. TESTEN and the exposed pad are grounded. RUN has a 10k pull-up and a debug reset pad.

12 MHz ABM8-272-T3 has 10 pF specified load; two 15 pF capacitors assume about 2.5 pF parasitic load. A 1k XOUT series damping resistor is included. Verify clock startup and drive level on hardware. GD25Q16EEIGR is 16 Mbit/2 MB, 3.3 V USON8. Flash CS has 10k pull-up; both IO2/IO3 are wired to RP2040 for quad mode.

AP63203WU-7 pin map checked against DS41326 Rev 3-2: FB1, EN2, VIN3, GND4, SW5, BST6. Fixed 3.3 V output, 3.8–32 V input, 1.1 MHz. Manufacturer table 2 specifies 3.9 μH, 10 μF input, two 22 μF output and 100 nF bootstrap. This prototype uses a 4.7 μH SRN4018-4R7M, a nearby standard value reducing ripple; verify stability and load-step behavior. FB senses the output directly. Input ceramic must be rated ≥35 V; bootstrap ≥25 V; output ceramics ≥10 V and retain sufficient capacitance after bias. Inductor saturation/ripple-current and exact footprint require purchasing review. Do not populate an adjustable AP63200 in this footprint without changing the feedback network.

Diode ORing keeps PD voltage out of host VBUS. Actual 5 V USB minimum, Schottky drop and buck dropout must be verified. CH224K supplies motor VBUS only; fallback 5 V cannot run the A4988. PG and VM ADC voltage gate firmware enable. 15 V is requested, not guaranteed with every charger/cable.

A4988 VREF = 3.3 × 10/(39+10) = 0.6735 V; Itrip = VREF/(8 × 0.24) = 0.3508 A. The imported 0.24 Ω sense resistors are 1%, 125 mW; nominal dissipation is about 29.5 mW. A 3.33 V regulator bound, 1% divider/sense resistor bounds and a 5% chopper engineering allowance estimate 0.3815 A maximum. Confirm the allowance against the driver specification and measure actual current and temperature. The existing SMF18A clamp still requires regenerative-energy testing.

Only exposed-pad ground vias may sit inside component pads; ordinary vias must clear pads. Component assembly is on top; PCB uses four copper layers: top / inner1 ground / inner2 signals / bottom. Ground is filled on all layers, with inner1 reserved from signal routing. USB is full-speed 12 Mbit/s: matched short pair and continuous ground reference require layout review beyond a generic DRC/short test. No controlled-impedance or EMC compliance claim is made.
