"""Keep native conservative keepout failure and actual physical circle clearance distinct."""
from pathlib import Path
import json,sys
sys.path.insert(0,'scripts')
from shapely.geometry import Point,LineString,box
p=Path('artifacts/iteration-7/native-CP2');j=json.load(open(p/'native.circuit.json'));t=next(e for e in j if e['type']=='pcb_trace' and e['pcb_trace_id']=='source_net_21_0');circles=[];bounds=[]
for a,z in zip(t['route'],t['route'][1:]):
 wire=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128)
 for k in [e for e in j if e['type']=='pcb_keepout']:
  x,y,r=k['center']['x'],k['center']['y'],k['radius'];circles.append(wire.distance(Point(x,y).buffer(r,quad_segs=128)));bounds.append(wire.distance(box(x-r,y-r,x+r,y+r)))
native=[e for e in j if e['type']=='pcb_trace_error'];assert len(native)==1;record={'native_error_retained':native,'physical_circle_radius_mm':3.2,'minimum_actual_Cu_to_any_physical_screw_circle_mm':min(circles),'minimum_Cu_to_native_keepout_axis_aligned_bounds_mm':min(bounds),'native_required_gap_mm':.15,'native_result_accepted':False,'no_keepout_or_DRC_modified':True,'checker_evidence':{'version':'0.0.283','function':'checkEachPcbTraceNonOverlapping','file':'@tscircuit/checks/dist/index.js','lines':[3871,3880],'behavior':'Non-pad/non-hole obstacles, including circular keepouts, use segmentToBoundsMinDistance(getCollidableBounds(obj)).'},'next_local_corridor_constraint':'At the upper-right screw bounding box y=9.8, a 0.16mm top wire must remain at or below y=9.57 to preserve the native 0.15mm margin; also clear actual U_DRV.EP by 0.15mm.'};(p/'keepout-diagnosis.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
