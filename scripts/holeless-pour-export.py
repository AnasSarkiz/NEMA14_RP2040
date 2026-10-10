"""Split ground polygons along hole interiors to avoid global LPC erasure in CLI CAM.
Union is verified before/after; no copper is added or removed intentionally.
"""
import json,pathlib,hashlib
from shapely.geometry import Polygon,LineString
from shapely.ops import split,unary_union
from shapely import set_precision
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json';j=json.loads(path.read_text());out=[];proof=[]
def ring(r):return {'vertices':[{'x':float(x),'y':float(y)}for x,y in list(r.coords)[:-1]]}
for e in j:
 if e['type']!='pcb_copper_pour':out.append(e);continue
 b=e['brep_shape'];coords=lambda r:[(p['x'],p['y'])for p in r['vertices']];original=Polygon(coords(b['outer_ring']),[coords(r)for r in b.get('inner_rings',[])])
 queue=[set_precision(original,.000001)];parts=[]
 while queue:
  p=queue.pop()
  if p.is_empty:continue
  if p.geom_type=='MultiPolygon':queue.extend(p.geoms);continue
  assert p.geom_type=='Polygon',p.geom_type
  if not p.interiors:parts.append(p);continue
  y=Polygon(p.interiors[0]).representative_point().y
  ps=list(split(p,LineString([(-100,y),(100,y)])).geoms)
  assert len(ps)>1
  queue.extend(ps)
 merged=unary_union(parts);error=original.symmetric_difference(merged).area
 assert error<.0001,(e['pcb_copper_pour_id'],error)
 for i,p in enumerate(parts):out.append({**e,'pcb_copper_pour_id':e['pcb_copper_pour_id']+f'_simple_{i}','brep_shape':{'outer_ring':ring(p.exterior),'inner_rings':[]}})
 proof.append({'pour':e['pcb_copper_pour_id'],'parts':len(parts),'union_delta_mm2':error})
path.write_text(json.dumps(out,indent=2)+'\n');(root/'artifacts/validation/holeless-pour-export.json').write_text(json.dumps({'reason':'Official CLI LPC hole regions erase previously emitted foreign copper. Split contours contain no holes; exact union verified.','rounding_grid_mm':.000001,'pours':proof,'boardSha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2)+'\n');print('pours',len(proof),'pieces',sum(p['parts']for p in proof))
