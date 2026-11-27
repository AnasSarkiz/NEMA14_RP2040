"""Independent qualification of the two-cap candidate; star gates remain explicit rejections."""
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
import hashlib,copy
r=Path('artifacts/iteration-11');p=Path(sys.argv[1] if len(sys.argv)>1 else r/'final.circuit.json');j=resolve_copper_nets(read(p));old=resolve_copper_nets(b);nm,cs,pn,sps,pps,ps,cts=index(j)
def traces(data):
 st={e['source_trace_id']:e for e in data if e['type']=='source_trace'};return {st[e['source_trace_id']]['name']:e for e in data if e['type']=='pcb_trace'}
a,z=traces(old),traces(j);assert len(z)==44 and a.keys()==z.keys();changed='AUTHORED_VREG_BASELINE'
for n,t in a.items():
 assert t['source_trace_id']==z[n]['source_trace_id'] and t['pcb_trace_id']==z[n]['pcb_trace_id'] and t['subcircuit_connectivity_map_key']==z[n]['subcircuit_connectivity_map_key']
 if n!=changed:assert t['route']==z[n]['route'],('Fixed route changed',n)
for typ in ['source_component','source_port','source_net','source_trace','pcb_via','pcb_board','pcb_hole','pcb_keepout']:
 assert [e for e in old if e['type']==typ]==[e for e in j if e['type']==typ],('Unintended record change',typ)
poses=read('experiments/vreg-star/poses.json')
for n,c in co.items():
 if n in poses:
  assert all(abs(x-y)<1e-12 for x,y in zip([cs[n]['center']['x'],cs[n]['center']['y'],cs[n]['rotation']],poses[n]));assert cs[n]['layer']==c['layer']=='top'
 else:assert all(cs[n][f]==c[f] for f in ['center','rotation','layer','width','height']),('Unintended part move',n)
old_drv=co['U_DRV']['pcb_component_id'];assert [e for e in b if e['type']=='pcb_smtpad' and e['pcb_component_id']==old_drv]==[e for e in j if e['type']=='pcb_smtpad' and e['pcb_component_id']==cs['U_DRV']['pcb_component_id']],'Driver land pattern changed'
# Native 1mm semantic: one direct source and one physical trace, real endpoint identities, true cached length.
t=z[changed];source=next(e for e in j if e['type']=='source_trace' and e.get('name')==changed);assert source['max_length']==1 and len(source['connected_source_port_ids'])==2;assert sum(e['type']=='pcb_trace' and e['source_trace_id']==source['source_trace_id'] for e in j)==1
wire=sum(math.dist([u['x'],u['y']],[v['x'],v['y']]) for u,v in zip(t['route'],t['route'][1:]));assert abs(wire-t['trace_length'])<1e-12 and wire<=1;assert all(e['width']==.16 and e['layer']=='top' for e in t['route']);assert t['route'][0]['start_pcb_port_id']==ps['U_DRV','VREG']['pcb_port_id'] and t['route'][-1]['end_pcb_port_id']==ps['C_VREG','pin1']['pcb_port_id']
pads={e['pcb_port_id']:e for e in j if e['type']=='pcb_smtpad'};contact=[];access=[]
for terminal,node in [(('U_DRV','VREG'),t['route'][0]),(('C_VREG','pin1'),t['route'][-1])]:
 port=ps[terminal];pad=g.pad_shape(pads[port['pcb_port_id']]);assert pad.covers(Point(node['x'],node['y']));area=Point(node['x'],node['y']).buffer(.08,quad_segs=128).intersection(pad).area;assert area>1e-8;access.append(math.dist([node['x'],node['y']],[port['x'],port['y']]));contact.append({'terminal':'.'.join(terminal),'actual_port':port['pcb_port_id'],'point_inside_real_pad':True,'disk_pad_overlap_mm2':area,'pad_centre_access_mm':access[-1]})
# Derive true VREG/foreign copper gaps at +20% width and the unchanged drill budget.
vs=[e for e in j if e['type']=='pcb_via'];rows=[]
for n,tr in z.items():
 for k,(u,v) in enumerate(zip(tr['route'],tr['route'][1:])):
  if u['route_type']!=v['route_type'] or u['route_type']!='wire' or u['layer']!=v['layer']:continue
  shape=LineString([(u['x'],u['y']),(v['x'],v['y'])]).buffer(max(u['width'],v['width'])*.6,quad_segs=128)
  for via in vs:
   if u['layer'] not in via['layers'] or via['subcircuit_connectivity_map_key']==tr['subcircuit_connectivity_map_key']:continue
   gap=g.pad_shape(via,True).distance(shape);rows.append({'path':n,'segment':k,'layer':u['layer'],'via':via['pcb_via_id'],'adjusted_margin_mm':gap-.115-.2})
assert min(e['adjusted_margin_mm'] for e in rows)>0
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);v.spec=copy.deepcopy(read('experiments/placement/generated.json'));vspec=read('experiments/original-process/vias.json')
for q in v.spec['vias']:q.update(vspec[q['name']])
critical,cu=v.verify(p);assert critical['independent']['disconnected_nets']==59;assert not any(e['net']=='VREG' for e in cu['disconnected_nets'])
# Explicitly retain the two original-hole star failures and all-width stress gate.
process=read(r/'final-process.json');summary=process['summary'];assert summary['negative_assumption_adjusted_SMT_margins']==2 and summary['negative_assumption_adjusted_annular_margins']==summary['assumption_adjusted_inner_via_rule_failures']==summary['width_plus_20_percent_shorts']==summary['width_plus_20_percent_spacing_findings']==0
out={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'baseline_head':'4600e6b5d1f7237af2204eefa6457145fd68fcee','poses':poses,'fixed_non_VREG_route_arrays':43,'fixed_actual_via_whole_records':22,'fixed_driver_land_pattern':True,'source_contract_and_native_max_length_exact':True,'VREG':{'one_physical_trace_one_direct_source':True,'native_maximum_mm':1,'actual_wire_mm':wire,'cached_length_matches_physical_recomputation':True,'endpoints':contact,'pad_edge_distance_mm':read('experiments/vreg-star/path.json')['actual_pad_edge_distance_mm'],'complete_port_centre_path_including_pad_access_mm':wire+sum(access),'native_limit_measures':'Authored wire centreline, not pad-centre access or the complete decoupling loop','ground_return_loop_not_qualified':True},'minimum_combined_drill_margin_mm':min(e['adjusted_margin_mm'] for e in rows),'process_summary':summary,'critical':critical,'native_routing_attempted':False,'native_stage_allowed':False,'blockers':['Two original-hole star-via all-SMT tolerance failures; retained land pattern cannot meet required pad gap','16 candidate locality failures and59 open nets','Finished process/CAM/physical/thermal/current/hardware acceptance absent'],'candidate_promoted':False,'manufacturing_qualified':False};Path(sys.argv[2] if len(sys.argv)>2 else r/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print('43 fixed route arrays /22 exact vias; VREG native wire',wire,'complete centre access path',wire+sum(access),'original-hole star failures2; no promotion or routing')
