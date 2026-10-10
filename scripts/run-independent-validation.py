"""Run required local checks against a frozen saved routed board and record real exits."""
from pathlib import Path
import subprocess,hashlib,json,os,datetime
root=Path(__file__).resolve().parents[1];os.chdir(root);out=root/'artifacts/validation/independent-checks';out.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();board=root/'artifacts/board.circuit.json';frozen=sha(board);env=dict(os.environ);env['PATH']=str(root/'node_modules/.bin')+':'+env['PATH'];env['XDG_CONFIG_HOME']='/workspace/.config';py='/workspace/.routing-venv/bin/python'
commands=[('typecheck',['npm','run','typecheck']),('build',['npm','run','build']),('connectivity',[py,'scripts/verify-connectivity.py']),('width',[py,'scripts/audit-trace-widths.py']),('shorts',['npm','run','shorts']),('silkscreen',[py,'scripts/audit-functional-silk.py'])];rows=[]
for name,command in commands:
 p=out/(name+'.txt');r=subprocess.run(command,cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);p.write_text(r.stdout);assert sha(board)==frozen,'Saved board changed during validation';rows.append({'name':name,'command':command,'exit_code':r.returncode,'output':str(p.relative_to(root)),'output_sha256':sha(p)});print(name,r.returncode,flush=True)
 if r.returncode:break
receipt={'source_sha256':frozen,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':rows,'all_commands_passed':len(rows)==len(commands)and all(r['exit_code']==0 for r in rows),'hardware_tested':False,'manufacturing_release':False}
(root/'artifacts/validation/independent-checks.json').write_text(json.dumps(receipt,indent=2)+'\n');assert receipt['all_commands_passed'],rows
