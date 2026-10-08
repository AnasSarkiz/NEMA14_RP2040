#!/usr/bin/env python3
"""Generate the human manufacturing review from the same audited CAM state."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 before=json.loads((ROOT/'artifacts/manufacturing-before/audit.json').read_text());afterpath=ROOT/'artifacts/manufacturing/audit.json';after=json.loads(afterpath.read_text()) if afterpath.exists() else None;manifestpath=ROOT/'artifacts/manufacturing/export-manifest.json';manifest=json.loads(manifestpath.read_text()) if manifestpath.exists() else None;j=json.loads((ROOT/'artifacts/board.circuit.json').read_text());board=next(e for e in j if e['type']=='pcb_board');name=json.loads((ROOT/'package.json').read_text())['name'];nc=sum(bool(i['no_connect_pads']) for i in before['connectivity']['unassigned_island_details']);unknown=[i for i in before['connectivity']['unassigned_island_details'] if not i['no_connect_pads'] and i['area_mm2']>1e-5]
 current_sha=hashlib.sha256((ROOT/'artifacts/board.circuit.json').read_bytes()).hexdigest()
 superseded_source=ROOT/'artifacts/manufacturing-superseded-opposite-edges/source.circuit.json'
 superseded_sha=hashlib.sha256(superseded_source.read_bytes()).hexdigest() if superseded_source.exists() else None
 old_audit_sha=after['source_sha256'] if after else None
 stale=after is not None and (old_audit_sha!=current_sha or old_audit_sha==superseded_sha)
 if stale:after=None
 final=(f'Current same-edge layout manufacturing validation is pending. Earlier actual-CAM audit for `{old_audit_sha}` is **SUPERSEDED** and must not be used for fabrication.' if stale else 'Not yet regenerated; no final manufacturing PASS claimed.') if after is None else f"Independent CAM audit: **{after['status']}** against source SHA-256 `{after['source_sha256']}`. This describes offline CAM consistency, not production qualification or supplier approval."
 rows=[]
 for layer in ['F_Paste','B_Paste']:
  b=before['paste'][layer];a=after['paste'][layer] if after else None;rows.append(f"| {layer}: bare-interface / manual-plated overlap (mm²) | {b['bare_interface_overlap_mm2']:.6f} / {b['manual_plated_joint_overlap_mm2']:.6f} | {a['bare_interface_overlap_mm2']:.6f} / {a['manual_plated_joint_overlap_mm2']:.6f} |" if a else f"| {layer}: bare-interface / manual-plated overlap (mm²) | {b['bare_interface_overlap_mm2']:.6f} / {b['manual_plated_joint_overlap_mm2']:.6f} | Pending |")
 for table in ['bom.csv','pick_and_place.csv']:
  b=before['assembly_tables'][table];a=after['assembly_tables'][table] if after else None;rows.append(f"| {table}: fitted rows / bare rows | {b['rows']} / {len(b['bare_rows'])} | {a['rows']} / {len(a['bare_rows'])} |" if a else f"| {table}: fitted rows / bare rows | {b['rows']} / {len(b['bare_rows'])} | Pending |")
 for label,key in [('100 µm stencil minimum aspect ratio','minimum_aspect_ratio'),('100 µm stencil minimum area ratio','minimum_area_ratio')]:
  b=before['stencil_release_screen'][key];a=after['stencil_release_screen'][key] if after else None;rows.append(f'| {label} | {b:.6f} | {a:.6f} |' if a is not None else f'| {label} | {b:.6f} | Pending |')
 source_components={e['source_component_id']:e for e in j if e['type']=='source_component'}
 usb_centers=', '.join(f"{source_components[e['source_component_id']]['name']}: X{e['center']['x']:.3f}, Y{e['center']['y']:.3f} mm, rotation {e.get('rotation',0)}°" for e in j if e['type']=='pcb_component' and source_components[e['source_component_id']]['name'] in {'J_PD','J_DATA'})
 counts=after['connectivity'] if after else None
 spacing=''
 if after and after.get('actual_copper_spacing'):
  measured=[f"{layer}: {values['minimum_distinct_conductor_clearance_mm']:.6f} mm" for layer,values in after['actual_copper_spacing'].items() if values['minimum_distinct_conductor_clearance_mm'] is not None]
  spacing='Actual finished-CAM minimum spacing between distinct electrical conductors is '+', '.join(measured)+'. The declared 0.15 mm clearance screen allows only the documented 0.0002 mm parser/coordinate tolerance; same-net copper is excluded and native no-connect pads remain separate conductors. Fixed native footprint constraints, if any, require separately documented review.'
 inner1_review=''
 bridge_path=ROOT/'artifacts/manufacturing/inner1-local-bridge-review.json'
 if after and bridge_path.exists():
  bridge=json.loads(bridge_path.read_text())
  if bridge['source_sha256']!=current_sha or bridge['actual_archive_sha256']!=after['archive']['sha256']:raise ValueError('Inner1 bridge review is stale')
  if bridge['fast_signal_segments_over_added_cut']:raise ValueError('USB/QSPI copper crosses the added inner1 cut; electrical review required')
  edge=min(r['minimum_trace_edge_distance_to_added_cut_mm'] for r in bridge['projected_fast_signal_review'])
  qspi_center=min(r['minimum_added_cut_distance_mm'] for r in bridge['projected_fast_signal_review'] if r['net'].startswith('QSPI_'))
  bridge_center=min(r['minimum_centerline_distance_to_bridge_cut_mm'] for r in bridge['projected_fast_signal_review'] if r['net'].startswith('QSPI_'))
  inner1_review=f"The RP2040 local IOVDD10 bypass correction uses one explicitly reviewed V3V3 bridge on inner1, normally the GND reference layer. Run `/workspace/.routing-venv/bin/python scripts/inspect-inner1-bridge.py` after the current CAM audit to reproduce `artifacts/manufacturing/inner1-local-bridge-review.json`. Independent before/after actual-CAM geometry measures {bridge['actual_ground_removed_mm2']:.6f} mm² of removed GND and {bridge['actual_ground_added_mm2']:.6f} mm² of restored GND. The final inner1 GND remains {bridge['ground_after_planar_parts']} planar polygon, with {bridge['actual_ground_after_mm2']:.6f} mm² after physical drill openings. No projected USB/QSPI trace copper overlaps any added ground cut. Across the entire repair, nearest QSPI_SD3 centerline / projected trace-edge distances are {qspi_center:.6f} / {edge:.6f} mm, to the new PD_GOOD via antipad centered at X1.425/Y1.225 mm. This is a projection between layers, not a same-layer copper-spacing violation. The separate actual GND-loss component containing the V3V3 bridge, its via clearances and refill contour has minimum QSPI centerline distance {bridge_center:.6f} mm. The electrical report's 2.4363 mm figure describes only its source-defined bridge slot; it does not apply to the via antipads, full refill contours or all repair cuts. The closer PD_GOOD antipad remains part of the physical signal-integrity qualification gate. All four original Gerber layers were independently rendered and inspected. These geometric checks do not establish impedance, return-current density or EMC performance; physical USB/QSPI qualification remains required."
 cam_iteration=''
 attempt=ROOT/'artifacts/manufacturing-attempt-1/audit.json'
 if attempt.exists():
  cam_iteration='''
A review iteration exposed a saved-Circuit-JSON schema defect missed by earlier connectivity checks: the handcrafted LDO heat polygons contained `brep_shape` but omitted the required `shape: "brep"` discriminator. The official converter silently omitted 9.097909 mm² of top heat copper and 8.423100 mm² on the bottom. The records were corrected to use the required shape and solder-mask fields and current source-net IDs. GND pours also precede the hole-free thermal pours, keeping the converter's global clear-polarity operations from erasing foreign thermal copper. All native land patterns and intended heat geometry are preserved. Actual-CAM/source comparison must prove the restored heat copper. The rejected iteration is retained under `artifacts/manufacturing-attempt-1/` with its actual ZIPs, audit and source hash.

The same iteration exposed a 5.658098 mm² top GND island inside a source polygon attached by a rounding-fragile narrow neck. Ground-fill generation now enforces 0.15 mm minimum neck, splits the geometry into real pieces and keeps only pieces contacting a mapped GND pad or a plated barrel already anchored to a GND pad. The final actual-copper audit must show zero unexpected islands. These source changes correct the manufactured board; they do not hide failed regions in CAM postprocessing.
'''
 text=f'''# Manufacturing review — {name}

Status: **prototype candidate; USER_REVIEW for fabrication and assembly release**. No supplier upload, order, payment, tscircuit publication or production qualification is authorized by this review.

{final}

## Actual-file evidence and corrections

The preserved original archive is extracted at `artifacts/manufacturing-before/`; its `source.circuit.json` is obtained from the pre-review Git HEAD. `audit.json` records every original Gerber/drill SHA-256 and the baseline findings. This audit operates on actual RS-274X/Excellon files, not screenshots or Circuit JSON alone.

| Check | Before | Corrected candidate |
| --- | --- | --- |
{chr(10).join(rows)}

Baseline actual copper agrees with native saved pad/trace/via/pour geometry on all exported layers within 0.0002 mm numerical tolerance. The parsed physical net graph has {before['connectivity']['named_nets_checked']} named nets, zero named-pad opens, and zero named-net shorts. {nc} unassigned islands are intentional imported no-connect pads. {len(unknown)} further unassigned island(s) require correction; see machine report for their layer, area and bounding coordinates. This classification closes a gap in a checker that counts only pad-bearing islands.

The CH32 converter generated through-hole paste despite the saved JSON stencil being cleaned; its bottom stencil contained 12 manual plated joints. The RP converter did not generate bottom paste, but its top stencil still covered bare boot/debug interfaces. Both raw assembly tables included bare interfaces. These are independently measured defects, not inferred from component names.

{cam_iteration}
## Reproducible corrected export

Run `npm run export`, then `npm run check:manufacturing`, then `/workspace/.routing-venv/bin/python scripts/inspect-via-paste.py`, then `/workspace/.routing-venv/bin/python scripts/report-manufacturing.py`. Install the independent parser environment with `/workspace/.routing-venv/bin/python -m pip install -r scripts/requirements-manufacturing.txt`. Required audited parser versions: Gerbonara 1.5.0, PyGerber 2.4.3 and Shapely 2.1.2. Exact installed CLI/core/Circuit JSON/tool versions and each actual copper file's generator metadata are recorded in `artifacts/manufacturing/software-versions.json`; the official CLI embeds its own Gerber converter, which can differ from the separately installed converter package. The export command first invokes the installed official tscircuit CLI and preserves that ZIP as `artifacts/manufacturing-raw.zip`.

The final ZIP is **`artifacts/nema14-gerbers.zip`**. Clean standalone assembly tables are `artifacts/manufacturing/bom.csv` and `artifacts/manufacturing/pick_and_place.csv`, also copied to `artifacts/bom.csv` and `artifacts/pick_and_place.csv`. Fitted rows carry exact catalog MPNs and JLCPCB C-numbers. Bare `J_MOTOR`, `J_DEBUG`, and `J_BOOT` are excluded from automated assembly, while their original copper, masks and drills remain functional interfaces. Every fitted part retains its native imported copper footprint.

`export-manifest.json` records intentional paste, mask, silkscreen and assembly-table transformations. Every copper layer, every plated/nonplated drill file, and the board outline must remain byte-identical to the raw CLI export. The wrapper asserts these hashes; it does not invent new routes or change supplied pad land patterns. The final audit then compares actual Cu to the frozen Circuit JSON and reconstructs cross-layer physical connectivity from copper islands and plated drill barrels.

Gerbonara 1.5.0 does not support standard `%LR` aperture rotations or G85 slots. The analytic adapter applies right-angle LR transforms to corresponding flash apertures and converts unambiguous exported split-line G85 slots into equivalent G00/M15/G01/M16/G05 routing. Unsupported transforms or unknown parser warnings fail rather than silently disappearing. The original CAM bytes remain intact, and PyGerber independently renders original Gerbers with standard LR support. Excellon slot endpoints and CPL positions are rounded to 3 decimals by the exporter; drill comparison permits 0.00055 mm and CPL comparison 0.00051 mm, below any normal mechanical fabrication tolerance.

## Fabrication and assembly process

- 35 × 35 mm outline, 1.6 mm board thickness; {board.get('num_layers',2)} copper layers. Follow the project layer stack and copper-weight assumptions in the electrical/trace review; obtain an actual fabricator stackup before impedance or thermal qualification.
- Four Ø3.2 mm nonplated mounting clearances on a 26 mm square, plus the two USB connectors' native mechanical locating holes. Motor rear threads remain unproven; use only the separately reviewed adapter candidate. Declared Ø5.4 mm screw-head keepouts use true circular geometry in the corrected source, with actual finished-Cu intrusion checked independently on every declared copper layer; native supplier land patterns are preserved.
- USB shell tabs use **eight plated routed slots**, nominal tool width 0.8 mm; native slot lengths and annuli are retained. Ensure the board house treats G85 features as plated milling, not nonplated cutouts. No paste is generated over these slots. Reflow connector signal pins from the top, then manually solder all shell tabs with inspection on both sides. The motor's four wires are also manually soldered after reflow; strain relief is required.
- All fitted components mount on the top. No bottom stencil or bottom component placement is required. Bare boot/debug interfaces receive no stencil paste and no automated component placement.
- The source/archive-bound `artifacts/manufacturing/via-paste-inspection.json` independently compares actual stencil apertures with physical via drill openings and native top SMT pads. It distinguishes the three exposed-pad holes from ordinary vias and rejects ordinary via drills intersecting solder pads or stencil paste. The center thermal/ground via in each QFN exposed pad uses a **filled and copper-capped via-in-pad process (VIPPO)**. Supplier capability, filling/capping quality and cost approval are pending. Do not order untreated open thermal holes under this stencil as if the same assembly process had been qualified.
- Fine-pitch rectangular MCU/driver lead paste uses 90% of native copper dimensions; rounded driver leads use an inscribed rectangle with 90% of the short dimension and a length calculated to remain within rounded copper. This corrects the default 70%-per-axis MCU apertures that fail common 100 µm stencil release screens. Native copper is untouched. The audit measures every actual paste polygon against aspect-ratio ≥1.5 and area-ratio ≥0.66 screens at candidate 0.10 mm foil thickness; these geometric screens do not replace assembler process acceptance.
- Each exposed pad has four stencil windows totaling nominal 60% of native copper-pad area, separated by a 0.20 mm cross-gap. Use an appropriate stencil thickness (prototype candidate: 0.10 mm) and obtain assembler review of aperture release, QFN voiding and connector co-planarity. These cannot be established by DRC.
- Solder-mask openings expand by 0.05 mm where distinct openings retain at least 0.10 mm web. The wrapper reduces expansion locally to guarantee 0.10 mm webs, retaining native openings only if no positive expansion is possible, and records each adjustment in `mask-web-policy.json`. Green LPI process capability and any fine-web exceptions need supplier confirmation. Copper footprints remain unchanged.
- Final silkscreen is clipped 0.15 mm away from solder-mask openings and 0.10 mm inside the board edge. This avoids ink on solderable surfaces; complete unclipped reference labels remain on the assembly drawing. Dense printed labels and pin-1/polarity visibility still require physical preview approval.

## Placement, polarity and supplier interpretation

CPL X/Y coordinates use the imported `pcb_component.center` bounding-box center, board-centered millimeter origin, unmirrored top side, and saved imported-footprint rotation. The audit reconciles every row with this source convention. Current source CPL datums are {usb_centers}. The native local logical/CAD anchor correction is 0.42504355 mm. Exact unchanged supplier USB STEP body-bbox centers differ from native footprint/CPL bbox-center datums by a measured 0.975 mm along each connector's mouth axis; consult the current mechanical report for transformed STEP bounds and CAD anchors. These are distinct datums, and no manufacturer pickup datum or JLCPCB placement preview is available to establish the required conversion. **Treat the CPL as a draft requiring supplier pickup-center and rotation calibration before assembly approval.** Shell-tab/slot fit and exact edge-aligned mouths establish land-pattern/model fit; they do not establish pick-machine datum interpretation.

The exact native MPN/footprint/STEP files, pin labels and center convention provide review evidence. They do not prove that JLCPCB interprets every supplier rotation identically. The supplier placement preview must be compared against the assembly STEP/drawings, particularly MCU and driver pin 1, electrolytic polarity, TVS orientation and both USB mouths. No blanket rotation waiver is claimed.

## Final measurement and remaining gate

{f"Final physical CAM result: {counts['named_nets_checked']} named nets, {len(counts['shorts'])} shorts, {len(counts['opens'])} opens, {len(counts['unconnected_pads'])} missing pads. See `artifacts/manufacturing/audit.json` for every layer's source comparison, actual tool histogram, unassigned island classification, paste coverage and clearances." if counts else 'Final actual-CAM measurement is pending the frozen corrected routing.'}

{spacing}

{inner1_review}

Independent monochrome renders of each copper layer are in `artifacts/manufacturing/independent-render/` (white = copper, black = clear/background). Baseline copper renders are preserved separately. Soldering quality, filled/capped via quality, slot interpretation, stencil release, X-ray QFN voiding, supplier placement interpretation, exact assembled clearance, prices and shipping remain unverified physical/supplier gates. Follow `docs/bringup-checklist.md` for current-limited power-up and qualification. This package is a reviewable prototype candidate and must not be described as production-ready.
'''
 (ROOT/'docs/manufacturing-review.md').write_text(text)
if __name__=='__main__':main()
