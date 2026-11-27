"""Exact old CP2/EP pairs and native-bound versus real-circle comparison."""
from pathlib import Path
import json,math
from model import *
from shapely.ops import nearest_points
j=read('artifacts/iteration-7/native-CP2/native.circuit.json');nm,cs,pn,sps,pps,ps,cts=index(j);ep=next(e for e in j if e['type']=='pcb_smtpad' and e['pcb_port_id']==ps['U_DRV','EP']['pcb_port_id']);poly=g.pad_shape(ep);t=next(e for e in j if e['type']=='pcb_trace' and e['pcb_trace_id']=='source_net_21_0');rows=[];cg=[];bg=[]
for i,(a,z) in enumerate(zip(t['route'],t['route'][1:])):
 wire=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128);gap=wire.distance(poly)
 if gap<.15-1e-6:
  u,v=nearest_points(poly,wire);rows.append({'pcb_trace_id':t['pcb_trace_id'],'source_trace_id':t['source_trace_id'],'segment_index':i,'foreign_pad_id':ep['pcb_smtpad_id'],'foreign_pad':'U_DRV.EP','layer':a['layer'],'wire_width_mm':a['width'],'segment_centres_mm':[[a['x'],a['y']],[z['x'],z['y']]],'measured_gap_mm':gap,'nearest_EP_and_wire_points_mm':[[u.x,u.y],[v.x,v.y]],'required_mm':.15})
 for k in [e for e in j if e['type']=='pcb_keepout']:
  x,y,r=k['center']['x'],k['center']['y'],k['radius'];cg.append(wire.distance(Point(x,y).buffer(r,quad_segs=128)));bg.append(wire.distance(box(x-r,y-r,x+r,y+r)))
assert len(rows)==2
r={'saved_head':'6b6aa3455ac8c4abb957ed4559d6f5a9017cb6a8','EP_pad_record':ep,'EP_polygon_world_mm':list(poly.exterior.coords),'two_exact_EP_pairs':rows,'actual_physical_screw_circle_clearance_mm':min(cg),'native_axis_bounds_clearance_mm':min(bg),'keepout_first_cause':'Native keepout uses axis-aligned bounds; no physical circle incursion. Its 0.15mm gate stays in force.','correction':'Route outside actual EP clearance and the unchanged native keepout bounds; no checker or threshold change.'};Path('artifacts/iteration-8/cp2-root-cause.json').write_text(json.dumps(r,indent=2)+'\n');print(rows);print('circle / bounds',min(cg),min(bg))
