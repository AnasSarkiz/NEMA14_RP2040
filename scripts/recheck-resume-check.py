"""Rerun a failed recorded check after a fix, retaining the original result."""
import datetime,hashlib,json,os,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/resume-validation.json';record=json.loads(path.read_text())
sha=hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest();assert record['board_sha256']==sha,'Requalify a changed board before targeted retries'
name=sys.argv[1];matches=[e for e in record['checks'] if e['check']==name];assert len(matches)==1
entry=matches[0];previous=dict(entry);env=dict(os.environ);env['PATH']=str(root/'node_modules/.bin')+':'+env['PATH'];env['XDG_CONFIG_HOME']='/workspace/.config'
with (root/entry['log']).open('w') as f:r=subprocess.run(entry['command'],cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
assert hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest()==sha
entry['exit_code']=r.returncode
record.setdefault('retry_history',[]).append({'check':name,'previous_exit_code':previous['exit_code'],'retry_exit_code':r.returncode,'board_sha256':sha,'retried_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
if name=='full_independent_CAM':
 cam=json.loads((root/'artifacts/manufacturing/audit.json').read_text())
 assert cam['source_sha256']==sha
 record['full_CAM_status']=cam['status'];record['remaining_CAM_findings']=cam['issues']
path.write_text(json.dumps(record,indent=2)+'\n');print(name,r.returncode);raise SystemExit(r.returncode)
