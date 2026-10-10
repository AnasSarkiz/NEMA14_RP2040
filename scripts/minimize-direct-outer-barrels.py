"""Remove redundant PD fanout barrels only with a full-width direct TOP joint.
Each removal must preserve one native-pad island and anchor every remaining PD
trace/via. No trace or pad is moved or narrowed. Rebuild/export checks required.
"""
import json,math,hashlib
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import verify_supplier_connectivity as g
original=g.path.read_bytes();k=next(k for k,n in g.nets.items()if n=='PD_VBUS');rows=[]
for v in g.j.copy():
 if v['type']!='pcb_via'or g.key(v)!=k:continue
 escape=next((e for e in g.j if e['type']=='pcb_trace'and e.get('pcb_trace_id')==v.get('pcb_trace_id')and e['pcb_trace_id'].startswith(('inside_power_escape_','outer_usb_power_pin_escape_'))),None)
 if not escape:continue
 if any(e['type']=='pcb_trace'and any(p['route_type']=='via'and math.dist((p['x'],p['y']),(v['x'],v['y']))<1e-6 for p in e['route'])for e in g.j):continue
 end=escape['route'][-1]
 if math.dist((end['x'],end['y']),(v['x'],v['y']))>1e-6:continue
 main=unary_union([LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(min(a['width'],b['width'])/2)for e in g.j if e['type']=='pcb_trace'and g.key(e)==k and e is not escape for a,b in zip(e['route'],e['route'][1:])if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']=='top'and min(a['width'],b['width'])>=.45-1e-6])
 if not main.buffer(1e-7).covers(Point(v['x'],v['y']).buffer(end['width']/2)):continue
 old=g.j;g.j=[e for e in old if e is not v];es,rs=g.groups(k);anchors={r for e,r in zip(es,rs)if e.get('pcb_port_id')}
 valid=len(anchors)==1 and all(r in anchors for e,r in zip(es,rs)if e['type']in ['pcb_trace','pcb_via'])
 if not valid:g.j=old;continue
 rows.append({'removed_barrel':v,'native_pin_escape':escape['pcb_trace_id'],'full_native_escape_endcap_covered_by_top_main_0p45_Cu':True,'remaining_PD_native_pad_islands':1,'every_remaining_PD_trace_and_via_anchored':True})
assert g.path.read_bytes()==original
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/validation/service-direct-power-barrel-minimization.json').write_text(json.dumps({'source_before_sha256':hashlib.sha256(original).hexdigest(),'source_after_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'removed':rows,'method':'Remove only redundant native PD fanout barrels with a complete endcap contact to >=0.45mm TOP main copper, no layer-transition descriptor and unchanged one-island/all-remaining-trace native physical connectivity. No pad/trace widths or paths are changed. Native DRC and actual CAM/drill validation must pass again.'},indent=2)+'\n');print('Removed redundant PD fanout barrels',len(rows))
