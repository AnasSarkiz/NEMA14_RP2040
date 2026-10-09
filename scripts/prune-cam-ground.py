"""Remove ground splinters revealed by finished Gerber/drill topology.
Guarded to motor bay only. Source pads/traces/foreign pours remain unchanged.
"""
import json,pathlib,hashlib
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json';j=json.loads(path.read_text());audit=json.loads((root/'artifacts/manufacturing/audit.json').read_text())
assert audit['source_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
k=next(e['subcircuit_connectivity_map_key'] for e in j if e['type']=='source_net' and e['name']=='GND');cuts={};pruned=[]
for e in audit['connectivity']['unassigned_island_details']:
 if e['no_connect_pads'] or e['area_mm2']<1e-5:continue
 x0,y0,x1,y1=e['bounds_mm'];assert -8<x0<x1<8 and -17.5<y0<y1<-14 and e['area_mm2']<1
 for l in e['layers']:cuts.setdefault(l,[]).append(box(x0,y0,x1,y1).buffer(.01))
 pruned.append(e)
def ring(r):return {'vertices':[{'x':x,'y':y} for x,y in list(r.coords)[:-1]]}
out=[];delta=0
for e in j:
 if e['type']!='pcb_copper_pour' or e.get('subcircuit_connectivity_map_key')!=k or e['layer'] not in cuts:out.append(e);continue
 b=e['brep_shape'];coords=lambda r:[(p['x'],p['y'])for p in r['vertices']];p=Polygon(coords(b['outer_ring']),[coords(r)for r in b.get('inner_rings',[])]);q=p.difference(unary_union(cuts[e['layer']])).simplify(.00001,preserve_topology=True);delta+=p.area-q.area
 for i,piece in enumerate(q.geoms if hasattr(q,'geoms')else[q]):
  if piece.is_empty:continue
  out.append({**e,'pcb_copper_pour_id':e['pcb_copper_pour_id']+f'_pruned_{i}','brep_shape':{'outer_ring':ring(piece.exterior),'inner_rings':[ring(r)for r in piece.interiors]}})
assert 0<delta<10,delta
path.write_text(json.dumps(out,indent=2)+'\n');(root/'artifacts/validation/actual-cam-ground-prune.json').write_text(json.dumps({'isolated_actual_CAM_copper':pruned,'ground_only_removed_area_mm2':delta,'cut_guard_mm':.01,'method':'Motor-bay-only subtraction of bounding contours of finished CAM unassigned islands; pads and traces untouched. Re-export and independent connectivity/spacing audit required.','boardSha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2)+'\n');print(delta)
