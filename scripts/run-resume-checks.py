"""Record actual exit codes and logs for every resumed-board qualification."""
import hashlib,json,os,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1];out=root/'artifacts/validation-resume';out.mkdir(exist_ok=True);env=dict(os.environ);env['PATH']=str(root/'node_modules/.bin')+':'+env['PATH'];env['XDG_CONFIG_HOME']='/workspace/.config'
# Delivered preview and extracted CAM files must be current before qualification.
subprocess.run(['python3','scripts/finalize-manufacturing-artifacts.py'],cwd=root,env=env,check=True)
checks=[('all_resistor_edge_clearances',['/workspace/.routing-venv/bin/python','scripts/check-resistor-edges.py']),('typescript',['tsc','--noEmit']),('drc',['bun','scripts/check.ts']),('connectivity',['/workspace/.routing-venv/bin/python','scripts/verify_supplier_connectivity.py']),('fitted_JST_and_actual_drills',['/workspace/.routing-venv/bin/python','scripts/check-motor-connector.py']),('exact_mounts_and_actual_drills',['python3','scripts/check-mount-drills.py']),('native_json_checks',['tsci','check','artifacts/board.circuit.json'])]
checks += [(f'native_{name}',['tsci','check',name,'index.circuit.tsx' if name=='netlist' else 'artifacts/board.circuit.json']) for name in ['netlist','pin_specification','source','schematic-placement','placement']]
checks += [('schematic_geometry_ERC',['/workspace/.routing-venv/bin/python','scripts/verify-schematic.py']),('every_trace_review',['/workspace/.routing-venv/bin/python','scripts/audit-every-trace.py']),('reference_feedback',['/workspace/.routing-venv/bin/python','scripts/check-reference-feedback.py']),('gerber_shorts',['tsci','check','shorts','artifacts/board.circuit.json','--mode','gerber','--layer','all','--pixels-per-mm','100']),('copper_widths',['/workspace/.routing-venv/bin/python','scripts/audit-trace-widths.py']),('full_independent_CAM',['/workspace/.routing-venv/bin/python','scripts/audit-manufacturing.py'])]
receipts=[]
for name,cmd in checks:
 with (out/(name+'.txt')).open('w') as log:r=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 if name=='native_schematic-placement' and (out/(name+'.txt')).read_text().strip():
  r.returncode=1 # This CLI emits placement diagnostics with a successful exit code.
 receipts.append({'check':name,'command':cmd,'exit_code':r.returncode,'log':str((out/(name+'.txt')).relative_to(root))});print(name,r.returncode,flush=True)
j=json.loads((root/'artifacts/board.circuit.json').read_text());m=json.loads((root/'artifacts/mechanical/mount-usb-screen.json').read_text());sha=hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest();mechanical_current=m['board_sha256']==sha and m['passed']
cam_path=root/'artifacts/manufacturing/audit.json';cam=json.loads(cam_path.read_text()) if cam_path.exists() else {};cam_current=cam.get('source_sha256')==sha
if not cam_current:cam={'status':'NOT_COMPLETED_FOR_CURRENT_BOARD','issues':['See full_independent_CAM log; a stale audit is not validation evidence.']}
(root/'artifacts/schematic-redesign/native-analysis.txt').write_bytes((out/'native_schematic-placement.txt').read_bytes())
record={'board_sha256':sha,'checks':receipts,'native_STEP_mechanical_pass':bool(mechanical_current),'CAD_models_checked':m['native_STEP_models'],'physical_nets_checked':json.loads((root/'artifacts/physical-connectivity.json').read_text())['checkedNets'],'counts':{t:sum(e['type']==t for e in j) for t in ['pcb_trace','pcb_via','pcb_copper_pour']},'full_CAM_status':cam['status'],'remaining_CAM_findings':cam['issues'],'rear_motor_compatibility_verified':False,'prototype_fabrication_ready':False,'physical_hardware_tested':False}
(root/'artifacts/resume-validation.json').write_text(json.dumps(record,indent=2)+'\n')
# Fail the whole qualification if any required check failed. The public prototype
# receipt retains every error instead of presenting CAM failures as a PASS.
raise SystemExit(1 if any(r['exit_code'] for r in receipts) or not mechanical_current or not cam_current else 0)
