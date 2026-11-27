"""Fresh pinned native replay of the rejected original-hole comparison; no promotion or gate suppression."""
from pathlib import Path
import json,copy,subprocess,sys,math,importlib.util
sys.path.insert(0,'experiments/original-process')
from model import read
r=Path('artifacts/iteration-10');tmp=Path('.config/original-process-test');tmp.mkdir(parents=True,exist_ok=True)
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
p=tmp/'fresh.circuit.json';run(['bun','experiments/original-process/render.ts',str(p)]);a,b=read(r/'final.circuit.json'),read(p)
def records(data,typ):
 out=copy.deepcopy([e for e in data if e['type']==typ])
 if typ=='pcb_trace':
  for e in out:
   actual=sum(math.dist([u['x'],u['y']],[v['x'],v['y']]) for u,v in zip(e['route'],e['route'][1:]) if u['route_type']==v['route_type']=='wire' and u['layer']==v['layer']);assert abs(e.pop('trace_length')-actual)<1e-12
 return out
for typ in ['source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_courtyard_outline','pcb_trace','pcb_via','pcb_board','pcb_hole','pcb_keepout']:assert records(a,typ)==records(b,typ),('Native replay drift',typ)
run([sys.executable,'experiments/original-process/audit.py',str(p),str(tmp/'audit.json')]);run([sys.executable,'experiments/placement/screen-process.py',str(p),str(tmp/'process.json')]);q=read(tmp/'audit.json');s=read(tmp/'process.json')['summary'];assert len(q['spacing_11_owned_findings'])==11 and all(e['width_stress_introduces_failure'] for e in q['spacing_11_owned_findings']);assert not q['supplemental_combined_width_and_drill']['failed'];assert q['supplemental_combined_width_and_drill']['minimum_margin_mm']>0;assert len(q['original_hole_SMT_failures'])==2;assert s['width_plus_20_percent_shorts']==s['width_plus_20_percent_spacing_findings']==s['negative_assumption_adjusted_annular_margins']==s['assumption_adjusted_inner_via_rule_failures']==0;assert s['negative_assumption_adjusted_SMT_margins']==2 and not q['promoted'] and not q['native_routing_attempted'];assert q['unchanged_route_arrays']==33
for kind in ['fixed_coordinate','hole_process','VREG_gate','wrong_net']:
 bad=copy.deepcopy(b)
 if kind=='hole_process':next(e for e in bad if e['type']=='pcb_via')['hole_diameter']=.2
 elif kind=='VREG_gate':next(e for e in bad if e['type']=='source_trace' and e.get('name')=='AUTHORED_VREG_BASELINE')['max_length']=3
 else:
  st={e['source_trace_id']:e.get('name') for e in bad if e['type']=='source_trace'};t=next(e for e in bad if e['type']=='pcb_trace' and st[e['source_trace_id']].startswith('KELVIN_A_POS'))
  if kind=='wrong_net':t['subcircuit_connectivity_map_key']='wrong-net'
  else:t['route'][1]['x']=math.nextafter(t['route'][1]['x'],math.inf)
 f=tmp/(kind+'.json');f.write_text(json.dumps(bad));z=subprocess.run([sys.executable,'experiments/original-process/audit.py',str(f),str(tmp/'rejected.json')],capture_output=True);assert z.returncode,kind
checks=read(r/'final-native.json');assert all(v['count']==0 for v in checks.values());allchecks=read(r/'final-native.json.all-routing.json');assert allchecks['by_type']=={'pcb_port_not_connected_error':300,'pcb_trace_too_long_error':1,'pcb_trace_style_warning':4};domain=read(r/'EP-domain.json');assert len(domain['bounded_via_radius_cases'])==22 and all(e['reachable_centre_area_mm2']==0 for e in domain['bounded_via_radius_cases']);assert all(e['gap_shortfall_mm']>.079 for e in domain['local_GND_gap_bounds']);assert read(r/'cli-replay.json')['all_physical_copper_coordinates_widths_layers_and_nets_exact']
print('PASS: original .30 holes, 11→0 inherited spacing, 3→0 combined drill pairs, 33 exact fixed routes, four physical Kelvin pad cuts, both barrel-inclusive returns; original-hole star margins and VREG gate remain rejected. No routed or manufacturing promotion.')
