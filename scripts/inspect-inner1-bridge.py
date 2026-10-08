#!/usr/bin/env python3
"""Compare actual pre/post repair inner1 ground and projected fast signal routes."""
import hashlib,importlib.util,json,pathlib
from shapely.geometry import LineString,Polygon
from shapely.ops import unary_union,nearest_points
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cam',ROOT/'scripts/audit-manufacturing.py');cam=importlib.util.module_from_spec(spec);spec.loader.exec_module(cam)
source=ROOT/'artifacts/board.circuit.json';saved=source.read_bytes();sha=hashlib.sha256(saved).hexdigest();j=json.loads(saved)
audit=json.loads((ROOT/'artifacts/manufacturing/audit.json').read_text())
assert audit['status']=='PASS' and audit['source_sha256']==sha
assert hashlib.sha256((ROOT/'artifacts/nema14-gerbers.zip').read_bytes()).hexdigest()==audit['archive']['sha256']
assert hashlib.sha256((ROOT/'artifacts/manufacturing/In1_Cu.gbr').read_bytes()).hexdigest()==audit['files']['In1_Cu.gbr']['sha256']
previous=ROOT/'artifacts/manufacturing-before-iovdd10-repair';old_bytes=(previous/'source.circuit.json').read_bytes();old=json.loads(old_bytes);oldfiles=previous/'parsed-files-and-audit'
old_audit=json.loads((oldfiles/'audit.json').read_text())
assert old_audit['status']=='PASS' and old_audit['source_sha256']==hashlib.sha256(old_bytes).hexdigest()
assert hashlib.sha256((previous/'actual-export.zip').read_bytes()).hexdigest()==old_audit['archive']['sha256']
assert hashlib.sha256((oldfiles/'In1_Cu.gbr').read_bytes()).hexdigest()==old_audit['files']['In1_Cu.gbr']['sha256']

def ground(circuit,directory):
 net=next(e['source_net_id'] for e in circuit if e['type']=='source_net' and e['name']=='GND')
 pours=[]
 for e in circuit:
  if e['type']=='pcb_copper_pour' and e['layer']=='inner1' and e.get('source_net_id')==net:
   b=e['brep_shape'];coords=lambda r:[(p['x'],p['y']) for p in r['vertices']];pours.append(Polygon(coords(b['outer_ring']),[coords(h) for h in b.get('inner_rings',[])]))
 expected=unary_union(pours)
 actual=cam.gerber(directory/'In1_Cu.gbr')[0]
 holes=unary_union([cam.drill(p)[0] for p in directory.glob('*.drl')]);actual=actual.difference(holes)
 parts=list(actual.geoms) if hasattr(actual,'geoms') else [actual]
 return unary_union([p for p in parts if p.intersection(expected).area>1e-4])

before=ground(old,oldfiles);after=ground(j,ROOT/'artifacts/manufacturing');loss=before.difference(after);added=after.difference(before)
# A 0.0002 mm edge erosion excludes coordinate/parser noise, matching the main CAM audit.
robustloss=loss.buffer(-.0002)
nets={e['source_net_id']:e['name'] for e in j if e['type']=='source_net'}
bridge_segments=[]
for e in j:
 if e['type']=='pcb_trace' and nets.get(e.get('source_net_id'))=='V3V3':
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='inner1':bridge_segments.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]))
bridge_line=unary_union(bridge_segments)
cut_parts=list(robustloss.geoms) if hasattr(robustloss,'geoms') else [robustloss]
bridge_cut=unary_union([p for p in cut_parts if p.distance(bridge_line)<1e-5])
assert not bridge_cut.is_empty
rows=[]
for e in j:
 if e['type']!='pcb_trace':continue
 name=nets.get(e.get('source_net_id'))
 if name not in {'USB_DP','USB_DM'} and not (name or '').startswith('QSPI_'):continue
 for a,b in zip(e['route'],e['route'][1:]):
  if a['route_type']!= 'wire' or b['route_type']!='wire' or a['layer']!=b['layer']:continue
  line=LineString([(a['x'],a['y']),(b['x'],b['y'])]);conductor=line.buffer(max(a['width'],b['width'])/2,quad_segs=64)
  nearest_edge,nearest_cut=nearest_points(conductor,robustloss);nearest_bridge_line,nearest_bridge_cut=nearest_points(line,bridge_cut)
  rows.append({'nearest_bridge_centerline_mm':[nearest_bridge_line.x,nearest_bridge_line.y],'nearest_bridge_cut_mm':[nearest_bridge_cut.x,nearest_bridge_cut.y],'nearest_trace_edge_mm':[nearest_edge.x,nearest_edge.y],'nearest_added_cut_mm':[nearest_cut.x,nearest_cut.y],'net':name,'trace_id':e['pcb_trace_id'],'layer':a['layer'],'segment_mm':[[a['x'],a['y']],[b['x'],b['y']]],'added_ground_cut_distance_mm':line.distance(robustloss),'centerline_length_over_added_ground_cut_mm':line.intersection(robustloss).length,'trace_edge_distance_to_bridge_cut_mm':conductor.distance(bridge_cut),'centerline_distance_to_bridge_cut_mm':line.distance(bridge_cut),'trace_edge_distance_to_added_cut_mm':conductor.distance(robustloss),'projected_trace_Cu_overlap_added_cut_mm2':conductor.intersection(robustloss).area})
summary=[]
for name in sorted({r['net'] for r in rows}):
 r=[r for r in rows if r['net']==name];summary.append({'net':name,'minimum_added_cut_distance_mm':min(p['added_ground_cut_distance_mm'] for p in r),'length_over_added_cut_mm':sum(p['centerline_length_over_added_ground_cut_mm'] for p in r),'minimum_centerline_distance_to_bridge_cut_mm':min(p['centerline_distance_to_bridge_cut_mm'] for p in r),'minimum_trace_edge_distance_to_bridge_cut_mm':min(p['trace_edge_distance_to_bridge_cut_mm'] for p in r),'minimum_trace_edge_distance_to_added_cut_mm':min(p['trace_edge_distance_to_added_cut_mm'] for p in r),'trace_Cu_overlap_added_cut_mm2':sum(p['projected_trace_Cu_overlap_added_cut_mm2'] for p in r)})
result={'source_sha256':sha,'actual_archive_sha256':audit['archive']['sha256'],'actual_inner1_sha256':audit['files']['In1_Cu.gbr']['sha256'],'before_source_sha256':hashlib.sha256((previous/'source.circuit.json').read_bytes()).hexdigest(),'actual_ground_before_mm2':before.area,'actual_ground_after_mm2':after.area,'actual_ground_removed_mm2':loss.area,'removed_ground_bounds_mm':list(robustloss.bounds),'actual_ground_added_mm2':added.area,'ground_after_planar_parts':len(after.geoms) if hasattr(after,'geoms') else 1,'projected_fast_signal_review':summary,'nearest_fast_signal_segments':{name:min([r for r in rows if r['net']==name],key=lambda r:r['trace_edge_distance_to_added_cut_mm']) for name in sorted({r['net'] for r in rows})},'bridge_specific_actual_cut_mm2':bridge_cut.area,'bridge_specific_actual_cut_bounds_mm':list(bridge_cut.bounds),'added_cut_components':[{'area_mm2':g.area,'bounds_mm':list(g.bounds)} for g in (robustloss.geoms if hasattr(robustloss,'geoms') else [robustloss])],'fast_signal_segments_over_added_cut':[r for r in rows if r['centerline_length_over_added_ground_cut_mm']>1e-5 or r['projected_trace_Cu_overlap_added_cut_mm2']>1e-7],'scope':'Actual independently parsed pre/post inner1 Cu and physical drill holes; GND polygons assigned by overlap with source GND pours after full CAM source/net verification. Signal centerlines projected geometrically. This does not establish USB impedance, return-current density, EMC or physical qualification.'}
assert source.read_bytes()==saved
(ROOT/'artifacts/manufacturing/inner1-local-bridge-review.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,indent=2))
