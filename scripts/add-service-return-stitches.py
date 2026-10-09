"""Add reviewed GND return stitches near the revised USB/QSPI layer transitions."""
import json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import verify_supplier_connectivity as g
from shapely.geometry import Point,Polygon,LineString
from shapely.ops import unary_union
j=g.j;ground=next(e for e in j if e['type']=='source_net'and e['name']=='GND');key=ground['subcircuit_connectivity_map_key'];base=next(e for e in j if e['type']=='pcb_via'and e.get('source_net_id')==ground['source_net_id']);checks=[]
for ident,x,y,sx,sy in [('service_usb_return_stitch',6.625,12.5,6.875,11.45),('service_qspi_return_stitch',-1,9.425,-1,8.325)]:
 if any(e.get('pcb_via_id')==ident for e in j):continue
 pt=Point(x,y);foreign=[]
 for e in j:
  if e['type'] in ['pcb_smtpad','pcb_plated_hole','pcb_via']and g.key(e)!=key:foreign.append(g.geometry(e))
  if e['type']=='pcb_trace'and g.key(e)!=key:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']:foreign.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
 clearance=pt.distance(unary_union(foreign))-.25;assert clearance>.20,clearance
 assert all(pt.distance(g.geometry(e))>.25 for e in j if e['type']=='pcb_smtpad')
 for e in j:
  if e['type']=='pcb_keepout':assert pt.distance(g.keepout_geometry(e))>.25
 pours=[]
 for e in j:
  if e['type']=='pcb_copper_pour'and e['layer']=='inner1'and g.key(e)==key:
   b=e['brep_shape'];coords=lambda r:[(p['x'],p['y'])for p in r['vertices']];pours.append(Polygon(coords(b['outer_ring']),[coords(r)for r in b.get('inner_rings',[])]))
 assert pt.distance(unary_union(pours))==0,'stitch must contact the existing GND reference'
 j.append({**base,'pcb_via_id':ident,'x':x,'y':y,'hole_diameter':.25,'outer_diameter':.5})
 checks.append({'via_id':ident,'xy_mm':[x,y],'nearest_foreign_copper_clearance_mm':clearance,'signal_transition_xy_mm':[sx,sy],'transition_to_return_stitch_mm':pt.distance(Point(sx,sy))})
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/validation/service-return-stitches.json').write_text(json.dumps({'checks':checks,'current_source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'scope':'Native geometry placement screen; actual CAM, paste, connectivity and DRC required after export.'},indent=2)+'\n');print(checks)
