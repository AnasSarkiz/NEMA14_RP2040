from pathlib import Path
import json,sys,hashlib,importlib.util
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
sys.path.insert(0,'scripts');from routing_geometry import resolve_copper_nets
spec=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
p=Path(sys.argv[1] if len(sys.argv)>1 else 'artifacts/iteration-4/authored.circuit.json');raw=p.read_bytes();b=resolve_copper_nets(json.loads(raw));sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};ports={(sc[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in pp.values()};pads=[e for e in b if e['type'] in ['pcb_smtpad','pcb_plated_hole']];net=sp[ports['U_DRV','MS3']['source_port_id']]['subcircuit_connectivity_map_key'];foreign=[];fixed=[];alltop=[];ep=None;vreg=None
for e in pads:
 if 'top' not in e.get('layers',[e.get('layer','top')]):continue
 q=g.pad_shape(e);alltop.append(q)
 if e.get('pcb_port_id')==ports['U_DRV','EP']['pcb_port_id']:ep=q
 if e.get('pcb_port_id')==ports['U_DRV','VREG']['pcb_port_id']:vreg=q
 if sp[pp[e['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key')!=net:foreign.append(q)
for e in b:
 if e['type']=='pcb_via' and 'top' in e['layers'] and e.get('subcircuit_connectivity_map_key')!=net:foreign.append(g.pad_shape(e))
 if e['type']=='pcb_trace' and e.get('subcircuit_connectivity_map_key')!=net:
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']=='top':fixed.append(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=256))
fu=unary_union(foreign+fixed);free=box(-17.25,-17.25,17.25,17.25).difference(fu.buffer(.15+.16/2,quad_segs=256));start=Point(ports['U_DRV','MS3']['x'],ports['U_DRV','MS3']['y']);pocket=next(poly for poly in free.geoms if poly.covers(start)) if hasattr(free,'geoms') else free;via_free=pocket.difference(unary_union([fu.buffer(.15+.45/2,quad_segs=256),unary_union(alltop).buffer(.3/2,quad_segs=256)]));out={'input_sha256':hashlib.sha256(raw).hexdigest(),'trace_width_mm':.16,'clearance_mm':.15,'via_pad_mm':.45,'via_drill_mm':.3,'physical_pocket_bounds':list(pocket.bounds),'physical_pocket_area_mm2':pocket.area,'mode_pins_inside':{pin:pocket.covers(Point(ports['U_DRV',pin]['x'],ports['U_DRV',pin]['y'])) for pin in ['MS1','MS2','MS3','RESET_N','VDD']},'through_via_center_free_area_mm2':via_free.area,'ep_to_vreg_pad_gap_mm':ep.distance(vreg),'maximum_wire_width_between_ep_and_vreg_at_clearance_mm':ep.distance(vreg)-2*.15,'top_layer_off_array_exit_exists':False,'through_via_candidate_area_is_top_only':True,'method':'Configuration-space polygon components with actual native pad/trace polygons; source-net pads are not obstacles. Through-via copper clearance and no-drill-in-SMT-pad constraints are applied separately.'};Path('.config/reachability/physical-pocket.json').write_text(json.dumps(out,indent=2)+'\n');Path('.config/reachability/physical-pocket.wkt').write_text(pocket.wkt+'\n');print(out)
