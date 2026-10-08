# RP2040 source BOM review

**67 fitted parts** from the current source catalog. This is a source identity review, not an ordering BOM or live quotation. Final clean assembly BOM/CPL and parsed paste evidence must be regenerated and reconciled against the latest saved copper.

The five newly fitted references are U_VM_ISO, Q_DATA, R_VM_EN, R_VM_BLEED, C_VM_ISO. C_BULK is now 100 µF C178585; R_REF_H/L are 3.9 kΩ/1 kΩ. Existing host-sense resistors are repurposed 10 kΩ base-feed/collector-pull components.

J_MOTOR, J_DEBUG, J_BOOT are bare PCB interfaces and must not be charged or placed as components. Mounting holes and USB shield/manual solder process follow the manufacturing review.

| CID | Exact MPN | Qty | References |
| --- | --- | --- | --- |
| C1525 | CL05B104KO5NNNC | 13 | C_ADC, C_BOOTSTRAP, C_DV23, C_DV50, C_FLASH, C_IO1, C_IO10, C_IO22, C_IO33, C_IO42, C_IO49, C_USB, C_VM_ISO |
| C1548 | 0402CG150J500NT | 2 | C_XIN, C_XOUT |
| C1589 | CL10B103KB8NNNC | 1 | C_REF |
| C2040 | RP2040 | 1 | U_MCU |
| C8598 | B5819W SL | 2 | D_DATA, D_PD |
| C11702 | 0402WGF1001TCE | 2 | R_BOOT, R_XOUT |
| C13585 | CL31A106KBHNNNE | 1 | C_BUCK_IN |
| C14663 | CC0603KRX7R9BB104 | 5 | C_CP, C_DRV_LOGIC, C_VCP, C_VM, C_VM2 |
| C15195 | CL05B103KB5NNNC | 1 | C_VM_SENSE |
| C15849 | CL10A105KB8NNNC | 1 | C_PD |
| C21120 | CL10B224KA8NNNC | 1 | C_VREG |
| C23018 | 0603WAF3901T5E | 1 | R_REF_H |
| C23186 | 0603WAF5101T5E | 1 | R_CC1 |
| C25100 | 0402WGF270JTCE | 2 | R_DM, R_DP |
| C25744 | 0402WGF1002TCE | 2 | R_FLASH_CS, R_RUN |
| C25803 | 0603WAF1003T5E | 1 | R_VM_H |
| C25804 | 0603WAF1002T5E | 8 | R_ENABLE, R_PG, R_SLEEP, R_USB_SENSE_H, R_USB_SENSE_L, R_VM_BLEED, R_VM_EN, R_VM_L |
| C25905 | 0402WGF5101TCE | 1 | R_CC2 |
| C38437 | A4988SETTR-T | 1 | U_DRV |
| C45783 | CL21A226MAQNNNE | 2 | C_BUCK_OUT1, C_BUCK_OUT2 |
| C52923 | CL05A105KA5NQNC | 2 | C_VREG_IN, C_VREG_OUT |
| C94514 | MMBT3904-7-F | 1 | Q_DATA |
| C131992 | SN74CBTLV1G125DCKR | 1 | U_VM_ISO |
| C165948 | TYPE-C-31-M-12 | 2 | J_DATA, J_PD |
| C178585 | EEEFPV101XAP | 1 | C_BULK |
| C441922 | ERJPA3F1001V | 2 | R_PD, R_REF_L |
| C780206 | SRN4018-4R7M | 1 | L_BUCK |
| C780769 | AP63203WU-7 | 1 | U_BUCK |
| C970725 | CH224K | 1 | U_PD |
| C2687116 | USBLC6-2SC6 | 1 | U_ESD |
| C2930216 | FRL0805FR240TS | 2 | R_SA, R_SB |
| C2986331 | GD25Q16EEIGR | 1 | U_FLASH |
| C19077512 | SMF18A | 1 | D_TVS |
| C20625731 | ABM8-272-T3 | 1 | Y_MCU |

Exact capacitor ratings/tolerances are recorded in source supplier-electrical-specs.json; unverified IDs are not assigned guessed ratings. Native import/CAD provenance does not verify stock, manufacturer geometry, derating or PCBA quote. See [supplier CAD](supplier-cad.md), [manufacturing review](manufacturing-review.md), and [component evidence](component-evidence.md).
