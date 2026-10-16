# CH224A migration — local version 1.13.0

This electrical and PCB change replaces the fitted CH224K while retaining the original fixed 15 V request. It is implemented in the JSX source, saved PCB, schematic and manufacturing BOM. No hardware operation or fabrication readiness is claimed.

## Component changes

| Reference | Before | After | Reason |
|---|---|---|---|
| U_PD | CH224K, C970725 | CH224A, C42459160 | New PD controller; manufacturer pin assignments verified |
| R_PD | 1 kΩ ERJPA3F1001V, C441922 | 0 Ω 0603WAF0000T5E, C21189 | CH224A uses a high-voltage supply input instead of the CH224K shunt-regulated VDD supply |
| R_PD_CFG | Absent | 56 kΩ, 1%, 0402WGF5602TCE, C25796 | CFG1 resistor configuration requests 15 V |
| C_PD | C15849, 1 µF; incomplete/incorrect voltage metadata | Same C15849, explicitly 1 µF / 50 V | Correct the rating to match the actual fitted Samsung part; no footprint or part substitution |
| R_PG | 10 kΩ pull-up to 3.3 V | Unchanged | This is the PG pull-up, not a VBUS sensing resistor |

## Electrical review

The baseline used fixed I/O straps: CFG1 low and CFG2/CFG3 tied to PD_VDD. This was a CH224K 15 V request; there was no GPIO-based voltage selection. Applying that strap pattern to CH224A would request 20 V. The new circuit uses the datasheet's 56 kΩ resistor mode to preserve 15 V, and leaves CFG2/SCL and CFG3/SDA unconnected. No I2C wiring or new firmware requirement is introduced for this fixed request.

Pin 1 is renamed VHV and receives PD_VBUS through R_PD = 0 Ω. Its bypass net is named PD_VHV. Pin 8 VBUS remains directly connected to PD_VBUS; the baseline has no series VBUS sensing resistor to replace. Pins 6/7 remain CC2/CC1. Pins 4/5 remain DP/DM NC. Pin 10 PG remains an active-low, open-drain indication pulled up to 3.3 V and connected to the original MCU input. CFG1 connects only to R_PD_CFG, avoiding an MCU-voltage tolerance change. The exposed pad remains grounded; the imported native model numbers the manufacturer's EP pin 0 as logical pin11.

## Footprint and PCB scope

The newly downloaded C42459160 import has byte-identical definitions for all ten lead pads and the exposed pad compared with the existing CH224K import. Downloaded STEP and OBJ bytes also match. The existing ESSOP10 land pattern, orientation, grounded exposed pad and thermal via are retained. The 0 Ω replacement has the same pads as the original R_PD. Authentic originals of the three new imports and model hashes are included in the supplier catalog.

All existing component placements, board dimensions, mounting holes, USB positions, land geometry and courtyards are preserved. One 0402 resistor is added in available space. Only the old CFG2/CFG3 supply straps and CFG1 ground connection are removed. Affected supply/configuration branches are routed against the saved copper with foreign-trace rip-up disabled. Ground polygons are cleared locally at changed copper rather than globally refilled. Exact per-board changes are recorded in `artifacts/ch224a-migration`.

## Validation and sourcing limits

`npm run check:pd` verifies the manufacturer pin map, exact two-terminal CFG1 network, 56 kΩ and 0 Ω values, 50 V bypass rating, PG pull-up and MCU connection, and preservation of every existing physical pad and placement against the recorded v1.12.2 Git baseline. `npm run check` includes this guard alongside native DRC. Test receipts and generated manufacturing files contain the current design hash; historical review receipts describe their own older hashes.

[JLCPCB lists CH224A C42459160 for Economic and Standard SMT assembly](https://jlcpcb.com/partdetail/wch-CH224A/C42459160). Its public page does not expose a stock quantity through the available tools. Live assembly stock remains unconfirmed; LCSC retail stock is not used as a substitute. The new resistor identifiers come from exact supplier imports and must also be checked when placing the assembly order. Passive pickup-angle warnings from native export remain subject to JLCPCB confirmation; resistor electrical polarity is interchangeable, but an unchecked machine rotation is not called supplier-approved.

The supplied WCH V2.0 document has an internal contradiction: Section 7.1 calls VBUS 3.8 V tolerant, while Table 8-1 assigns VBUS to the 32 V high-voltage group, the pin table requires VBUS shorted to VHV, and the reference schematics/migration instructions show the direct connection. This implementation follows the pin table, reference circuit and migration instructions. Manufacturer clarification of that inconsistent sentence remains a manufacturing-release blocker.

Hardware still needs charger/PDO fallback testing, PG timing and MCU sampling, supply transient/thermal measurements, effective bypass capacitance at bias, and supplier acceptance of the exposed-pad via process. The new controller's higher maximum supported PD voltage does not change the board's intended 15 V operating point or qualify the rest of the board for 28 V. Rear motor retention, cable/crimp fit and firmware interlocks remain hardware checks.

## References

- [WCH CH224DS1 V2.0 official download page](https://www.wch-ic.com/downloads/CH224DS1_PDF.html)
- [Supplied WCH datasheet PDF](https://done.land/assets/files/ch224a_datasheet.pdf), Sections 4, 5.2, 6.1, 7, 8 and 9
- [CH224A assembly listing](https://jlcpcb.com/partdetail/wch-CH224A/C42459160)
- [0 Ω C21189](https://jlcpcb.com/partdetail/C21189)
- [1 µF / 50 V C15849](https://jlcpcb.com/partdetail/C15849)

The legacy footprint check now uses the frozen published baseline where historical vendor `.original` files were not shipped. The three new imports retain their freshly downloaded originals. Fitted model hashes, all native land patterns/courtyards and the compiled source are checked; optional DNP models are excluded from fitted-model verification.

The full native placement command may return orientation-optimization advisories. Its actual exit code and log are retained; these are not relabeled as an unconditional zero-status pass. Native geometric DRC, actual-copper connectivity and Gerber audits remain separate mandatory checks.

New configuration-resistor positions: RP2040 (-16.45, 11.00) mm, 90 degrees; CH32 (-1.00, 7.30) mm, 90 degrees. The original 0.75 mm resistor-pad-to-board-edge target is retained.

The 56 kohm resistor is also listed for JLCPCB assembly: https://jlcpcb.com/partdetail/26539-0402WGF5602TCE/C25796 . No live quantity is claimed.
