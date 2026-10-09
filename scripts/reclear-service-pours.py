"""Re-clear retained power pours against revised upper-bay pads and routing.
No power-net reassignment; cuts restricted to changed +Y bay and explicitly widened inner2 power fragment.
"""
import verify_supplier_connectivity as g
import json,hashlib
from shapely.geometry import Polygon,box,Point,LineString
from shapely.ops import unary_union
j=g.j;bay=box(-17.2,7.2,17.2,17.2).union(box(-12,-9.5,-10,-7.5));out=[];proof=[]
def ring(r):return {'vertices':[{'x':x,'y':y}for x,y in list(r.coords)[:-1]]}
for e in j:
 if e['type']!='pcb_copper_pour':out.append(e);continue
 key=g.key(e);layer=e['layer'];b=e['brep_shape'];coords=lambda r:[(p['x'],p['y'])for p in r['vertices']];original=Polygon(coords(b['outer_ring']),[coords(r)for r in b.get('inner_rings',[])]);cuts=[]
 for p in j:
  t=p['type'];foreign=g.key(p)!=key
  if t in ['pcb_smtpad','pcb_plated_hole'] and foreign and layer in p.get('layers',[p.get('layer')]):cuts.append(g.geometry(p).buffer(.20,quad_segs=32))
  elif t=='pcb_via' and foreign and layer in p['layers']:cuts.append(Point(p['x'],p['y']).buffer(p['outer_diameter']/2+.20,quad_segs=32))
  elif t=='pcb_trace' and foreign:
   for a,b in zip(p['route'],p['route'][1:]):
    if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']==layer:cuts.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2+.2,quad_segs=32))
  elif t=='pcb_keepout':c=p['center'];cuts.append(Point(c['x'],c['y']).buffer(p['radius'],quad_segs=64))
 q=original.difference(unary_union(cuts).intersection(bay)).simplify(.00001,preserve_topology=True)
 proof.append({'pour':e['pcb_copper_pour_id'],'net':g.nets.get(key),'layer':layer,'removed_mm2':original.area-q.area})
 for i,p in enumerate(q.geoms if hasattr(q,'geoms')else[q]):
  if p.is_empty:continue
  out.append({**e,'pcb_copper_pour_id':e['pcb_copper_pour_id']+f'_usbclear_{i}','brep_shape':{'outer_ring':ring(p.exterior),'inner_rings':[ring(r)for r in p.interiors]}})
g.path.write_text(json.dumps(out,indent=2)+'\n');(g.ROOT/'artifacts/validation/usb-retained-pour-clearance.json').write_text(json.dumps({'changedBay_mm':list(bay.bounds),'cut_clearance_mm':.2,'pours':proof},indent=2)+'\n');print(proof)
