"""Audit actual native Core output; a solved SRJ is not routed acceptance."""
from pathlib import Path
import json,hashlib,sys,math,importlib.util
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets
from shapely.geometry import LineString
from shapely.ops import unary_union
p=Path('artifacts/iteration-5/core-driver');b=resolve_copper_nets(json.load(open('artifacts/iteration-5/cluster-authored.circuit.json')));c=resolve_copper_nets(json.load(open(p/'native.circuit.json')));st={e['source_trace_id']:e for e in c if e['type']=='source_trace'};old={e['pcb_trace_id']:e for e in b if e['type']=='pcb_trace'};new={e['pcb_trace_id']:e for e in c if e['type']=='pcb_trace'}
def shape(t):
 out={}
 for a,z in zip(t['route'],t['route'][1:]):
  if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:out.setdefault(a['layer'],[]).append(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(min(a['width'],z['width'])/2,quad_segs=128))
 return {l:unary_union(q) for l,q in out.items()}
changes=[]
for tid,t in old.items():
 assert tid in new
 a,z=shape(t),shape(new[tid]);area=sum(a[l].symmetric_difference(z[l]).area if l in a and l in z else (a.get(l) or z[l]).area for l in set(a)|set(z));assert st[new[tid]['source_trace_id']].get('name')==st[t['source_trace_id']].get('name')
 if area>1e-8:changes.append({'id':tid,'branch':st[t['source_trace_id']].get('name'),'wire_copper_symmetric_difference_mm2':area})
returns=[tid for tid,t in old.items() if st[t['source_trace_id']].get('name','').startswith('RETURN_')];assert all(tid not in [x['id'] for x in changes] for tid in returns)
cu=json.load(open(p/'copper.json'));critical=json.load(open(p/'critical.json'));native=json.load(open(p/'native-checks.json'));alln=json.load(open(p/'native-checks.json.all-routing.json'));measure=[]
for t in c:
 if t['type']!='pcb_trace' or t['pcb_trace_id'] in old:continue
 source=st.get(t.get('source_trace_id'),{});net=next((n['name'] for n in c if n['type']=='source_net' and n['subcircuit_connectivity_map_key']==t.get('subcircuit_connectivity_map_key')),None);w=[n['width'] for n in t['route'] if n['route_type']=='wire'];length=sum(math.hypot(a['x']-z['x'],a['y']-z['y']) for a,z in zip(t['route'],t['route'][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']);measure.append({'trace':t['pcb_trace_id'],'net':net,'minimum_wire_width_mm':min(w),'planar_wire_length_mm':length,'native_source_trace_id':source.get('source_trace_id')})
report={'input_authored_sha256':hashlib.sha256(Path('artifacts/iteration-5/cluster-authored.circuit.json').read_bytes()).hexdigest(),'native_output_sha256':hashlib.sha256((p/'native.circuit.json').read_bytes()).hexdigest(),'native_materialization':True,'scoped_solver':json.load(open(p/'result.json')),'fixed_authored_wire_changes':changes,'six_ground_wire_shapes_preserved':True,'four_actual_pad_pickoffs_pass':all(x['pickup_geometry_pass'] and x['full_branch_continuity_verified'] for x in critical['kelvin_pickups']),'selected_native_checks':{k:v['count'] for k,v in native.items()},'native_all_routing_by_type':alln['by_type'],'independent':{k:(len(v) if isinstance(v,list) else v) for k,v in cu.items() if k in ['pcb_traces','pcb_vias','shorts','clearance_violations','board_edge_violations','screw_keepout_violations','drill_spacing_violations','hole_trace_violations','disconnected_nets']},'new_auto_wire_measurements':measure,'candidate_accepted':False,'full_board_routed':False,'manufacturing_qualified':False}
sums={};widths={}
for t in c:
 if t['type']!='pcb_trace':continue
 name=st[t['source_trace_id']].get('name')
 if not name:continue
 sums[name]=sums.get(name,0)+sum(math.hypot(a['x']-z['x'],a['y']-z['y']) for a,z in zip(t['route'],t['route'][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']);widths[name]=sorted(set(widths.get(name,[])+[n['width'] for n in t['route'] if n['route_type']=='wire']))
report['actual_native_authored_branch_planar_wire_mm']=sums;report['actual_native_authored_branch_widths_mm']=widths;report['limits']=['Ground return wire lengths exclude barrels; selected stack required for 5mm total-length acceptance.','Automatic driver supply neckdowns down to 0.16mm are not validated for current/thermal capacity. Zero thickness warnings are not current acceptance.','Six authored trace wire shapes change in this rejected isolated output. Accepted experiment source remains untouched.']
(p/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Native geometry changes',len(changes),'padcuts',report['four_actual_pad_pickoffs_pass'],'independent',report['independent'])
