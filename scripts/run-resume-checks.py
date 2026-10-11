"""Record actual exit codes and logs for every resumed-board qualification."""
import hashlib,json,os,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1];out=root/'artifacts/validation-resume';out.mkdir(exist_ok=True);env=dict(os.environ);env['PATH']=str(root/'node_modules/.bin')+':'+env['PATH'];env['XDG_CONFIG_HOME']='/workspace/.config'
checks=[('typescript',['tsc','--noEmit']),('drc',['bun','scripts/check.ts']),('connectivity',['/workspace/.routing-venv/bin/python','scripts/verify_supplier_connectivity.py']),('fitted_JST_and_actual_drills',['python3','scripts/check-motor-connector.py']),('exact_mounts_and_actual_drills',['python3','scripts/check-mount-drills.py']),('native_json_checks',['tsci','check','artifacts/board.circuit.json'])]
checks += [(f'native_{name}',['tsci','check',name,'index.circuit.tsx' if name=='netlist' else 'artifacts/board.circuit.json']) for name in ['netlist','pin_specification','source','schematic-placement','placement']]
checks += [('gerber_shorts',['tsci','check','shorts','artifacts/board.circuit.json','--mode','gerber','--layer','all','--pixels-per-mm','100']),('copper_widths',['/workspace/.routing-venv/bin/python','scripts/audit-trace-widths.py']),('full_independent_CAM',['/workspace/.routing-venv/bin/python','scripts/audit-manufacturing.py'])]
receipts=[]
for name,cmd in checks:
 with (out/(name+'.txt')).open('w') as log:r=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 receipts.append({'check':name,'command':cmd,'exit_code':r.returncode,'log':str((out/(name+'.txt')).relative_to(root))});print(name,r.returncode,flush=True)
j=json.loads((root/'artifacts/board.circuit.json').read_text());m=json.loads((root/'artifacts/mechanical/mount-usb-screen.json').read_text());sha=hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest();assert m['board_sha256']==sha and m['passed']
cam=json.loads((root/'artifacts/manufacturing/audit.json').read_text());assert cam['source_sha256']==sha
record={'board_sha256':sha,'checks':receipts,'native_STEP_mechanical_pass':m['passed'],'CAD_models_checked':m['native_STEP_models'],'physical_nets_checked':json.loads((root/'artifacts/physical-connectivity.json').read_text())['checkedNets'],'counts':{t:sum(e['type']==t for e in j) for t in ['pcb_trace','pcb_via','pcb_copper_pour']},'full_CAM_status':cam['status'],'remaining_CAM_findings':cam['issues'],'rear_motor_compatibility_verified':False,'prototype_fabrication_ready':False,'physical_hardware_tested':False}
(root/'artifacts/resume-validation.json').write_text(json.dumps(record,indent=2)+'\n')
# Fail the whole qualification if any required check failed. The public prototype
# receipt retains every error instead of presenting CAM failures as a PASS.
raise SystemExit(1 if any(r['exit_code'] for r in receipts) else 0)
