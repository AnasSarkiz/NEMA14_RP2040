"""Fresh native CLI/typecheck validation of the separate assembly entry."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT);OUT=ROOT/'artifacts/assembly-scene';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
env=dict(os.environ);env['PATH']=str(ROOT/'node_modules/.bin')+':'+env['PATH'];env['XDG_CONFIG_HOME']='/workspace/.config'
protected=['index.circuit.tsx','index.circuit.json','artifacts/board.circuit.json','artifacts/nema14-gerbers.zip'];before={p:sha(ROOT/p)for p in protected};results=[]
for name,cmd in [('typecheck',['npm','run','typecheck']),('native-cli-build',['tsci','build','assembly.circuit.tsx','--ignore-config'])]:
 p=OUT/(name+'.txt');r=subprocess.run(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);p.write_text(r.stdout)
 results.append({'name':name,'command':cmd,'exit_code':r.returncode,'output':str(p.relative_to(ROOT)),'output_sha256':sha(p)})
 print(name,r.returncode,flush=True)
 if r.returncode:break
for p,v in before.items():assert sha(ROOT/p)==v,'Assembly validation changed '+p
report={'assembly_entry_sha256':sha(ROOT/'assembly.circuit.tsx'),'source_board_sha256':before['artifacts/board.circuit.json'],'commands':results,'all_commands_passed':len(results)==2 and all(x['exit_code']==0 for x in results),'PCB_artifacts_unchanged':before,'hardware_tested':False}
(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['all_commands_passed'],'Assembly CLI/typecheck failed; inspect recorded logs'
def modelproof(j):
 parts={e['source_component_id']:e['name']for e in j if e['type']=='source_component'}
 return {parts[e['source_component_id']]:{'url_sha':hashlib.sha256(e['model_glb_url'].encode()).hexdigest(),'position':e['position'],'rotation':e['rotation'],'origin':e.get('model_origin_position')}for e in j if e['type']=='cad_component'}
native=ROOT/'dist/assembly/circuit.json'
assert modelproof(json.loads((ROOT/'assembly.circuit.json').read_text()))==modelproof(json.loads(native.read_text())), 'Native CLI CAD identities/transforms differ'
report['native_cli_model_identities_and_transforms_match']=True;report['native_cli_output_sha256']=sha(native)
(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
