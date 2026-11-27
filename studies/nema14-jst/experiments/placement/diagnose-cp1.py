"""Reproduce the saved CP1 pad clearances using independent actual pad and wire geometry."""
from pathlib import Path
import json,math
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import nearest_points
j=resolve_copper_nets(read('artifacts/iteration-6/cli-guarded-CP1/native.circuit.json'));sco={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'};sps={e['source_port_id']:e for e in j if e['type']=='source_port'};pps={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'}
pad=next(e for e in j if e['type']=='pcb_smtpad' and sco[sps[pps[e['pcb_port_id']]['source_port_id']]['source_component_id']]=='U_DRV' and sps[pps[e['pcb_port_id']]['source_port_id']]['name']=='CP2');poly=g.pad_shape(pad);rows=[]
for t in j:
 if t['type']!='pcb_trace' or t['pcb_trace_id'].startswith('pcb_trace_'):continue
 for i,(a,z) in enumerate(zip(t['route'],t['route'][1:])):
  if a['route_type']!=z['route_type'] or a['route_type']!='wire' or a['layer']!=z['layer'] or a['layer']!='top':continue
  wire=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128);gap=wire.distance(poly)
  if gap<.15-1e-6:
   u,v=nearest_points(poly,wire);rows.append({'trace':t['pcb_trace_id'],'segment':i,'wire_centerline_mm':[[a['x'],a['y']],[z['x'],z['y']]],'actual_width_mm':a['width'],'foreign_pad':'U_DRV.CP2','actual_clearance_mm':gap,'required_mm':.15,'nearest_pad_and_wire_points_mm':[[u.x,u.y],[v.x,v.y]],'pad_record':pad})
assert len(rows)==2;Path('artifacts/iteration-7/cp1-reproduction.json').write_text(json.dumps({'native_input':'76db864 CLI guarded CP1','violations':rows,'no_router_run':True},indent=2)+'\n');print([(r['segment'],r['actual_clearance_mm']) for r in rows])
