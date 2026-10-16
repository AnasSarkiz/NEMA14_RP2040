"""Verify the actual default public preview, separate from fabrication JSON."""
import datetime,hashlib,json,pathlib,urllib.parse,urllib.request,sys,subprocess
root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]
name='AnasSarkiz/'+json.loads((root/'package.json').read_text())['name'];base='https://registry-api.tscircuit.com/'
def get(endpoint,**q):
 with urllib.request.urlopen(base+endpoint+'?'+urllib.parse.urlencode(q),timeout=60) as r:return json.load(r)
def file(p):return get('package_files/get',package_name=name,use_latest_version='true',file_path=p)['package_file']['content_text']
preview=get('package_releases/get_preview_circuit_json',package_name=name,is_latest='true')['preview_circuit_json_response']
assert preview['circuit_json_found'] and preview['component_path']=='assembly.circuit.json'
remote=json.loads(file('assembly.circuit.json'));local=json.loads((root/'assembly.circuit.json').read_text())
assert remote==preview['circuit_json']
def strip(j):return [{k:v for k,v in e.items() if not(e['type']=='cad_component' and k in ['model_obj_url','model_step_url'])} for e in j]
assert strip(remote)==strip(local)
native=json.loads((root/'artifacts/board.circuit.json').read_text());assert strip(remote[:len(native)])==strip(native)
extras=remote[len(native):];sources=[e for e in extras if e['type']=='source_component'];cad=[e for e in extras if e['type']=='cad_component'];cables=[e for e in extras if e['type']=='cad_cable'];assert len(sources)==len(cad)==18 and len(cables)==0
assert not any(e['type'].startswith('pcb_') for e in extras)
connection=json.loads(file('artifacts/top-assembly/harness-connection-verification.json'));assert connection['passed'] and connection['motor_wire_outlet_faces_JST_board_edge']
fit=json.loads(file('artifacts/top-assembly/assembly-fit-verification.json'));assert fit==json.loads((root/'artifacts/top-assembly/assembly-fit-verification.json').read_text()) and fit['passed']
current_board_sha=hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest()
if fit['board_sha256']!=current_board_sha:
 preservation=json.loads(file('artifacts/schematic-pin-alignment/verification.json'))
 assert preservation['passed'] and preservation['board_sha256']==current_board_sha
 assert preservation['before_board_sha256']==fit['board_sha256']
 assert preservation['electrical_and_PCB_and_CAD_records_unchanged'] and preservation['mechanical_assembly_records_unchanged']
 canonical=subprocess.check_output(['node','-e',"const j=JSON.parse(require('fs').readFileSync('artifacts/board.circuit.json','utf8'));process.stdout.write(JSON.stringify(j.filter(e=>!e.type.startsWith('schematic_'))))"],cwd=root)
 assert preservation['non_schematic_records_sha256']==hashlib.sha256(canonical).hexdigest()
assert not fit['motor_rear_attachment_verified'] and not fit['physical_assembly_tested']
report={'passed':True,'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'package':name,'version':json.loads((root/'package.json').read_text())['version'],'actual_public_preview_component':'assembly.circuit.json','public_preview_matches_native_assembly':True,'reviewed_board_records_preserved':True,'review_board_sha256':fit['board_sha256'],'current_board_sha256':current_board_sha,'public_mechanical_parts':len(cad),'public_cables':len(cables),'motor_rear_attachment_verified':False,'physical_assembly_tested':False}
(root/'artifacts/top-assembly/assembly-publication-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
