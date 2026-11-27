"""Replay physical evidence and enforce rejection of the remaining manufacturing gates."""
from pathlib import Path
import json,copy,subprocess,sys,math,importlib.util
sys.path.insert(0,'experiments/tolerance')
from model import read
r=Path('artifacts/iteration-9');tmp=Path('.config/tolerance-test');tmp.mkdir(parents=True,exist_ok=True)
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
p=tmp/'fresh.circuit.json';run(['bun','experiments/tolerance/render.ts',str(p),'--small-hole-screen']);run([sys.executable,'experiments/placement/screen.py',str(p),str(tmp/'placement.json')]);run([sys.executable,'experiments/tolerance/verify.py',str(p),str(tmp/'verified.json')]);a,b=read(r/'final.circuit.json'),read(p)
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def records(data,typ):
 result=copy.deepcopy([e for e in data if e['type']==typ])
 if typ=='pcb_trace':
  for e in result:assert abs(e.pop('trace_length')-v.length([e]))<1e-12
 return result
for typ in ['source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_courtyard_outline','pcb_trace','pcb_via','pcb_board','pcb_hole','pcb_keepout']:assert records(a,typ)==records(b,typ),'Native replay drift '+typ
q=read(tmp/'verified.json');assert q['stress_before_after']==[24,11] and q['introduced_stress_before_after']==[13,0];assert q['locality']['after']==43 and not q['native_stage_allowed'];assert q['preserved_non_CP_routes']==42 and q['preserved_via_records']==22
# Every inherited finding survives exactly, rather than a newly hidden or shifted conflict.
old=read('artifacts/iteration-8/width-stress-causes.json')['findings'];new=read(r/'final-process.json')['width_plus_20_percent_spacing'];key=lambda e:(e['a'],e['b'],e['layer'],round(e['clearance_mm'],6));expected={key(e):e for e in old if e['already_present_in_baseline_stress']};assert set(expected)=={key(e) for e in new};assert all(abs(expected[key(e)]['clearance_mm']-e['clearance_mm'])<1e-12 for e in new)
# Reject one-ULP fixed-copper changes, CP width changes and native max-length suppression.
for kind in ['fixed_coordinate','CP_width','VREG_gate']:
 bad=copy.deepcopy(b);st={e['source_trace_id']:e.get('name') for e in bad if e['type']=='source_trace'}
 if kind=='VREG_gate':next(e for e in bad if e['type']=='source_trace' and e.get('name')=='AUTHORED_VREG_BASELINE')['max_length']=3
 else:
  name='AUTHORED_VREG_BASELINE' if kind=='fixed_coordinate' else 'AUTHORED_CP1_CORRIDOR';t=next(e for e in bad if e['type']=='pcb_trace' and st[e['source_trace_id']]==name);k='x' if kind=='fixed_coordinate' else 'width';t['route'][1][k]=math.nextafter(t['route'][1][k],math.inf)
 path=tmp/(kind+'.json');path.write_text(json.dumps(bad));result=subprocess.run([sys.executable,'experiments/tolerance/verify.py',str(path),str(tmp/'bad.json')],capture_output=True);assert result.returncode!=0,kind
checks=read(r/'final-native-checks.json');assert all(x.get('count')==0 for x in checks.values());allchecks=read(r/'final-native-checks.json.all-routing.json');assert allchecks['by_type']=={'pcb_port_not_connected_error':300,'pcb_trace_too_long_error':1,'pcb_trace_style_warning':4};error=next(e for e in allchecks['findings'] if e['type']=='pcb_trace_too_long_error');assert error['maximum_trace_length']==1 and abs(error['actual_trace_length']-2.60585631220988)<1e-12
mapping=read(r/'stress-segment-map.json');assert len(mapping['findings'])==24 and all(e['matching_primitive_pairs'] for e in mapping['findings']);assert sum(not e['already_present_in_baseline_stress'] for e in mapping['findings'])==13
audit=read(r/'audit.json');assert audit['CLI_physical_copper_net_and_widths_exactly_match'];combined=audit['supplemental_combined_width_and_drill_screen'];assert combined['failure_count']==3 and combined['CP_failed_pairs']==0 and not combined['replaces_existing_gate'];locked=read(r/'locked-process-screen.json');assert locked['summary']['negative_assumption_adjusted_annular_margins']==4 and locked['summary']['negative_assumption_adjusted_SMT_margins']==3;assert min(e['minimum_combined_drill_margin_mm'] for e in read(r/'locked-process-CP-margin.json')['CP_paths'])>0
print('PASS: native full placement replay; 13 introduced stress failures removed, 11 inherited failures retained; exact 42 fixed routes and 22 vias; real Kelvin pad cuts and both barrel-inclusive returns; CP keepout/drill margins; strict geometry/width/native-length-gate rejection. No routed or manufacturing promotion.')
