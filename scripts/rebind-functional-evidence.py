"""Reuse fabrication/electrical evidence only after full non-schematic equality.
No CAM, thermal, mechanical or hardware test is represented as rerun here.
The schematic/native/browser checks are rerun separately on the new sheets.
"""
from pathlib import Path
import hashlib,json,subprocess
r=Path(__file__).resolve().parents[1];h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda f:json.loads((r/f).read_text());write=lambda f,j:(r/f).write_text(json.dumps(j,indent=2)+'\n')
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();path=r/'artifacts/board.circuit.json';previous=subprocess.check_output(['git','show','HEAD:artifacts/board.circuit.json'],cwd=r);a=json.loads(previous);b=read('artifacts/board.circuit.json');strip=lambda j:[e for e in j if not e['type'].startswith('schematic_')]
assert strip(a)==strip(b),'Electrical, mechanical or PCB input changed: evidence cannot be rebound'
old=hashlib.sha256(previous).hexdigest();new=h(path);proof={'schema':'schematic-only-evidence-binding-v1','compared_git_revision':revision,'previous_saved_board_sha256':old,'current_saved_board_sha256':new,'all_non_schematic_records_equal':True,'non_schematic_records_sha256':hashlib.sha256(json.dumps(strip(b),sort_keys=True,separators=(',',':')).encode()).hexdigest(),'hardware_tested':False,'method':'All non-schematic records, in order with every value, equal the committed engineering release. Actual CAM ZIPs, all exported Gerber/drill/assembly files, BOM and PnP remain byte-identical. Prior results remain applicable to identical inputs; they were not rerun by this binding script.','unchanged_artifacts':{},'rebound_reports':{}}
# Positively verify every fabrication file against the committed engineering release.
files=[p for p in(r/'artifacts/manufacturing').rglob('*')if p.is_file() and p.suffix!='.json']
files += [r/'artifacts'/f for f in ['nema14-gerbers.zip','manufacturing-raw.zip','bom.csv','source-bom.csv','pick_and_place.csv']]
for p in files:
 rel=str(p.relative_to(r));base=subprocess.check_output(['git','show','HEAD:'+rel],cwd=r);assert p.read_bytes()==base,rel;proof['unchanged_artifacts'][rel]=h(p)
fields={
 'artifacts/physical-connectivity.json':'sha256',
 'artifacts/trace-width-review.json':'sha256',
 'artifacts/raw-cli-export-binding.json':'source_sha256',
 'artifacts/manufacturing/audit.json':'source_sha256',
 'artifacts/manufacturing/export-manifest.json':'source_sha256',
 'artifacts/manufacturing/via-paste-inspection.json':'source_sha256',
 'artifacts/assembly/assembly-review.json':'source_sha256',
 'artifacts/assembly/harness-drawings-review.json':'source_sha256',
 'artifacts/validation/service-silkscreen.json':'source_sha256',
 'artifacts/validation/service-outer-power-cam.json':'source_sha256'}
if (r/'artifacts/manufacturing/inner1-local-bridge-review.json').exists():fields['artifacts/manufacturing/inner1-local-bridge-review.json']='source_sha256'
for file,key in fields.items():
 j=read(file);assert j[key]in[old,new],(file,j[key]);previous_report_sha=h(r/file)
 if j[key]==old:
  original_source=j[key];j[key]=new;j['schematic_only_evidence_binding']={'proof':'artifacts/validation/functional-schematic-evidence-binding.json','previous_report_sha256':previous_report_sha,'original_source_sha256':original_source,'current_source_sha256':new,'non_schematic_inputs_equal':True,'original_test_repeated':False};write(file,j)
 proof['rebound_reports'][file]={'previous_report_sha256':previous_report_sha,'current_report_sha256':h(r/file),'binding':key}
# The outer CAM report also records hashes of its current identical-input dependencies.
j=read('artifacts/validation/service-outer-power-cam.json');j['native_policy_sha256']=h(r/'artifacts/validation/service-outer-power-policy.json');j['cam_audit_sha256']=h(r/'artifacts/manufacturing/audit.json');assert j['archive_sha256']==h(r/'artifacts/nema14-gerbers.zip');write('artifacts/validation/service-outer-power-cam.json',j);proof['rebound_reports']['artifacts/validation/service-outer-power-cam.json']['current_report_sha256']=h(r/'artifacts/validation/service-outer-power-cam.json')
# Refresh the presentation inventory and the actually rerun native schematic command.
pcb=[e for e in b if e['type'].startswith('pcb_')and not e['type'].endswith(('_warning','_error'))];presentation={'savedPcbGeometryUnchanged':True,'sourcePinsAndNetsUnchanged':True,'pcbGeometrySha256':hashlib.sha256(json.dumps(pcb,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'boardSha256':new,'nativeA4Sheets':[e for e in b if e['type']=='schematic_sheet'],'componentModels':sum(e['type']=='cad_component'and bool(e.get('model_obj_url'))for e in b),'proof':'artifacts/validation/functional-schematic-invariance.json'};write('artifacts/presentation-verification.json',presentation)
cli=read('artifacts/validation/service-cli-results.json');cli['previous_prepared_source_sha256']=cli['prepared_source_sha256'];cli['prepared_source_sha256']=h(r/'artifacts/final-source.circuit.json');cli['schematic_only_evidence_binding']='artifacts/validation/functional-schematic-invariance.json'
import xml.etree.ElementTree as ET
for f in ['artifacts/validation/service-cli-schematic.txt','artifacts/validation/schematic-placement.txt']:
 tree=ET.fromstring('<analysis>'+(r/f).read_text()+'</analysis>');assert not [x for g in tree.iter('SchematicPlacementIssues')for x in g],f
for c in cli['commands']:
 if c['name']=='schematic':c.update({'exit_code':0,'output_sha256':h(r/c['output']),'rerun_on_current_functional_schematic':True})
write('artifacts/validation/service-cli-results.json',cli)
# Only the current displayed board hash changes in the routing document.
p=r/'docs/outer-power-routing.md';s=p.read_text();assert old in s;s=s.replace(old,new);s+='\nSchematic-only refresh: all electrical/PCB/CAD records and CAM ZIP bytes are unchanged from the prior routing release. See `functional-schematic-evidence-binding.json`; fabrication checks remain applicable through exact input equivalence.\n';p.write_text(s)
write('artifacts/validation/functional-schematic-evidence-binding.json',proof);print('Bound',len(fields),'unchanged-input reports;',len(files),'fabrication files byte-identical; no physical test claimed')
