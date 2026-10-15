"""Verify the actual default public preview, separate from fabrication JSON."""
import datetime,hashlib,json,pathlib,urllib.parse,urllib.request,sys
root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]
name='AnasSarkiz/'+json.loads((root/'package.json').read_text())['name'];base='https://registry-api.tscircuit.com/'
def get(endpoint,**q):
 with urllib.request.urlopen(base+endpoint+'?'+urllib.parse.urlencode(q),timeout=60) as r:return json.load(r)
def file(p):return get('package_files/get',package_name=name,use_latest_version='true',file_path=p)['package_file']['content_text']
preview=get('package_releases/get_preview_circuit_json',package_name=name,is_latest='true')['preview_circuit_json_response']
assert preview['circuit_json_found'] and preview['component_path']=='assembly.circuit.json'
remote=json.loads(file('assembly.circuit.json'));dist=json.loads(file('dist/assembly/circuit.json'));local=json.loads((root/'assembly.circuit.json').read_text())
assert remote==dist==preview['circuit_json']
def strip(j):return [{k:v for k,v in e.items() if not(e['type']=='cad_component' and k in ['model_obj_url','model_step_url'])} for e in j]
assert strip(remote)==strip(local)
native=json.loads((root/'artifacts/board.circuit.json').read_text());assert strip(remote[:len(native)])==strip(native)
extras=remote[len(native):];sources=[e for e in extras if e['type']=='source_component'];cad=[e for e in extras if e['type']=='cad_component'];cables=[e for e in extras if e['type']=='cad_cable'];assert len(sources)==len(cad)==9 and len(cables)==1
assert not any(e['type'].startswith('pcb_') for e in extras)
fit=json.loads(file('artifacts/top-assembly/assembly-fit-verification.json'));assert fit==json.loads((root/'artifacts/top-assembly/assembly-fit-verification.json').read_text()) and fit['passed']
assert fit['board_sha256']==hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest()
assert not fit['motor_rear_attachment_verified'] and not fit['physical_assembly_tested']
report={'passed':True,'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'package':name,'version':json.loads((root/'package.json').read_text())['version'],'actual_public_preview_component':'assembly.circuit.json','public_preview_matches_native_assembly':True,'reviewed_board_records_preserved':True,'review_board_sha256':fit['board_sha256'],'public_mechanical_parts':len(cad),'public_cables':len(cables),'motor_rear_attachment_verified':False,'physical_assembly_tested':False}
(root/'artifacts/top-assembly/assembly-publication-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
