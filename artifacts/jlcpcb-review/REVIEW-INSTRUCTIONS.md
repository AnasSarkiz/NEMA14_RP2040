# NEMA14_RP2040: JLCPCB engineering review

This handoff is prepared for order review. It is not JLCPCB approval or a production release. No order or payment has been submitted.

Upload `JLCPCB-Gerbers.zip` for the PCB, `JLCPCB-BOM.csv` and `JLCPCB-CPL.csv` for SMT assembly. The BOM contains exact source MPNs and LCSC part numbers. The raw native export is retained separately as historical evidence and must not replace this corrected package. `review-cam.zip` contains the exact CAM and detailed source-identity tables used by the independent audit.

Select 4 layers, 35 × 35 mm, 1.6 mm board thickness, and ENIG for the separate bare top-side test-point pads. Request at least 35 um outer copper, 17.5 um inner copper and 20 um plated via barrels. Copper layer order is F_Cu / In1_Cu / In2_Cu / B_Cu. Both drill files are required: plated drills/slots and NPTH. The four mounting holes are Ø3.2 mm at (±13, ±13), with board-center origin.

The 100 um stencil has independently screened fine-pitch apertures and four windows totaling 60% exposed-pad coverage for the MCU, PD controller and A4988. `Thermal-Via-Process.csv` identifies the actual exposed-pad via positions and drill sizes that require filling, copper capping and planarization. Confirm the supplier's paste/reflow and via-in-pad processes before releasing assembly; these capabilities and costs have not been quoted.

SMT fitted parts: 81. Bottom SMT references: none. Separate bare top-side `TP_*` test points have no purchased component or stencil paste. JST `J_MOTOR` is native SMT BM04B-SRSS-TB(LF)(SN), C160390, and is included in the top-side SMT BOM and CPL. No bottom-side fitted components or JST through-hole leads are present. The functional order is pin 1 A+, 2 A−, 3 B+, 4 B−. The JST mates vertically from +Z.

The **eight USB-C shell tabs require through-hole soldering**. `Through-Hole-Joint-Plan.csv` lists the actual eight joint coordinates for supplier quotation or manual soldering. USB signal pads receive stencil paste; shell slots do not. Do not assume an SMT-only quote includes these joints or that the unsoldered USB tabs provide a qualified cable-retention or shield-ground connection.

CPL coordinates are millimeters about board center, unmirrored board XY for both sides. Rotation is the native imported footprint orientation plus component placement rotation. **Check every polarized part and pin 1 in JLCPCB's placement preview.** `placement-orientation-review.json` lists each actual numbered pad, center, side and rotation; source agreement is not proof of supplier pickup convention. For both USB connectors the imported land-pattern center differs from the body-bounding-box center by 0.975 mm along the mouth axis. Do not silently substitute the body center as the pickup datum.

The preview images show actual corrected mask and silkscreen Gerbers, not the native CAD captions. Dense silkscreen omits captions that cannot fit safely; all fitted references remain in the assembly maps and placement tables. Inspect assembly maps together with the pad-orientation manifest.

Software verification covers source nets, all saved traces/segments/vias, physical connectivity, actual CAM shorts/opens and clearance, pad/mask/drill agreement, stencil geometry, assembly identities, exact outline and mounts, and nominal native STEP mechanical checks. **USB impedance/reference paths, switching loops, sense/ground return behavior, firmware and thermal performance still require engineering and hardware validation.** A working reference board does not prove this implementation works.

Both USB mouths share the +Y edge, with defined 10 mm cable housings at 12.4 mm pitch, giving a 2.4 mm nominal gap. Use M3 DIN 920 screw heads no larger than Ø4 mm. Cable/screw screening is nominal CAD evidence. Verify real plug tolerances, JST mating cable, underside clearance and the mounting stack. Rear-motor compatibility has not been verified.

Supplier review still must confirm exact stock and quote, pickup orientation, via-in-pad and stencil/reflow process, specified stackup/copper, and assembly sides/THT plan. Do not authorize substitutes. Prototype bring-up must verify USB data, 15 V PD, regulator isolation, phase current/thermal behavior, motor, temperature sensor, LEDs and buzzer before production approval.

Strict generic Circuit JSON importers retain inherited metadata compatibility findings, listed in `native-json-compatibility.json`: display offsets stored as numbers instead of strings, null optional ownership, and a generic buzzer source record. Native rendering, physical coordinates and pin/net checks pass; the order package introduces no schema findings and every new paste aperture passes its native schema. No whole-file generic-schema PASS is claimed. These metadata fields do not determine the fabrication or placement coordinates.

Board source SHA-256: `b2703f81acfe5760d8d662183e6180af1577a4f1964f431bf93a420f76781522`. Corrected CAM audit: PASS, zero findings. Electrical source, placement, native footprints/courtyards, copper, masks, drills and outline are preserved.
