"""Scoped copper regressions; never promotes a controller or a fabrication result."""
from pathlib import Path
import json,sys,math,copy,hashlib,importlib.util
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets,pad_cut_topology,shared_outside_pad
from native_sources import source_owner_names
from shapely.geometry import LineString
from shapely.ops import unary_union
spec=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
root=Path('artifacts/iteration-5');raw=(root/'cluster-authored.circuit.json').read_bytes();b=resolve_copper_nets(json.loads(raw));baseline=resolve_copper_nets(json.load(open('artifacts/iteration-4/normal-attempt.circuit.json')));accepted=Path('artifacts/final-source.circuit.json');assert hashlib.sha256(accepted.read_bytes()).hexdigest()=='fe986e028cb398ebf3ed7fcbd9fd5dd8133b64c80aeac673c0540aa5c98cf06b'
def index(board):
 names=source_owner_names(board);sp={e['source_port_id']:e for e in board if e['type']=='source_port'};ports={(names[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in board if e['type']=='pcb_port'};pcs={names[e['source_component_id']]:e for e in board if e['type']=='pcb_component'};pads={e['pcb_port_id']:e for e in board if e['type']=='pcb_smtpad'};st={e.get('name'):e for e in board if e['type']=='source_trace'};return sp,ports,pcs,pads,st
sp,ports,pcs,pads,st=index(b);oldsp,oldports,oldpcs,oldpads,oldst=index(baseline);auth=json.load(open('experiments/compact/authored.json'))
def length(traces):return sum(math.hypot(a['x']-z['x'],a['y']-z['y']) for t in traces for a,z in zip(t['route'],t['route'][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer'])
def selected(board,source):return [e for e in board if e['type']=='pcb_trace' and e.get('source_trace_id')==source['source_trace_id']]
def branch_shapes(traces):
 by={}
 for t in traces:
  for a,z in zip(t['route'],t['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:by.setdefault(a['layer'],[]).append(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(min(a['width'],z['width'])/2,quad_segs=128))
 # Include real barrels touched by this branch, on every physical layer.
 wires={l:unary_union(gs) for l,gs in by.items()};keys={t['subcircuit_connectivity_map_key'] for t in traces}
 for v in b:
  if v['type']!='pcb_via' or v.get('subcircuit_connectivity_map_key') not in keys:continue
  shape=g.pad_shape(v).difference(g.pad_shape(v,True))
  if not any(l in wires and shape.intersection(wires[l]).area>1e-10 for l in v['layers']):continue
  for l in v['layers']:by.setdefault(l,[]).append(shape)
 return {l:unary_union(gs) for l,gs in by.items()}
lengths={};kelvin=[]
for phase in 'AB':
 for pole,pin,target,power in [('POS','pin1',('U_DRV','OUT1A' if phase=='A' else 'OUT2A'),'DRV'),('NEG','pin2',('J_MOTOR',phase+'_PLUS'),'COIL')]:
  name=f'KELVIN_{phase}_{pole}';powername=f'POWER_{phase}_{power}';kt=selected(b,st[name]);pt=selected(b,st[powername]);pad=g.pad_shape(pads[ports['R_SHUNT_'+phase,pin]['pcb_port_id']]);p=ports['R_SHUNT_'+phase,pin];amp=ports['U_I'+phase,'IN_'+pole];net=sp[p['source_port_id']]['subcircuit_connectivity_map_key']
  topo=pad_cut_topology(b,net,p['pcb_port_id'],amp['pcb_port_id'],ports[target]['pcb_port_id'],pad,'top',g.pad_shape);assert topo['actual_shunt_pad_is_required_pickup'],name
  overlap=shared_outside_pad(branch_shapes(kt),branch_shapes(pt),pad,'top');assert overlap<1e-8,(name,overlap)
  for tracegroup,width in [(kt,.16),(pt,.45)]:assert tracegroup and all(abs(n['width']-width)<1e-9 for t in tracegroup for n in t['route'] if n['route_type']=='wire')
  edge=auth['actual_pad_edges'][name];assert pad.boundary.distance(__import__('shapely').geometry.Point(*edge))<1e-6
  kelvin.append({'branch':name,'actual_edge_mm':edge,'shared_winding_copper_outside_actual_pad_mm2':overlap,**topo})
  for group,n in [(kt,name),(pt,powername)]:lengths[n]={'control_planar_wire_mm':length(selected(baseline,oldst[n])),'compact_planar_wire_mm':length(group)}

def return_geometry(board,phase,remove_via=False,narrow=False):
 source=ports['R_S'+phase,'pin2']['pcb_port_id'];ep=ports['U_DRV','EP']['pcb_port_id'];ts=[t for suffix in ['TOP','INNER','EP'] for t in selected(board,st['RETURN_'+phase+'_'+suffix])];records=[]
 for t in ts:
  for a,z in zip(t['route'],t['route'][1:]):
   if a['route_type']!=z['route_type'] or a['route_type']!='wire' or a['layer']!=z['layer']:continue
   width=min(a['width'],z['width'])
   if narrow and t==ts[0]:width=.16
   if width<.6-1e-9:return False
   records.append((LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(width/2,quad_segs=128),[a['layer']],None))
 for pid in [source,ep]:records.append((g.pad_shape(pads[pid]),['top'],pid))
 for i,name in enumerate(['V_G'+phase,'V_STAR_'+phase]):
  if remove_via and i==0:continue
  av=next(v for v in auth['vias'] if v['name']==name);vs=[v for v in board if v['type']=='pcb_via' and math.hypot(v['x']-av['x'],v['y']-av['y'])<1e-8];assert len(vs)==1
  v=vs[0];records.append((g.pad_shape(v).difference(g.pad_shape(v,True)),v['layers'],None))
 parent=list(range(len(records)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,(poly,layers,pid) in enumerate(records):
  for j,(other,ls,_) in enumerate(records[:i]):
   if set(layers)&set(ls) and poly.intersection(other).area>1e-10:parent[root(j)]=root(i)
 ends=[{root(i) for i,r in enumerate(records) if r[2]==pid} for pid in [source,ep]];return bool(ts and set.intersection(*ends))
returns=[]
for phase in 'AB':
 ts=[t for suffix in ['TOP','INNER','EP'] for t in selected(b,st['RETURN_'+phase+'_'+suffix])];wire=length(ts);assert wire<=5 and return_geometry(b,phase);assert not return_geometry(b,phase,remove_via=True);assert not return_geometry(b,phase,narrow=True)
 returns.append({'phase':phase,'full_center_to_center_planar_wire_mm':wire,'width_mm':.6,'only_phase_traces_two_real_barrels_source_pad_and_EP_connected':True,'other_ground_pads_excluded':True,'three_dimensional_length_formula_mm':f'{wire:.12f} + 2 * top_to_inner1_depth_mm','maximum_depth_for_5mm_total_mm':(5-wire)/2,'actual_stack_length_qualified':False})
fixed=['J_PD','J_DATA','J_MOTOR','U_ENCODER','C_ENCODER','C_ENCODER_BULK']
# Every encoder-related capacitor present in the control is fixed, including DNP.
fixed+= [n for n in oldpcs if n.startswith('C_ENC') and n not in fixed]
for n in fixed:
 assert n in oldpcs and n in pcs,n
 for field in ['center','rotation','layer']:assert pcs[n][field]==oldpcs[n][field],(n,field)
for typ in ['pcb_board','pcb_hole','pcb_keepout']:
 fields={'pcb_board':['width','height','num_layers','thickness','min_trace_width','min_trace_to_pad_edge_clearance','min_via_hole_diameter','min_via_pad_diameter'],'pcb_hole':['x','y','hole_diameter'],'pcb_keepout':['center','radius','layers']}[typ]
 assert [{k:e.get(k) for k in fields} for e in b if e['type']==typ]==[{k:e.get(k) for k in fields} for e in baseline if e['type']==typ],typ
cu=json.load(open(root/'cluster-copper.json'));assert cu['input_sha256']==hashlib.sha256(raw).hexdigest()
for k in ['shorts','clearance_violations','board_edge_violations','screw_keepout_violations','drill_spacing_violations','hole_trace_violations','unsupported']:assert not cu[k],k
native=json.load(open(root/'cluster-native.json'));assert all(v['count']==0 for v in native.values());assert json.load(open(root/'cluster-native.json.meta.json'))['input_sha256']==hashlib.sha256(raw).hexdigest()
mfg=json.load(open(root/'cluster-manufacturing.json'));assert mfg['input_sha256']==hashlib.sha256(raw).hexdigest();oldmfg=json.load(open(root/'control-manufacturing.json'));mode=min(oldmfg['vias'],key=lambda v:abs(v['nominal_smt_hole_gap_mm']-.0245171939));assert mode['position_only_smt_hole_gap_mm']<-.05;assert not mfg['supplier_acceptance_verified']
native_driver=resolve_copper_nets(json.load(open(root/'core-driver/native.circuit.json')));assert all(return_geometry(native_driver,phase) for phase in 'AB')
local=json.load(open(root/'full-unpacked-locality.json'));before=json.load(open('artifacts/iteration-4/locality.json'));key=lambda r:tuple(r[k] for k in ['a','pa','b','pb']);oldrows={key(r):r for r in before['rows']};lost=[r for r in local['rows'] if oldrows[key(r)]['pass'] and not r['pass']];gained=[r for r in local['rows'] if not oldrows[key(r)]['pass'] and r['pass']]
report={'source_sha256':hashlib.sha256(raw).hexdigest(),'accepted_source_unchanged':True,'fixed_mechanical_poses_unchanged':True,'scoped_native_selected_checks':{k:v['count'] for k,v in native.items()},'scoped_independent':{k:(len(v) if isinstance(v,list) else v) for k,v in cu.items() if k in ['pcb_traces','pcb_vias','shorts','clearance_violations','disconnected_nets','board_edge_violations','screw_keepout_violations']},'four_actual_pad_pickups':kelvin,'lengths':lengths,'actual_authored_ground_returns':returns,'manufacturing':{'source':mfg['source'],'actual_stack_and_process_selected':False,'position_only_smt_failures':sum(not v['position_only_smt_nonoverlap'] for v in mfg['vias']),'position_only_inner_via_rule_failures':sum(any(v['layers'][l]['position_adjusted_inner_via_rule_pass'] is False for l in ['inner1','inner2']) for v in mfg['vias']),'old_mode_via_nominal_gap_mm':mode['nominal_smt_hole_gap_mm'],'old_mode_via_position_adjusted_gap_mm':mode['position_only_smt_hole_gap_mm'],'supplier_acceptance_verified':False},'full_unpacked_locality':{'control_pass':sum(r['pass'] for r in before['rows']),'candidate_pass':sum(r['pass'] for r in local['rows']),'total':len(local['rows']),'gained_targets':gained,'regressed_targets':lost,'full_board_candidate_accepted':False},'negative_controls':{'missing_return_barrel_rejected':2,'narrow_return_rejected':2,'old_mode_via_tolerance_rejected':1},'full_board_routed_DRC_pass':False,'manufacturing_qualified':False}
cli=json.load(open(root/'native-cli-exit.json'));cj=json.load(open('dist/experiments/compact/cluster/circuit.json')) if Path('dist/experiments/compact/cluster/circuit.json').exists() else json.loads(__import__('gzip').decompress((root/'native-cli.circuit.json.gz').read_bytes()));types=['source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_via','pcb_trace','pcb_board','pcb_hole','pcb_keepout'];assert cli['exit_code']==0;assert all([e for e in b if e['type']==t]==[e for e in resolve_copper_nets(cj) if e['type']==t] for t in types);report['native_cli']={**cli,'source_and_pcb_arrays_identical':types,'full_routing_test':False};
if len(sys.argv)>1:
 replay=resolve_copper_nets(json.load(open(sys.argv[1])));assert all([e for e in b if e['type']==t]==[e for e in replay if e['type']==t] for t in types),'Fresh native source/PCB geometry changed'
 report['fresh_native_replay_source_and_pcb_equal']=True
(root/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Verified scoped copper, 4 actual pickups, 2 isolated returns, fixed mechanics, 5 rejection controls; full board rejected')
