# Current variant comparison — 2026-10-09

| Feature | CH32 | RP2040 |
|---|---|---|
| MCU | CH32X035G8U6 | RP2040 +2MB flash/crystal |
| PCB |35×35mm,2layers,topassembly|35×35mm,4layers,topassembly|
| Logic supply |HT7533-1, primary30V operating/33Vabsolute; measured mounted thermal margin pending|AP63203, exactSRN4018-4R7M; effectiveC/stability/current qualification pending|
| Fitted parts |45 including manual motor header|68 including manual motor header|
| USB |Bothsame+Y,14mm pitch,0.4mm protrusion|Same|
| Motor |14HM11-0404S, PH keyed four-pin fully inside PCB + restrained harness|Same|
| Carrier |Front-M3 enlarged carrier, PEEK/temperature-rated barrier, service loop|Same |
| Programming |ROM USB path plus WCHdebug; bench unperformed|ROM BOOTSEL USB path plus SWD; bench unperformed|

CH32 has fewer parts/layers, while RP2040 adds flash/core rail/crystal and converter complexity. Neither is a qualified motor controller. Both require current, USB/PD, sequencing, regeneration, mounted temperature and physical-fit hardware tests. Current models correct the bulk height7.7±0.3mm; original supplier model retained separately. Factory lead/splice/material qualification, biasedC/protection evidence, supplier pickup/rotation preview and VIPPO process acceptance remain explicit gates. Native source/CAM consistency is not supplier or production approval. Refer to the current engineering manifest and reviews in each repository; historical clean reports do not validate a changed revision.

Both preserve manufacturer-derived JST drilling but retain a disclosed generic header-post CAD mismatch; exact internal mating profiles and physical coupon fit remain open. CH32 requires3 filled/capped SMT vias; RP2040 requires4 including the explicit C_USB ground via, plus4 ordinary0.20/0.40mm fine escape vias requiring8:1 drill-process acceptance. The motor factory leads are modeled through an additional separated service loop, enlarging the host envelope substantially beyond the PCB. See the current mechanical report/drawing for exact bounds.

JST row Y−14.1mm on both boards gives0.4mm nominal full-header edge margin and0.5mm for the mating housing. Pin-row X is−1.5mm CH32 /+1.7mm RP2040; actual body/tolerance and fit qualification remains required. See [inside-board-jst](inside-board-jst.md).
