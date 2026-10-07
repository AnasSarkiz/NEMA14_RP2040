# Sources and provenance

- Original CH32 project: `AnasSarkiz/NEMA17_Controller`, commit `e19f75e` (independently copied source; original project remains unchanged).
- tscircuit 0.0.2759, CLI 0.1.2258: latest npm releases checked during this change, pinned in lockfile.
- RP2040 Raspberry Pi manufacturer datasheet (cached official supplier copy): `references/RP2040.pdf`. Sections 1.4 and 2.9 establish the numbered pin map, power rails, bypasses, 12 MHz USB boot clock and 27 Ω USB resistors. Original https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf . Direct manufacturer website access is blocked in this environment; the cached PDF was read.
- Diodes AP63203 DS41326 Rev 3-2, November 2024: `references/AP63203.pdf`, pin descriptions, component table 2 and PCB layout guidance. https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf . Cached manufacturer PDF was read.
- Abracon ABM8-272-T3, drawing 456603 Rev IR November 2023: `references/ABM8-272-T3.pdf`, 12 MHz / 10 pF load / 50 Ω ESR.
- GigaDevice GD25Q16E Rev 1.5: `references/GD25Q16E.pdf`, 16 Mbit, USON 3×2 mm, flash pins and quad-enable behavior. Device-specific boot support requires testing.
- STEPperONLINE 14HM11-0404S: `references/14HM11-0404S.pdf`, retrieved from https://www.omc-stepperonline.com/download/14HM11-0404S.pdf . Electrical ratings and front 26 ±0.2 mm M3 pitch confirmed; rear hole dimensions absent.
- RP2040, AP63203, GD25Q16EEIGR and crystal pad geometry copied from existing cached supplier imports. Numbered pins checked against manufacturer references; assembly/library review is still needed. No generic QFN footprint is substituted for the reduced RP2040 ground pad.

The remaining A4988, CH224K, USB-C and ESD footprints derive from the original project. This is an engineering prototype; exact purchasing identities for passives and the inductor land pattern require final assembly review. No stock check or assembly quote is claimed.


Current fitted parts are genuine JLCPCB imports obtained with `tsci import --jlcpcb --download --use-exact-footprint <C-number>`. `src/jlcpcb-catalog.json` records component-to-part mapping, original import hashes and native OBJ/STEP hashes. No fitted part uses a custom replacement footprint. Earlier KiCad/Eagle references establish pin cross-checks only; they do not define the current supplier land patterns.

Current tools: tscircuit 0.0.2764, CLI 0.1.2261, pinned in the lockfile. WCH evaluation-board reference section 5 documents PC17-high cold-start ROM USB programming. RP2040 and AP63203 manufacturer PDFs used for power/boot/reference checks are cached in the RP2040 project's `references/` directory. The AP63203 PDF is DS41326 Rev 3-2, November 2024, including the fixed-output pin map and PCB layout guidance. Additional direct Allegro/Raspberry Pi document retrieval during this review returned HTTP 403; no new manufacturer qualification is claimed from those failed requests.
