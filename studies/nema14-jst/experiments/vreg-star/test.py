"""Native replay verifies the positive VREG leg and the retained star rejection state."""
from pathlib import Path
import json,copy,subprocess,sys,math
sys.path.insert(0,'experiments/vreg-star')
from model import read
r=Path('artifacts/iteration-11');tmp=Path('.config/vreg-star-test');tmp.mkdir(parents=True,exist_ok=True)
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
p=tmp/'fresh.circuit.json';run(['bun','experiments/vreg-star/render.ts',str(p)]);a,b=read(r/'final.circuit.json'),read(p)
def records(data,typ):
 out=copy.deepcopy([e for e in data if e['type']==typ])
 if typ=='pcb_trace':
  for e in out:
   actual=sum(math.dist([u['x'],u['y']],[v['x'],v['y']]) for u,v in zip(e['route'],e['route'][1:]) if u['route_type']==v['route_type']=='wire' and u['layer']==v['layer']);assert abs(e.pop('trace_length')-actual)<1e-12
 return out
for typ in ['source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_courtyard_outline','pcb_trace','pcb_via','pcb_board','pcb_hole','pcb_keepout']:assert records(a,typ)==records(b,typ),('Native replay drift',typ)
run([sys.executable,'experiments/vreg-star/verify.py',str(p),str(tmp/'verification.json')]);run([sys.executable,'experiments/placement/screen-process.py',str(p),str(tmp/'process.json')]);q=read(tmp/'verification.json');s=read(tmp/'process.json')['summary'];assert q['fixed_non_VREG_route_arrays']==43 and q['fixed_actual_via_whole_records']==22;assert .98<q['VREG']['actual_wire_mm']<1 and q['VREG']['complete_port_centre_path_including_pad_access_mm']>2;assert s['width_plus_20_percent_shorts']==s['width_plus_20_percent_spacing_findings']==s['negative_assumption_adjusted_annular_margins']==s['assumption_adjusted_inner_via_rule_failures']==0 and s['negative_assumption_adjusted_SMT_margins']==2
for kind in ['fixed_coordinate','fake_cached_length','native_maximum','endpoint_identity','hole_process']:
 bad=copy.deepcopy(b);st={e['source_trace_id']:e.get('name','') for e in bad if e['type']=='source_trace'};t=next(e for e in bad if e['type']=='pcb_trace' and st[e['source_trace_id']]=='AUTHORED_VREG_BASELINE')
 if kind=='fixed_coordinate':e=next(e for e in bad if e['type']=='pcb_trace' and st[e['source_trace_id']]=='AUTHORED_CP1_CORRIDOR');e['route'][1]['x']=math.nextafter(e['route'][1]['x'],math.inf)
 elif kind=='fake_cached_length':t['trace_length']=.5
 elif kind=='native_maximum':next(e for e in bad if e['type']=='source_trace' and e.get('name')=='AUTHORED_VREG_BASELINE')['max_length']=1.1
 elif kind=='endpoint_identity':t['route'][0]['start_pcb_port_id']='pcb_port_0'
 else:next(e for e in bad if e['type']=='pcb_via')['hole_diameter']=.2
 f=tmp/(kind+'.json');f.write_text(json.dumps(bad));z=subprocess.run([sys.executable,'experiments/vreg-star/verify.py',str(f),str(tmp/'rejected.json')],capture_output=True);assert z.returncode,kind
native=read(r/'final-native.json');assert all(e['count']==0 for e in native.values());assert read(r/'final-native.json.all-routing.json')['by_type']=={'pcb_port_not_connected_error':300,'pcb_trace_style_warning':4};bound=read(r/'star-access-bound.json');assert bound['only_driver_SMT_pads_used']==29 and len(bound['necessary_access_cases'])==6 and all(e['necessary_reachable_via_centre_area_at_0_115_mm2']==0 and e['optimistic_max_radial_budget_interval_mm'][1]<.079 and e['extra_optimistic_reach_allowance_mm']==.001 for e in bound['necessary_access_cases']);assert read(r/'cli-replay.json')['all_physical_copper_coordinates_widths_layers_and_nets_exact'];assert not q['native_stage_allowed'] and not q['candidate_promoted'];assert read(r/'body-bounds.json')['screw_clear'] and read(r/'body-bounds.json')['plug_clear']
print('PASS: native VREG maximum1 retained, actual wire0.990775mm with real pad endpoints;43 fixed routes/22 exact original-hole vias; all width/foreign-drill/nominal gates clean; two star tolerance failures retained; no routing or promotion.')
