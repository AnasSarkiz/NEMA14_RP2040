# Sources and provenance

- Original CH32 project: `AnasSarkiz/NEMA17_Controller`, commit `e19f75e` (independently copied source; original project remains unchanged).
- tscircuit 0.0.2759, CLI 0.1.2258: latest npm releases checked during this change, pinned in lockfile.
- RP2040 Raspberry Pi manufacturer datasheet (cached official supplier copy): `references/RP2040.pdf`. Sections 1.4 and 2.9 establish the numbered pin map, power rails, bypasses, 12 MHz USB boot clock and 27 Ω USB resistors. Original https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf . Direct manufacturer website access is blocked in this environment; the cached PDF was read.
- Diodes AP63203 DS41326 Rev 3-2, November 2024: `references/AP63203.pdf`, pin descriptions, component table 2 and PCB layout guidance. https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf . Cached manufacturer PDF was read.
- Abracon ABM8-272-T3, drawing 456603 Rev IR November 2023: `references/ABM8-272-T3.pdf`, 12 MHz / 10 pF load / 50 Ω ESR.
- GigaDevice GD25Q16E Rev 1.2, December 2021: `references/GD25Q16E.pdf`, 16 Mbit, USON 3×2 mm, flash pins and quad-enable behavior. Device-specific boot support requires testing.
- STEPperONLINE 14HM11-0404S: `references/14HM11-0404S.pdf`, retrieved from https://www.omc-stepperonline.com/download/14HM11-0404S.pdf . Electrical ratings and front 26 ±0.2 mm M3 pitch confirmed; rear hole dimensions absent.
- RP2040, AP63203, GD25Q16EEIGR and crystal pad geometry copied from existing cached supplier imports. Numbered pins checked against manufacturer references; assembly/library review is still needed. No generic QFN footprint is substituted for the reduced RP2040 ground pad.

The remaining A4988, CH224K, USB-C and ESD footprints derive from the original project. This is an engineering prototype; exact purchasing identities for passives and the inductor land pattern require final assembly review. No stock check or assembly quote is claimed.


Current fitted parts are genuine JLCPCB imports obtained with `tsci import --jlcpcb --download --use-exact-footprint <C-number>`. `src/jlcpcb-catalog.json` records component-to-part mapping, original import hashes and native OBJ/STEP hashes. No fitted part uses a custom replacement footprint. Earlier KiCad/Eagle references establish pin cross-checks only; they do not define the current supplier land patterns.

Current tools: tscircuit 0.0.2764, CLI 0.1.2261, pinned in the lockfile. WCH evaluation-board reference section 5 documents PC17-high cold-start ROM USB programming. RP2040 and AP63203 manufacturer PDFs used for power/boot/reference checks are cached in the RP2040 project's `references/` directory. The AP63203 PDF is DS41326 Rev 3-2, November 2024, including the fixed-output pin map and PCB layout guidance. Additional direct Allegro/Raspberry Pi document retrieval during this review returned HTTP 403; no new manufacturer qualification is claimed from those failed requests.


Manufacturer evidence collected during the 2026-10-08 engineering review is recorded in `references/manufacturer-review.json` and `docs/component-evidence.md`. Manufacturer-authored Allegro A4988 4988-DS Rev. 5, WCH CH224DS1 version 1F and CH32X035DS0 V2.3 were retrieved from legitimate GitHub document mirrors; source URLs and SHA-256 hashes are recorded. Direct manufacturer/catalog sites remained blocked through the mandatory proxy. Exact TVS/inductor/ESD and capacitor derating qualification is not claimed. `src/supplier-electrical-specs.json` records capacitor ratings from exact cached supplier identities and resistor tolerance by exact F-code MPN; unidentified capacitor ratings are omitted. The local PCB Designer calculation reference is preserved with MIT license and upstream commit at `references/calculators/`.

The review replaces C_BULK with fresh exact native JLCPCB **C178585 / Panasonic EEEFPV101XAP**, 100 µF / 35 V. The official FP-series document dated 2025-09-01 is cached as `references/Panasonic-FP-2025.pdf`; its exact 35 V / 100 µF / D8 row and frequency table verify ripple and ESR ratings. `references/Panasonic-FP-provenance.json` records the primary URL, SHA-256 and native import hash. No custom land pattern is used; exact imported pad geometry and polarity match the removed C72522 part. Live stock/pricing and actual ripple/thermal/lifetime qualification remain unverified.

Native input protection uses C131992 TI SN74CBTLV1G125DCKR and C94514 Diodes MMBT3904-7-F. Exact TI primary SCDS057H is mirrored/cached in references/SN74CBTLV1G125-SCDS057H.pdf; source URL/hash/pin map and partial-power conditions are in manufacturer-review.json. Native imports and hashes are in the catalog. Exact NPN primary data remains a sourcing evidence gate until separately retrieved.
