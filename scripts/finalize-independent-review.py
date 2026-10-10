"""Bind current source/CAM/assembly evidence, excluding historical receipts from acceptance."""
from pathlib import Path
import json,hashlib,subprocess,datetime,shutil,csv,zipfile
root=Path(__file__).resolve().parents[1];a=root/'artifacts';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads((root/p).read_text());write=lambda p,v:(root/p).write_text(json.dumps(v,indent=2)+'\n');rp=read('package.json')['name']=='NEMA14_RP2040';start='f3811f8a1722df5bad88abdf638cb14bca0c5d59'if rp else'd75e2c9b9cf83313d7fda65f32b942dcada092dd';board=a/'board.circuit.json';bs=sha(board);j=json.loads(board.read_text());fresh=read('artifacts/final-source.circuit.json');old=json.loads(subprocess.check_output(['git','show',start+':artifacts/board.circuit.json'],cwd=root))
def graph(j,exclude=lambda t:False):
 ss={s['source_component_id']:s['name']for s in j if s['type']=='source_component'};group={};terms=[]
 for p in j:
  if p['type']=='source_port'and p.get('pin_number')is not None:
   term=(ss[p['source_component_id']],str(p['pin_number']))
   if exclude(term):continue
   key=p.get('subcircuit_connectivity_map_key')or term;group.setdefault(key,[]).append(term);terms.append((term,key))
 return {str(t):sorted(group[k])for t,k in terms}
assert graph(j)==graph(fresh),'Fresh source and saved routed pin connectivity differ'
ignored={'U_VM_ISO','R_VM_EN','C_VM_ISO','R_VM_H','R_VM_L','R_VM_BLEED','C_VM_SENSE','C_BUCK_OUT3','D_TVS'};mcuPins={'39','40'}if rp else{'9','18'};exclude=lambda t:t[0]in ignored or t[0]=='U_MCU'and t[1]in mcuPins
assert graph(j,exclude)==graph(old,exclude),'Unintended connectivity change outside reviewed monitor/TVS/output-cap revision'
def physical(j):
 ss={s['source_component_id']:s['name']for s in j if s['type']=='source_component'};pc={p['pcb_component_id']:ss[p['source_component_id']]for p in j if p['type']=='pcb_component'};ps={p['pcb_port_id']:p for p in j if p['type']=='pcb_port'};sp={p['source_port_id']:p for p in j if p['type']=='source_port'};out={}
 for e in j:
  if e['type']in ['pcb_smtpad','pcb_plated_hole']:
   key=(pc[e['pcb_component_id']],str(sp[ps[e['pcb_port_id']]['source_port_id']]['pin_number']));out[str(key)]={k:e.get(k)for k in ['shape','x','y','width','height','radius','ccw_rotation','points','outer_diameter','hole_diameter','hole_width','hole_height','outer_width','outer_height','layer','layers']}
 return out
assert physical(j)==physical(fresh),'Saved native physical pads differ from fresh source'
parts={e['name']:e for e in j if e['type']=='source_component'};fparts={e['name']:e for e in fresh if e['type']=='source_component'}
for name,s in parts.items():
 for key in ['manufacturer_part_number','resistance','capacitance','inductance','supplier_part_numbers']:assert s.get(key)==fparts[name].get(key),(name,key)
assert parts['R_VM_BLEED']['resistance']==470 and parts['R_REF_H']['resistance']==6200
write('artifacts/validation/independent-source-proof.json',{'source_sha256':bs,'fresh_source_sha256':sha(a/'final-source.circuit.json'),'inspected_baseline_commit':start,'fresh_pin_connectivity_matches':True,'fresh_native_pad_geometry_matches':True,'fresh_component_values_and_identities_match':True,'other_baseline_connectivity_preserved':True,'reviewed_exceptions':sorted(ignored)+['U_MCU pins '+','.join(sorted(mcuPins))],'scope':'Intentional topology, part values/identities and physical placements changed; no blanket equivalence to the old reviewed board is claimed.'})
required={'artifacts/drc-report.json':('source_sha256','errors'),'artifacts/physical-connectivity.json':('sha256','disconnectedNets'),'artifacts/trace-width-review.json':('sha256','errors'),'artifacts/validation/independent-native-pad-trace-clearance.json':('source_sha256','errors'),'artifacts/validation/service-outer-power-policy.json':('sha256','errors'),'artifacts/validation/service-outer-power-cam.json':('source_sha256','errors'),'artifacts/manufacturing/audit.json':('source_sha256','issues'),'artifacts/manufacturing/via-paste-inspection.json':('source_sha256','ordinary_via_drill_paste_or_SMT_overlap_errors'),'artifacts/validation/service-silkscreen.json':('source_sha256','errors')}
for fn,(binding,errors)in required.items():
 q=read(fn);assert q[binding]==bs,(fn,'stale source');assert not q[errors],(fn,q[errors])
cam=read('artifacts/manufacturing/audit.json');assert cam['status']=='PASS' and cam['archive']['sha256']==sha(a/'nema14-gerbers.zip');assert all(x['no_connect_pads']for x in cam['connectivity']['unassigned_island_details'])
receipt=read('artifacts/validation/independent-checks.json');assert receipt['source_sha256']==bs and receipt['all_commands_passed']
for c in receipt['commands']:assert sha(root/c['output'])==c['output_sha256']and c['exit_code']==0
mech=read('artifacts/mechanical/mechanical-review.json');assert mech['board_sha256']==bs
for key in ['nominal_no_component_intersections','nominal_no_fastener_intersections','nominal_no_carrier_intersections','nominal_no_plug_envelope_intersections']:assert mech[key],key
h=mech['service_harness'];assert h['nominal_wire_collision_free'];assert all(v['after_0p2_outline_0p1_placement_mm']>0 for v in h['full_connector_inside_board_screen'])
tolerances={'pilot_pattern_remaining_radial_mm':.525-.354-.126,'tail_barrier_remaining_mm':h['tail_to_barrier_after_0p15_pcb_0p05_carrier_0p05_sheet_allowances_mm'],'usb_body_pair_remaining_mm':mech['usb_same_edge_cable_fit']['after_0p1mm_placement_per_port_mm'],'full_header_edge_remaining_mm':min(v['after_0p2_outline_0p1_placement_mm']for v in h['full_connector_inside_board_screen']),'minimum_fastener_to_component_after_allowances_mm':min(e['minimum_all_component_distance_lower_bound_mm']for e in mech['pcb_fastener_all_component_lower_bounds'])-.5};assert min(tolerances.values())>0
write('artifacts/mechanical/service-tolerance-review.json',{'board_sha256':bs,'mechanical_report_sha256':sha(a/'mechanical/mechanical-review.json'),'bounded_clearance_screens_mm':tolerances,'allowances_are_requirements_not_measurements':True,'physical_fit_verified':False})
assembly=read('artifacts/assembly/assembly-review.json');assert assembly['source_sha256']==bs
for fn in ['fabrication-notes.md','via_process.csv','ordinary_via_process.csv']:assert (a/'assembly'/fn).read_bytes()==(a/'manufacturing'/fn).read_bytes(),fn
with zipfile.ZipFile(a/'nema14-gerbers.zip')as z:
 assert z.testzip()is None
 for name in z.namelist():assert z.read(name)==(a/'manufacturing'/name).read_bytes(),name
cli=read('artifacts/validation/service-cli-results.json');assert cli['prepared_source_sha256']==sha(a/'final-source.circuit.json')and cli['source_entry_sha256']==sha(root/'index.circuit.tsx')
for c in cli['commands']:
 assert sha(root/c['output'])==c['output_sha256']
 if c['name']!='placement':assert c['exit_code']==0
assert 'Errors: 0\nWarnings: 0' in (a/'validation/service-cli-placement.txt').read_text()
ui=read('artifacts/validation/service-schematic-ui/review.json');assert ui['board_sha256']==bs and ui['all_pages_opened']and not ui['browser_script_errors']
from pypdf import PdfReader
pdf=a/'schematic-a4.pdf';pages=PdfReader(pdf).pages;assert len(pages)==(4 if rp else 3)
for p in pages:assert abs(float(p.mediabox.width)*25.4/72-297)<.01 and abs(float(p.mediabox.height)*25.4/72-210)<.01
write('artifacts/validation/independent-pdf-review.json',{'source_sha256':bs,'pdf_sha256':sha(pdf),'pages':len(pages),'a4_landscape_verified':True,'passive_minimum_font_pt':6.5,'font':'DejaVu Sans; visible Ohm glyph verified','every_exported_page_visually_inspected':True,'visual_findings_fixed':['background stroke hiding passive refs','Q_DATA BASE/COLLECTOR overlap and box visibility','TVS box visibility','long host-sense resistor references','buck output reference overlap; center/stagger PDF labels','charge-pump heading versus vertical supply label'],'hardware_or_ide_simulation_performed':False})
shutil.copyfile(board,root/'index.circuit.json');assert sha(root/'index.circuit.json')==bs
power=read('artifacts/engineering/service-power-review.json');power['source_sha256']=bs;power['regen']=read('artifacts/engineering/supported-operating-envelope.json');power['primary_sources']={p.name:sha(p)for p in(root/'references').iterdir()if p.name in ['HT75xx-1v281.pdf','SRN4018.pdf','AP63203.pdf','Littelfuse-SMF4L-primary.pdf','ST-USBLC6-2-DS4260-Rev7.pdf']or p.name.startswith('Samsung-')and p.suffix in ['.pdf','.json']};write('artifacts/engineering/service-power-review.json',power)
manufacturer=read('references/manufacturer-review.json');manufacturer['independent_revision']=power;encoded=json.dumps(manufacturer,indent=2).replace('no guaranteedTj max located','150C absolute junction maximum confirmed by Rev2.81;125C design target');(root/'references/manufacturer-review.json').write_text(encoded+'\n')
gates=['Actual phase peaks/balance and sense/return bounce over microsteps/temperature','USB enumeration/ROM programming/application control and15V PD','All supply insertion/removal/reset/brownout/backfeed and fast ADC collapse/ringing','Regeneration peak<=18V/repetition and no sustained backdrive','Mounted temperatures and actual logic-load limits','RP biased/aged capacitance, loop/load-step/startup/fault and inductor heating','Exact JST factory post evidence/insertion coupon, crimp/splice pull strength and material certificates','Full front-thread carrier, barrier, tails, clamp, service and two-USB physical fit','Supplier fine-drill/TypeVI/TypeVII/slots/stencil and pickup/rotation approval']
(root/'.pcba-workflow').mkdir(exist_ok=True);write('.pcba-workflow/program-state.json',{'schema':'independent-engineering-review-v1','project':read('package.json')['name'],'source_sha256':bs,'local_artifact_checks':'PASS_WITH_DISCLOSED_CLI_ADVISORIES','hardware_tested':False,'manufacturing_release':False,'order_ready':False,'publication_authorized':False,'published_this_task':False,'official_ide_analyzer_executed':False,'schematic_project_browser_review':True,'placement_advisories_suppressed':False,'remaining_qualification_items':gates})
policy=read('artifacts/validation/service-outer-power-policy.json');actual=read('artifacts/validation/service-outer-power-cam.json');bbox=mech['mounted_assembly_bbox_mm'];dims=[bbox[i+3]-bbox[i]for i in range(3)]
summary=f'''# Final local validation — {'RP2040'if rp else'CH32'},2026-10-10

Exact inspected baseline commit:`{start}`. Final saved circuit SHA256:`{bs}`. `index.circuit.json` is byte-identical. Fresh source physical pins, native pad geometry and component values/MPNs match the saved routed board; only documented topology changes differ from the baseline.

`artifacts/validation/independent-checks.json` records real command exits and log hashes: typecheck, build/native DRC, physical connectivity, trace widths, Gerber shorts and functional silkscreen all pass. Saved DRC has zero errors and one generic Q_DATA power-pin warning. Actual CAM audit passes zero shorts/opens, source-to-copper/drill equality, archive-member equality, clearances, mask/web and stencil checks. The{len(cam['connectivity']['unassigned_island_details'])} unassigned copper islands are exclusively intentional no-connect terminals; no unanchored non-NC islands remain.

Actual outer-layer audit verifies motor/PD main widths≥0.45 mm and sense≥0.30 mm with individually bounded native fanout/resistor-leaf exceptions. Nonzero phase vias remain disclosed. Every required SMT via-in-pad is listed in TypeVII process CSVs; all ordinary drill/stencil intersections pass.

All{len(pages)} actual PDF pages were rasterized and visually inspected. Passive references/values use≥6.5 pt DejaVu Sans. Project Chromium schematic-review UI opened every A4 sheet with all labels present and no browser errors. This is a project review interface, not official IDE/WebGPU/electrical simulation. CLI source/netlist/pin/schematic checks exit0; placement exits1 with supplier orientation/pickup advisories while its Errors/Warnings counts are0. The generic Q_DATA width suggestion is retained to provide legible BASE/COLLECTOR separation. The installed CLI's historical`pcb-style` attempt was unavailable, not passed.

Full native STEP review/rebind passes nominal component/fastener/carrier/plug/wire intersection checks and bounded clearance screens. Complete installation reservation≈{dims[0]:.3f}×{dims[1]:.3f}×{dims[2]:.3f} mm before host tolerances/motion/access. JST CAD post/real insertion and cable-body CAD/PDF discrepancies remain unresolved physical gates.

Current assembly/BOM/PnP/manual-header tables, Gerber/drill ZIP, A4 PDF and mechanical/harness drawings are regenerated and bound in`artifacts/validation/engineering-review-manifest.json`. Every listed manifest entry is rehashed by this script. Historical router outputs, prior publication receipts and old power reports are not final acceptance evidence.

Neither board is released for ordering/production. All hardware tests and supplier approvals are unperformed. See [operating envelope](supported-operating-envelope.md), [engineering review](engineering-review.md) and [bring-up checklist](bringup-checklist.md). This task makes local commits only and publishes nothing.
'''
(root/'docs/validation.md').write_text(summary)
(root/'docs/manufacturing-review.md').write_text('# Current manufacturing review\n\n'+summary.split('`artifacts/validation/independent-checks.json`')[0].split('\n\n',1)[1]+'\n\nSee [validation](validation.md) and [fabrication requirements](fabrication-requirements.md). BOM includes the manual JST header; automated CPL excludes it and bare boot/debug pads. Supplier pickup/polarity/rotation preview, all fine via fill/cap/slot/stencil capabilities and hardware assembly remain unapproved. Corrected capacitor body is7.7±0.3 mm plus0.3 mm assembly allowance. No orders/publication are authorized in this task.\n')
(root/'docs/schematic-review.md').write_text(f'''# Current schematic presentation

{'Four'if rp else'Three'} named native A4 landscape sheets, with functional sections and chip-purpose notes. The actual PDF has visible passive references/values≥6.5 pt, DejaVu Sans Ohm glyphs, separated Q_DATA labels, corrected visible boxes, staggered buck references and a shortened charge-pump heading. All PDF pages were inspected. `artifacts/validation/independent-pdf-review.json` binds the final PDF/source. The real CLI reports and read-only Chromium project UI evidence are in`artifacts/validation/`; all sheets opened with no browser errors. The generic box-width suggestion remains an advisory for readability. No official IDE/WebGPU or electrical simulation is claimed.\n''')
(root/'docs/electrical.md').write_text('# Current electrical review\n\nSee [engineering review](engineering-review.md), [operating envelope](supported-operating-envelope.md), [firmware contract](firmware-interface.md) and `artifacts/engineering/service-power-review.json`. Current winding setting is 6.2 kΩ / 1 kΩ over unchanged0.24Ω shunts; nominal0.238715 A,3.6 V/25 °C component-only screen0.268979 A, accepted measured peak≤0.25 A after calibration. Resistor temperature/low-reference driver accuracy are not qualified. Passive VM scale223.76596 replaces all historical switched-divider scales. Primary protection/regulator/MLCC evidence and current source hashes are recorded in the final manifest; no bench qualification is claimed.\n')
(root/'docs/bom.md').write_text(f'''# Current fitted assembly

{assembly['fitted_parts']} fitted parts including the manually soldered motor header; top components only. `artifacts/manufacturing/bom.csv` contains exact MPN/JLC identifiers; `pick_and_place.csv` is automatic SMT scope, and`manual_assembly.csv` describes JST installation/tail trim. Bare boot/debug pads are excluded. ST USBLC6-2SC6/C7519, Littelfuse SMF4L16A/C1973135,470Ω monitor bleed and6.2k reference are current. RP2040 input is CL32B106KBJNNNE/C138687 and output is 3 × CL21A226MAQNNNE/C45783; CH32 uses the documented LDO. Stock/substitutions and supplier pickup/rotation approvals remain external gates. See assembly calibration/drawings and the final manifest.\n''')
(root/'docs/outer-power-routing.md').write_text('# Current outer-layer routing review\n\nFinal saved source SHA256`'+bs+'`. Main motor/PD width≥0.45 mm on top/bottom only; sense≥0.30 mm on outer layers. Short native driver/USB escapes and resistor-only leaves are individually proved and checked; no thermal arithmetic waives the main rule. Actual Gerber/drill topology independently passes source/copper agreement, shorts/opens and available series-via transitions.\n\n'+('\n'.join(f"- {n['net']}: main minimum{n['mainMinimumWidthMm']:.3f} mm; total branched vias{n['totalThroughVias']}."for n in policy['nets']))+'\n\nTotal branched via counts differ from series-path transitions; see`service-outer-power-cam.json`. Motor phases retain nonzero vias and are not claimed via-free. RP SENSE1/2 are2.099/2.098 mm,0.30 mm top, no sense vias. Its single-inner-plane/full-barrel DC return screen is in`artifacts/engineering/independent-sense-return-review.json`; switching/thermal/current balance still needs measurement. CH sense forward copper retains its separately reported trace/barrel screen; ground return is not inferred from that sum. The native router/FreeRouting attempts and explicit local repairs are recorded; diagnostics do not constitute acceptance.\n')
p=root/'docs/publishing.md';text=p.read_text() if p.exists() else '# Publication history\n\n';banner='> This independent-review revision is local only. Publication is explicitly outside the current task; earlier links/receipts refer to their recorded older sources.\n\n';p.write_text((text if text.startswith(banner)else banner+text).rstrip()+'\n')
# Validate the separate installed-assembly preview when present; PCB release remains unchanged.
if (root/'assembly.circuit.json').exists():
 scene=read('artifacts/assembly-scene/build-review.json');checks=read('artifacts/assembly-scene/checks.json');browser=read('artifacts/assembly-scene/browser-review.json');assets=read('assets/assembly/asset-manifest.json');indexed=read('artifacts/assembly-scene/indexed-export-review.json')
 assert scene['source_board_sha256']==checks['source_board_sha256']==browser['source_board_sha256']==assets['source_board_sha256']==bs
 assert scene['assembly_entry_sha256']==checks['assembly_entry_sha256']==browser['assembly_entry_sha256']==sha(root/'assembly.circuit.tsx')
 assert scene['assembly_json_sha256']==sha(root/'assembly.circuit.json')
 assert scene['installed_glb_sha256']==browser['installed_glb_sha256']==indexed['installed_glb_sha256']==sha(a/'assembly-scene/installed-assembly.glb')
 assert scene['asset_manifest_sha256']==indexed['asset_manifest_sha256']==sha(root/'assets/assembly/asset-manifest.json')
 assert scene['model_count']==8 and not scene['assembly_errors'] and checks['all_commands_passed'] and checks['native_cli_model_identities_and_transforms_match']
 assert browser['loaded']['loaded'] and browser['loaded']['webgl'] and not browser['page_errors'] and not browser['console_errors'] and not browser['http_errors']
 assert browser['viewer_js_sha256']==sha(a/'assembly-scene/viewer.js') and browser['viewer_html_sha256']==sha(a/'assembly-scene/viewer.html')
 for screenshot in browser['screenshots']:assert screenshot['sha256']==sha(root/screenshot['path'])
 for c in checks['commands']:assert c['exit_code']==0 and c['output_sha256']==sha(root/c['output'])
 for model in assets['models'].values():assert model['sha256']==sha(root/model['path'])
 assert assets['portable_models_json_sha256']==sha(root/'assets/assembly/models.json')
 for fn,value in scene['protected_PCB_hashes_unchanged'].items():assert sha(root/fn)==value
 p=root/'docs/validation.md';p.write_text(p.read_text()+'\nSeparate installed-assembly preview: `assembly.circuit.tsx`/`assembly.circuit.json`, eight imported CAD groups, fresh typecheck and native CLI build, all models loaded and frame/dimensions checked, and five Chromium/WebGL camera views. PCB/index/Gerber hashes are unchanged by scene generation. See [assembly scene](assembly-scene.md) and its `artifacts/assembly-scene/` receipts. This adds visual assembly coverage, not hardware qualification.\n')

# Format newly generated prose; protect inline-code identities and hashes.
import re
for doc in ['validation.md','manufacturing-review.md','schematic-review.md','electrical.md','bom.md','outer-power-routing.md']:
 p=root/'docs'/doc; segments=p.read_text().split('`')
 for i in range(0,len(segments),2):
  t=segments[i]
  t=re.sub(r'(?<=[a-z])(?=\d)', ' ', t)
  t=re.sub(r'(?<=\d)(?=(?:mm|mA|mΩ|Ω|V|A|°C|k|pt|Type)\b)', ' ', t)
  t=re.sub(r'(?<=[a-z])(?=TypeV)', ' ', t)
  t=t.replace('input isCL','input is CL').replace('supplier-orientation','supplier orientation')
  segments[i]=t.replace('SMF4L16 A','SMF4L16A')
 p.write_text('`'.join(segments))

# Build an explicit current inventory; old unrelated receipts remain historical, never acceptance.
manifestpath=a/'validation/engineering-review-manifest.json';hist=a/'historical-independent-review-2026-10-10/engineering-review-manifest.json'
if manifestpath.exists()and not hist.exists():shutil.copyfile(manifestpath,hist)
selected={root/'index.circuit.tsx',root/'index.circuit.json',root/'package.json',root/'package-lock.json',root/'tscircuit.config.json',root/'.pcba-workflow/program-state.json',board,a/'final-source.circuit.json',a/'drc-report.json',a/'physical-connectivity.json',a/'trace-width-review.json',a/'nema14-gerbers.zip',a/'manufacturing-raw.zip',a/'raw-cli-export-binding.json',pdf}
for folder in ['src','imports/supplier','references','scripts','docs','artifacts/assembly','artifacts/mechanical','artifacts/manufacturing','artifacts/engineering','artifacts/validation/independent-checks','artifacts/validation/service-schematic-ui']:
 selected.update(p for p in(root/folder).rglob('*')if p.is_file()and'__pycache__'not in p.parts and p.suffix!='.pyc')
historical_names={'ldo-thermal-copper.json','ldo-thermal-screening.json','route-replay-verification.json','routing-engine-evidence.json'}
selected={p for p in selected if not (p.parent==a/'engineering' and p.name in historical_names)}
for fn in ['assembly.circuit.tsx','assembly.circuit.json','tsconfig.json']:
 if (root/fn).exists():selected.add(root/fn)
for folder in ['assets/assembly','artifacts/assembly-scene']:
 selected.update(p for p in(root/folder).rglob('*')if p.is_file())
for p in a.glob('*.svg'):selected.add(p)
for p in a.glob('*.png'):selected.add(p)
for fn in list(required)+['artifacts/validation/independent-source-proof.json','artifacts/validation/independent-pdf-review.json','artifacts/validation/independent-checks.json','artifacts/validation/service-cli-results.json','artifacts/validation/schematic-placement.txt','artifacts/validation/service-motor-inside-board.json']:selected.add(root/fn)
for p in(a/'validation').glob('service-cli-*.txt'):selected.add(p)
if rp:
 for p in a.glob('independent*'):selected.add(p)
 for p in(a/'validation').glob('independent-*'):
  if p.is_file():selected.add(p)
manifest={'schema':'nema14-independent-engineering-manifest-v1','project':read('package.json')['name'],'inspected_baseline_commit':start,'saved_board_sha256':bs,'fresh_source_sha256':sha(a/'final-source.circuit.json'),'index_saved_board_byte_identical':True,'local_validation_passed':True,'manufacturing_release':False,'hardware_tested':False,'published_this_task':False,'inventory_note':'Only the listed current artifacts/evidence are authoritative. Historical receipts and router diagnostics do not independently validate changed revisions. External/bench gates remain open. Local commit IDs are recorded in the task receipt after commits, outside this self-hashing inventory.','entries':[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(selected)if p.is_file()and p!=manifestpath]};manifestpath.write_text(json.dumps(manifest,indent=2)+'\n')
for e in manifest['entries']:assert sha(root/e['path'])==e['sha256'],e['path']
print(read('package.json')['name'],'final source',bs,'verified manifest entries',len(manifest['entries']))
