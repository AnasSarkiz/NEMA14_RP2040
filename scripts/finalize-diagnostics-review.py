"""Bind current source/CAM/assembly evidence, excluding historical receipts from acceptance."""
from pathlib import Path
import json,hashlib,subprocess,datetime,shutil,csv,zipfile
root=Path(__file__).resolve().parents[1];a=root/'artifacts';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads((root/p).read_text());write=lambda p,v:(root/p).write_text(json.dumps(v,indent=2)+'\n');rp=read('package.json')['name']=='NEMA14_RP2040';start='56222094968d6ebefd37adfe6f32623149403b10'if rp else'd557db5fdc52cc89e721df5644218017db7230e0';board=a/'board.circuit.json';bs=sha(board);j=json.loads(board.read_text());fresh=read('artifacts/final-source.circuit.json');old=json.loads(subprocess.check_output(['git','show',start+':artifacts/board.circuit.json'],cwd=root))
def graph(j,exclude=lambda t:False):
 ss={s['source_component_id']:s['name']for s in j if s['type']=='source_component'};group={};terms=[]
 for p in j:
  if p['type']=='source_port'and p.get('pin_number')is not None:
   term=(ss[p['source_component_id']],str(p['pin_number']))
   if exclude(term):continue
   key=p.get('subcircuit_connectivity_map_key')or term;group.setdefault(key,[]).append(term);terms.append((term,key))
 return {str(t):sorted(group[k])for t,k in terms}
assert graph(j)==graph(fresh),'Fresh source and saved routed pin connectivity differ'
ignored=set(parts_name for parts_name in {e['name'] for e in j if e['type']=='source_component'} ^ {e['name'] for e in old if e['type']=='source_component'})
mcuPins={'2','3','4','5','6','27'}if rp else{'10','11','12','13','16'}
exclude=lambda t:t[0]in ignored or t[0]=='U_MCU'and t[1]in mcuPins
assert graph(j,exclude)==graph(old,exclude),'Unintended connectivity change outside reviewed diagnostics/buck revision'
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
pdf=a/'schematic-a4.pdf';pages=PdfReader(pdf).pages;assert len(pages)==(5 if rp else 4)
for p in pages:assert abs(float(p.mediabox.width)*25.4/72-297)<.01 and abs(float(p.mediabox.height)*25.4/72-210)<.01
write('artifacts/validation/independent-pdf-review.json',{'source_sha256':bs,'pdf_sha256':sha(pdf),'pages':len(pages),'a4_landscape_verified':True,'passive_minimum_font_pt':6.5,'automatedTextOverlapAudit':'functional-schematic-text-audit.json','hardware_or_ide_simulation_performed':False})
shutil.copyfile(board,root/'index.circuit.json');assert sha(root/'index.circuit.json')==bs

power=read('artifacts/engineering/diagnostics-power-review.json');assert power['source_sha256']==bs
scene=read('artifacts/assembly-scene/checks.json');assert scene['source_board_sha256']==bs and scene['all_commands_passed']
scene_browser=read('artifacts/assembly-scene/browser-review.json');assert scene_browser['source_board_sha256']==bs and not scene_browser['page_errors']and not scene_browser['console_errors']and not scene_browser['http_errors']and len(scene_browser['screenshots'])==5
assert scene_browser['installed_glb_sha256']==sha(a/'assembly-scene/installed-assembly.glb')
# Hash every current release artifact, keeping historical inputs explicitly separate.
project=read('package.json')['name'];fitted=len(read('src/jlcpcb-catalog.json')['components']);sheets=len([e for e in j if e['type']=='schematic_sheet'])
assert fitted==(79 if rp else 59) and sheets==(5 if rp else 4)
summary=f"""# Diagnostics revision validation — {project}

Inspected exact local baseline commit `{start}`. Final saved PCB SHA256 `{bs}`; `index.circuit.json` is byte-identical. Fresh source pin connectivity, native pads and part values/identities match the saved routed board. The baseline graph is unchanged except added diagnostics, CH32 buck replacement and the explicitly reassigned MCU pins recorded in `independent-source-proof.json`.

Both boards are 35 × 35 × 1.6 mm, four layers, top fitted parts, same-edge USB openings and an entirely inside-board keyed JST header. This variant has {fitted} fitted parts and {sheets} functional A4 sheets. CH32's two-layer routing attempt could not close the added circuits; the four-layer alternative is documented and costs more to fabricate.

Current typecheck, build/native DRC, physical connectivity, trace-width/RMS thermal screens, actual all-layer Gerber shorts and functional silkscreen checks pass. DRC errors: 0; {len(read('artifacts/drc-report.json')['warnings'])} native metadata warnings remain visible. Exact exits/log hashes are in `artifacts/validation/independent-checks.json`. Actual CAM/source/drill/archive equality, clearances, mask and paste audits pass. Main motor/15V widths≥0.45mm on outer layers; sense≥0.30mm. Nonzero phase vias remain disclosed; this is not a via-free design. Thin native escapes/resistor leaves are individually bounded. The RP2040 driver-only logic supply branch is physically proved against its actual terminals and screened at 20 mA using the 8 mA A4988 limit, conditional on fPWM<50kHz.

All current PDF pages have A4 dimensions, automated text/foreign-symbol overlap audits and project Chromium sheet review. CLI netlist, pin-specification, source and schematic checks pass. Placement reports zero Errors/Warnings but exits 1 with supplier pickup/orientation advisories. Machine pickup centers/rotations remain pending supplier preview. The installed CLI has no pcb-style check; official IDE/WebGPU/electrical simulation was not run.

Native STEP review/rebind and separate assembly preview use the current fitted geometry. See the bound mechanical/assembly-scene receipts and drawings. Nominal models and tolerance screens do not establish physical fit; header posts, mating housing, leads, clamp, barrier, screws and both cables need a real assembly coupon.

Regenerated Gerber/drill ZIP, BOM, PnP, manual-header tables, assembly drawings, A4 PDF and eight-group separate `assembly.circuit.tsx` scene are inventoried in `artifacts/validation/engineering-review-manifest.json`. Historical manifests, LDO/return calculations, router experiments and old publication receipts do not validate this revision.

Hardware tests remain unperformed: winding currents/balance, USB and 15 V PD, ROM/application programming, every power transition/reset/brownout/backfeed, regeneration, converter stability/ripple/startup/fault, mounted temperatures, TMP102 accuracy/response, sounder waveform/current/acoustics and full installed physical fit. Diagnostic firmware is specified, not implemented. TypeVI/TypeVII fill, fine-drill/slots/stencil and pickup conventions require supplier acceptance. Neither board is released for production or ordering. This task saves local commits and publishes nothing.
"""
(root/'docs/validation.md').write_text(summary)
comparison="""# NEMA14 diagnostic variants

Both preserve the motor/harness, 35 mm outline, same-edge two USB-C ports, inside-board JST and top assembly. Exact per-board files/hashes are in each engineering manifest.

| Feature | CH32X035G8U6 | RP2040 |
|---|---|---|
| MCU | CH32X035G8U6 | RP2040, external flash/crystal |
| Fitted parts |59 |79 |
| Copper |4 layers; upgraded from2 for diagnostics |4 layers retained |
| Logic converter |AP63203WU-7, SRN4018-4R7M, exact biased-capacitor review |Same |
| Added status |Green Everlight LED,1kΩ resistor |Same |
| Temperature |TMP102AIDRLR,0x48; software I2C PA5/PA6; ALERT PB1 |Same sensor; I2C0 GPIO1/16; ALERT GPIO4 |
| Buzzer |MLT-5020, AO3400A driver, flyback/default-off/bypass; PA7 TIM3CH2 |Same sounder circuit; GPIO2 PWM |
| Status GPIO |PB0 active low |GPIO3 active low |
| Schematic |4 functional A4 pages |5 functional A4 pages |
| Main motor/15V routing |≥0.45mm outer layers; native escapes individually bounded; phase vias remain |Same |
| Programming hardware |USB ROM boot path and WCH debug |USB ROM BOOTSEL and SWD |
| Firmware/physical hardware qualification |Not implemented/not tested |Same |

PD baseline 3V3 allowance 100 mA; pulse 550 mA / average 310 mA qualification ceilings, no external loads. DATA-only3V3 target 75 mA, measured USB DATA input≤100mA in every state, including loss of PD during an alarm. Buzzer only with valid 15 V PD, 4 kHz / 50% carrier,≤100ms bursts at≤1Hz. These are proposed requirements, not measured ratings. TMP102 reports local PCB temperature, not winding temperature; software alarms are not an independent thermal safety system.

Both use15V PD, accepted measured phase peaks≤0.25A, room0–40°C/local air≤45°C/motor case≤60°C, stop energy≤0.10mJ at≤1Hz and no continuous back-driving. Supply18V measured operating ceiling and all transient tests apply. Motor/cable installation reservation≈49.204×157.480×102.771mm precedes tolerances and service access. Front M3 motor threads only; rear end-cap screws untouched.

Both need supplier-approved TypeVII filled/copper-capped exposed-pad vias and listed TypeVI close off-pad barrels. Ordinary drill counts/coordinates, mask/paste and pickup datums are in current fabrication CSVs. Pickup conventions, crimp/splice/material certificates, physical fit, current, USB/PD, power transitions, regeneration, mounted temperatures and the new sensor/sounder behavior remain unqualified. Old DC return/thermal receipts describe earlier copper and are historical. No production readiness is claimed.
"""
(root/'docs/variant-comparison.md').write_text(comparison)
state={'schema':'nema14-diagnostics-review-v1','project':project,'source_sha256':bs,'local_artifact_checks':'PASS_WITH_DISCLOSED_ADVISORIES','hardware_tested':False,'firmware_implemented':False,'manufacturing_release':False,'order_ready':False,'published_this_task':False,'official_ide_analyzer_executed':False,'remaining_qualification_items':power['qualification']}
(root/'.pcba-workflow').mkdir(exist_ok=True);write('.pcba-workflow/program-state.json',state)
(root/'docs/outer-power-routing.md').write_text('# Current outer-power routing\n\nFinal saved board SHA256 `'+bs+'`. Main motor and15V routes use top/bottom only, minimum0.45mm with individually proved native pin escapes/resistor leaves; sense0.30mm.\n\n'+'\n'.join('- '+v['net']+': '+str(v['mainMinimumWidthMm'])+'mm main minimum; '+str(v['totalThroughVias'])+' branched through vias.' for v in read('artifacts/validation/service-outer-power-policy.json')['nets'])+'\n\nPhase vias are present. All-branch counts are not series transition counts. Actual CAM series transitions are in service-outer-power-cam.json. New ground/supply planes invalidate old return-resistance calculations; bench ground-bounce/current-sharing review remains required. BUCK_SW RMS thermal budget0.48A derives from pulse/average and ripple screens; transient≈0.921A is checked separately.\n')
# Replace stale general-summary hash maps with actual current release identities.
v=read('artifacts/verification.json');oldv=a/'diagnostics/historical-reviews/verification-before-final-binding.json'
if not oldv.exists():oldv.write_text(json.dumps(v,indent=2)+'\n')
v['source_sha256']=bs;v['sha256']={str(path.relative_to(root)):sha(path) for path in [board,root/'index.circuit.json',a/'final-source.circuit.json',a/'nema14-gerbers.zip',a/'schematic-a4.pdf']};v['hardwareBenchTested']=False;v['firmwareImplemented']=False;v['manufacturingRelease']=False;v['fittedComponentCount']=fitted;v['schematicA4PageCount']=sheets;v['drcErrors']=0;v['drcWarnings']=len(read('artifacts/drc-report.json')['warnings']);write('artifacts/verification.json',v)
manifestpath=a/'validation/engineering-review-manifest.json';selected={root/f for f in ['index.circuit.tsx','index.circuit.json','assembly.circuit.tsx','assembly.circuit.json','package.json','package-lock.json','tscircuit.config.json','tsconfig.json','.pcba-workflow/program-state.json','README.md']}
folders=['src','imports/supplier','references','scripts','docs','assets/assembly','artifacts/assembly','artifacts/assembly-scene','artifacts/mechanical','artifacts/manufacturing','artifacts/validation/independent-checks','artifacts/validation/service-schematic-ui','artifacts/validation/diagnostics-pdf-review']
for folder in folders:selected.update(p for p in(root/folder).rglob('*')if p.is_file()and'__pycache__'not in p.parts and p.suffix!='.pyc')
for p in a.glob('*'):
 if p.is_file()and(p.suffix in ['.png','.svg','.pdf']or p.name in ['board.circuit.json','final-source.circuit.json','drc-report.json','physical-connectivity.json','trace-width-review.json','nema14-gerbers.zip','manufacturing-raw.zip','raw-cli-export-binding.json','verification.json','jlcpcb-import-report.json','supplier-cad-alignment.json','source-bom.csv']):selected.add(p)
for folder in ['artifacts/diagnostics','artifacts/engineering']:
 for p in(root/folder).glob('*.json'):
  if folder.endswith('engineering')and p.name not in ['diagnostics-power-review.json','supported-operating-envelope.json']:continue
  selected.add(p)
for fn in list(required)+['artifacts/validation/independent-source-proof.json','artifacts/validation/independent-pdf-review.json','artifacts/validation/independent-checks.json','artifacts/validation/service-cli-results.json','artifacts/validation/functional-schematic-text-audit.json','artifacts/validation/schematic-port-net-coverage.json','artifacts/validation/schematic-placement.txt','artifacts/validation/service-motor-inside-board.json']:selected.add(root/fn)
for p in(a/'validation').glob('service-cli-*.txt'):selected.add(p)
manifest={'schema':'nema14-diagnostics-engineering-manifest-v1','project':project,'inspected_baseline_commit':start,'saved_board_sha256':bs,'fresh_source_sha256':sha(a/'final-source.circuit.json'),'index_saved_board_byte_identical':True,'local_validation_passed':True,'hardware_tested':False,'manufacturing_release':False,'firmware_implemented':False,'published_this_task':False,'inventory_note':'Listed current files are authoritative; diagnostics record actual attempts/manual edits, not independent acceptance. Historical/old receipts are excluded. No physical qualification claimed.','entries':[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(selected)if p.is_file()and p!=manifestpath]};manifestpath.write_text(json.dumps(manifest,indent=2)+'\n')
for e in manifest['entries']:assert sha(root/e['path'])==e['sha256'],e['path']
print(project,'final source',bs,'verified inventory',len(manifest['entries']))
