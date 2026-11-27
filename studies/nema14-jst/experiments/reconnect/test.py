"""Native replay and negative controls; never rerun the bounded router in CI."""
from pathlib import Path
import json,sys,copy,subprocess,math,importlib.util,gzip
sys.path.insert(0,'experiments/reconnect')
from model import read
root=Path('artifacts/iteration-8');tmp=Path('.config/cp2-buzzer');tmp.mkdir(parents=True,exist_ok=True)
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
fresh=tmp/'fresh.circuit.json';run(['bun','experiments/reconnect/render.ts',str(fresh),'--small-hole-screen']);run([sys.executable,'experiments/placement/screen.py',str(fresh),str(tmp/'placement.json')]);run([sys.executable,'experiments/reconnect/analyze.py',str(fresh),str(tmp/'loops.json')]);run([sys.executable,'experiments/reconnect/verify.py',str(fresh),str(tmp/'critical.json')]);a=read(root/'authored.circuit.json');b=read(fresh)
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def rows(j,typ):
 out=copy.deepcopy([e for e in j if e['type']==typ])
 if typ=='pcb_trace':
  for e in out:
   assert abs(e['trace_length']-v.length([e]))<1e-12;e.pop('trace_length',None)
 return out
for typ in ['source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_courtyard_outline','pcb_via','pcb_trace','pcb_board','pcb_hole','pcb_keepout']:assert rows(a,typ)==rows(b,typ),'Native replay changed '+typ
assert read(tmp/'placement.json')['full_nominal_placement_pass'];critical=read(tmp/'critical.json');assert critical['locality']['candidate_pass']==43 and critical['locality']['regressed_previous_passes']==[];assert len(critical['four_actual_pad_pickups'])==4;assert all(r['finished_stack_centerline_mm']<=5 for r in critical['actual_ground_returns']);assert all(x['minimum_reduction_mm']>0 for x in read(tmp/'loops.json')['loop_comparison'].values())
# A physically missing barrel must break the isolated supply branch.
wrong=copy.deepcopy(b);vias=json.load(open('experiments/reconnect/vias.json'));q=vias[0];wrong=[e for e in wrong if not(e['type']=='pcb_via' and math.dist([e['x'],e['y']],[q['x'],q['y']])<1e-9)];p=tmp/'missing-barrel.json';p.write_text(json.dumps(wrong));res=subprocess.run([sys.executable,'experiments/reconnect/verify.py',str(p),str(tmp/'bad.json')],capture_output=True,text=True);assert res.returncode!=0
# Native world-coordinate or width drift is rejected rather than repaired.
for field in ['x','width']:
 wrong=copy.deepcopy(b);st={e['source_trace_id']:e.get('name','') for e in wrong if e['type']=='source_trace'};t=next(e for e in wrong if e['type']=='pcb_trace' and st[e['source_trace_id']]=='AUTHORED_CP2_CORRIDOR');t['route'][1][field]+=.001;p=tmp/('bad-'+field+'.json');p.write_text(json.dumps(wrong));res=subprocess.run([sys.executable,'experiments/reconnect/analyze.py',str(p),str(tmp/'bad.json')],capture_output=True,text=True);assert res.returncode!=0
# A materially wrong derived length cache is rejected; it is never trusted as geometry.
wrong=copy.deepcopy(b);st={e['source_trace_id']:e.get('name','') for e in wrong if e['type']=='source_trace'};t=next(e for e in wrong if e['type']=='pcb_trace' and st[e['source_trace_id']]=='AUTHORED_SENSE_B__2');t['trace_length']+=.001;p=tmp/'bad-length-cache.json';p.write_text(json.dumps(wrong));res=subprocess.run([sys.executable,'experiments/reconnect/analyze.py',str(p),str(tmp/'bad.json')],capture_output=True,text=True);assert res.returncode!=0 and 'invalid derived length cache' in res.stderr
# Preserve rejection of the real former EP failures and of manufacturing stress.
old=read(root/'cp2-root-cause.json');assert '0.120894' in json.dumps(old) and '0.119332' in json.dumps(old)
mfg=read(root/'process-screen.json');assert mfg['summary']['vias']==22 and mfg['summary']['width_plus_20_percent_spacing_findings']==24;assert not mfg['supplier_acceptance_verified'];assert read(root/'locked-process-screen.json')['summary']['negative_assumption_adjusted_annular_margins']==4
checks=read(root/'native-checks.json');assert all(x.get('count')==0 for x in checks.values());assert read(root/'native-checks.json.all-routing.json')['by_type']['pcb_port_not_connected_error']==302
# The saved one-net native result stays a partial controller, with immutable prior copper.
receipt=read(root/'native-VREG/verification.json');assert receipt['before_traces']==43 and receipt['after_traces']==44 and receipt['before_vias']==receipt['after_vias']==22;assert receipt['all_fixed_records_byte_equivalent'] and receipt['actual_vreg_connected'];assert receipt['independent']['disconnected_nets']==59 and all(receipt['independent'][k]==0 for k in ['shorts','clearance_violations','drill_spacing_violations','hole_trace_violations','board_edge_violations','screw_keepout_violations']);assert receipt['cli_exit']['exit_code']==1 and not receipt['fabrication_ready']
before=read(root/'native-VREG/before.circuit.json');after=read(root/'native-VREG/native.circuit.json');assert not v.compare_fixed(before,after)
for field in ['x','width']:
 wrong=copy.deepcopy(after);t=next(e for e in wrong if e['type']=='pcb_trace');t['route'][0][field]=math.nextafter(t['route'][0][field],math.inf);assert v.compare_fixed(before,wrong)
print('PASS: native full placement replay; CP1/CP2 net/geometry/width match; 32 prior traces +20 vias unchanged; drilled loop/barrel checks and rejection controls; 43/59 retained; four real Kelvin pickups; both real returns <=5 mm. Manufacturing and full routing remain blocked.')
