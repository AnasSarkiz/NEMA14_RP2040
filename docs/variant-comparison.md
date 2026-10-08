# CH32 and RP2040 variant comparison

Both variants target the same STEPperONLINE **14HM11-0404S**, a 35 × 35 mm rear PCB on a separate front-thread carrier, two outward-facing USB-C ports on the same +Y edge, CH224K 15 V PD power, A4988 current regulation and top-side assembly. Neither variant is approved for fabrication or physical operation.

| Topic | NEMA14_CH32X035G8U6 | NEMA14_RP2040 |
| --- | --- | --- |
| Fitted component count | **44** | **67** |
| Bare PCB interfaces | Motor, debug, BOOT; excluded from placement | Motor, debug/RUN, BOOTSEL; excluded from placement |
| Copper layers | 2 | 4: top / inner1 GND with one local V3V3 bridge / inner2 signals / bottom |
| MCU startup storage/clock | Internal flash/clock architecture; no fitted external flash or crystal | RP2040 plus external 2 MB flash, 12 MHz crystal, two load capacitors, damping resistor and flash support |
| Dedicated 3.3 V regulator parts | 3: U_LDO, C_LDO_IN, C_LDO_OUT | 6: U_BUCK, L_BUCK, C_BUCK_IN, C_BUCK_OUT1/2, C_BOOTSTRAP |
| Logic power conversion | HT7533-1 linear regulator | AP63203 fixed 3.3 V synchronous buck |
| USB programming path | WCH cold-start ROM ISP plus DIO/DCK debug | RP2040 ROM USB BOOTSEL plus SWD/RUN |
| VM sensing | Protected bus switch, GPIO PB7/physical18 OE, ON conversion ×21 | Same bus switch, GPIO27/physical39 OE, ON conversion ×21 |
| Host detection | Active-low NPN collector, PA3 digital input | Active-low NPN collector, GPIO29 digital input |
| Driver current target | 0.3508 A nominal; actual accuracy unqualified | Same nominal reference/current; actual accuracy unqualified |
| Source BOM/CAD | Exact native JLCPCB imports for all 44 fitted parts | Exact native JLCPCB imports for all 67 fitted parts |

Both port centers are at X±5.3 mm (10.6 mm pitch); compact cable overmolds ≤10 mm wide are a fit-screening requirement, not a verified cable specification. Simultaneous insertion, retention, carrier/screw clearance and cable bend access must be checked on actual assemblies.

The RP2040 MCU bypass repair has one bounded inner1 V3V3 bridge: its actual top/inner1 path is 5.723 mm through two 0.40/0.20 mm vias. The source GND pour remains one connected 987.169 mm² region; the bridge’s own source clearance slot is at least 2.436 mm from projected USB/QSPI copper. The actual CAM bridge-containing cut, including its via/refill contour, has a 2.348 mm minimum QSPI centerline distance. The full independently parsed CAM repair has additional cuts: no USB/QSPI copper projects across any added cut, but nearest QSPI_SD3 centerline/edge distances are 0.222/0.142 mm. The 2.436 mm figure applies only to the bridge slot. These geometry results retain high-frequency return-path qualification as a prototype gate.

The dedicated regulator count excludes general MCU/rail bypasses, common diode-OR parts and common motor/PD circuitry. RP2040's internal 1.1 V regulator and additional MCU bypasses also add assembly work. The five newly fitted input-protection parts are present in both counts: U_VM_ISO, Q_DATA, R_VM_EN, R_VM_BLEED and C_VM_ISO.

**Cost:** CH32 has 23 fewer placements, a simpler startup circuit and two copper layers, so its architecture has fewer cost drivers. RP2040 adds external flash/clock, a switching regulator and four-layer fabrication. No current unit prices, assembly fees, stock or fabrication quotation were verified; component count is not a price estimate. Supplier setup fees, order quantity and assembly classification can change the quoted difference.

**Efficiency and heat:** At a nominal 15 V regulator input, ideal CH32 linear-conversion efficiency is approximately 3.3/15=**22%**, excluding quiescent current. At 5 V input it is approximately **66%**. A 15 mA planning load gives (15−3.3)×0.015=**0.1755 W** loss; 25 mA gives **0.2925 W**. These are load scenarios, not measured system maxima. Typical WCH MCU current is only 4.2 mA at 3.3 V/48 MHz with all peripheral clocks enabled, whereas motor-driver logic adds up to 8 mA. Low total load can make a linear regulator practical, but exact Holtek thermal/tolerance/stability limits and actual motor-heated temperatures remain unqualified.

The RP buck avoids dissipating the full input/output voltage difference in a linear element and is generally preferable for larger logic loads. Its actual efficiency has not been measured or assigned a guaranteed percentage. Its converter, inductor and switching loops introduce ripple, startup and EMI concerns; RP2040/flash consumption can exceed the CH32 load. A more efficient regulator does not by itself prove lower total board power or lower temperature in this assembly.

**Complexity:** CH32 offers the smaller component/assembly scope, while RP2040 provides the Pico SDK/UF2/SWD development path and external 2 MB storage. Both require application firmware, active-low host detection, validated 15 V motor-power gating, default-off VM isolation and safe reset/brownout behavior. RP2040 adds QSPI/crystal/core-rail bring-up and more routing constraints; CH32 adds lot-specific ADC-channel restrictions and unresolved LDO qualification.

**Fabrication readiness:** Each project’s final source/copper/CAM/BOM/CPL/A4/STEP/replay evidence is bound by its engineering-review manifest. Both official PCB-placement checks retain exit 1 advisories despite placement DRC showing 0 errors and 0 warnings: CH32 has three orientation suggestions; RP2040 has seven orientation suggestions and two overlaps involving bare BOOT/debug contact courtyards. Actual native pads, fitted STEP bodies, probe access and routed CAM provide the separate physical disposition. Accept only the final hashes recorded in each manifest; historical clean reports do not validate a changed revision. These offline results do not constitute physical qualification or supplier approval. Both require assembly inspection, actual USB flashing, both phase currents below 0.40 A with uncertainty accounted for, power-order/backfeed/fast-collapse measurements, regulator and motor thermal soak, regeneration tests and physical carrier fit. Exact TVS/ESD/inductor/NPN/temperature evidence remains identified in the manufacturer review.

The Panasonic C178585 bulk capacitor is 100 µF / 35 V with verified ripple/ESR ratings in both variants. Its native CAD is approximately 5.82 mm high although the manufacturer specifies 7.7 ±0.3 mm; the mechanical review screens the manufacturer's maximum envelope and retains **USER_REVIEW**. Rear end-cap screw features are not qualified independent mounting threads.

For a budget prototype, the CH32 variant has the lower parts/layer burden if its measured LDO temperature and exact specifications pass. Choose RP2040 when its development ecosystem or storage/processing requirements justify the additional parts and power/routing work. Neither choice removes the prototype qualification gates.

See engineering-review.md, manufacturing-review.md, mechanical-fit.md, motor-compatibility.md and bringup-checklist.md in each project. No publication, order or fabrication approval follows from this comparison.
