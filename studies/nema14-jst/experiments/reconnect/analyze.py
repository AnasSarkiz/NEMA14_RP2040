"""Measure real native copper and baseline lower bounds; never invent a previous routed loop."""
from pathlib import Path
import json,sys,math,hashlib,importlib.util,copy
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
p=Path(sys.argv[1]);j=resolve_copper_nets(read(p));_,cs,_,sps,pps,ps,_=index(j);old=resolve_copper_nets(b);_,_,_,os,op,ops,_=index(old)
st={e['source_trace_id']:e for e in j if e['type']=='source_trace'};groups={st[t['source_trace_id']].get('name',''):t for t in j if t['type']=='pcb_trace'};pads={e['pcb_port_id']:e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole']};oldpads={e['pcb_port_id']:e for e in old if e['type'] in ['pcb_smtpad','pcb_plated_hole']}
newvias=read('experiments/reconnect/vias.json');vias=[e for e in j if e['type']=='pcb_via'];via={v['name']:next(e for e in vias if math.dist([e['x'],e['y']],[v['x'],v['y']])<1e-9) for v in newvias}
def endpoint(ref):
 owner,pin=ref[1:].split(' > .')
 if owner in via:return via[owner]['x'],via[owner]['y'],via[owner]['subcircuit_connectivity_map_key']
 hit=[e for (n,k),e in ps.items() if n==owner and pin in sps[e['source_port_id']].get('port_hints',[k])];assert len(hit)==1,ref;e=hit[0];return e['x'],e['y'],sps[e['source_port_id']]['subcircuit_connectivity_map_key']
rows=[]
for r in read('experiments/reconnect/paths.json'):
 t=groups[r['name']];wire=t['route'];assert all(e['route_type']=='wire' and e['layer']==r['layer'] and e['width']==r['width_mm'] for e in wire),(r['name'],wire)
 actual=[]
 for e in wire:
  q=[e['x'],e['y']]
  if not actual or actual[-1]!=q:actual.append(q)
 assert len(actual)==len(r['world_points_mm']);assert all(math.dist(a,z)<1e-9 for a,z in zip(actual,r['world_points_mm'])),r['name']
 for e,ref in [(wire[0],r['from']),(wire[-1],r['to'])]:
  x,y,key=endpoint(ref);assert math.dist([x,y],[e['x'],e['y']])<1e-9;assert key==t['subcircuit_connectivity_map_key'],(r['name'],'wrong net')
 length=sum(math.dist(a,z) for a,z in zip(actual,actual[1:]));assert abs(length-r['wire_length_mm'])<1e-9
 rows.append({'name':r['name'],'native_trace_id':t['pcb_trace_id'],'layer':r['layer'],'width_mm':r['width_mm'],'wire_length_mm':length,'net_key':t['subcircuit_connectivity_map_key'],'native_endpoints_and_world_points_match':True,'minimum_offline_foreign_copper_gap_mm':r['minimum_other_copper_gap_mm']})
# Original fixed geometry: deliberately reroute CP1; every other prior copper record must match.
ost={e['source_trace_id']:e for e in old if e['type']=='source_trace'};oldtr={ost[e['source_trace_id']].get('name',''):e for e in old if e['type']=='pcb_trace'}
# Fresh replay may differ in the derived JS length cache across machines.
# Validate that cache independently, then compare every physical/identity field exactly.
# Native before/after byte-preservation is a separate strict check, never normalized.
def physical_record(t):
 q=copy.deepcopy(t);actual=sum(math.dist([a['x'],a['y']],[z['x'],z['y']]) for a,z in zip(q['route'],q['route'][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']);assert abs(q['trace_length']-actual)<1e-12,('invalid derived length cache',q['pcb_trace_id']);q.pop('trace_length');return q
for name,t in oldtr.items():
 if name=='AUTHORED_CP1_CORRIDOR':continue
 old_record,new_record=physical_record(t),physical_record(groups[name]);assert old_record==new_record,('prior fixed physical record changed',name,{k:[old_record.get(k),new_record.get(k)] for k in set(old_record)|set(new_record) if old_record.get(k)!=new_record.get(k)})
oldv=[e for e in old if e['type']=='pcb_via'];assert all(e in vias for e in oldv),'Prior via record changed'
# Baseline distance between physical pad edges is a rigorous optimistic lower bound.
pairs=[('flyback_sink',('BZ1','_NEG'),('D_BUZZER','anode'),['BUZ_FLYBACK_SINK']),('flyback_supply',('D_BUZZER','cathode'),('BZ1','_POS'),['BUZ_FLYBACK_SUPPLY']),('switch_supply',('C_BUZZER','pin1'),('BZ1','_POS'),['BUZ_SWITCH_SUPPLY__0','BUZ_SWITCH_SUPPLY__1','BUZ_SWITCH_SUPPLY__2']),('switch_drain',('BZ1','_NEG'),('Q_BUZZER','pin3'),['BUZ_SWITCH_DRAIN']),('switch_return',('Q_BUZZER','pin2'),('C_BUZZER','pin2'),['BUZ_SWITCH_RETURN'])]
lengths={r['name']:r['wire_length_mm'] for r in rows};loops=[];depth=.035/2+.1164+.0152+1.265+.0152/2
for name,a,z,ns in pairs:
 # MOS source pin numbering is resolved from actual native hints, not assumed here.
 if a[0]=='Q_BUZZER':a=next(k for k,e in ops.items() if k[0]=='Q_BUZZER' and 'S' in os[e['source_port_id']].get('port_hints',[]))
 if z[0]=='Q_BUZZER':z=next(k for k,e in ops.items() if k[0]=='Q_BUZZER' and 'D' in os[e['source_port_id']].get('port_hints',[]))
 pa,pz=ops[a],ops[z];edge=g.pad_shape(oldpads[pa['pcb_port_id']]).distance(g.pad_shape(oldpads[pz['pcb_port_id']]));barrel=2*depth if name=='switch_supply' else 0
 loops.append({'branch':name,'baseline_terminal_refs':['.'.join(a),'.'.join(z)],'baseline_physical_pad_edge_lower_bound_mm':edge,'baseline_center_euclidean_lower_bound_mm':math.dist([pa['x'],pa['y']],[pz['x'],pz['y']]),'baseline_actual_copper_available':False,'candidate_native_fragments':ns,'candidate_actual_wire_mm':sum(lengths[n] for n in ns),'candidate_conducted_barrel_mm':barrel,'candidate_wire_plus_barrel_mm':sum(lengths[n] for n in ns)+barrel})
summary={}
for label,selected in [('flyback',loops[:2]),('switch',loops[2:])]:
 lb=sum(r['baseline_physical_pad_edge_lower_bound_mm'] for r in selected);actual=sum(r['candidate_wire_plus_barrel_mm'] for r in selected);summary[label]={'baseline_sum_physical_edge_lower_bound_mm':lb,'candidate_external_copper_wire_plus_barrel_mm':actual,'candidate_shorter_than_optimistic_baseline':actual<lb,'minimum_reduction_mm':lb-actual,'package_internal_paths_not_measured':True}
cu=g.inspect(str(p));report={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'prior_unchanged_trace_records':32,'prior_unchanged_via_records':20,'intentional_prior_path_reroutes':['AUTHORED_CP1_CORRIDOR'],'traces':len(groups),'vias':len(vias),'new_vias':newvias,'actual_native_paths':rows,'loop_branches':loops,'loop_comparison':summary,'top_to_inner2_conducted_depth_mm':depth,'stack_tolerances_confirmed':False,'independent':{k:len(cu[k]) for k in ['shorts','clearance_violations','drill_spacing_violations','hole_trace_violations','board_edge_violations','screw_keepout_violations','disconnected_nets']},'manufacturing_qualified':False,'full_controller_promoted':False}
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['traces','vias','loop_comparison','independent']},indent=2))
