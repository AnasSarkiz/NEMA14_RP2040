"""Add same-net logical-center spokes wholly contained in actual SMT pad copper.
Native checks sometimes require a center contact even when a routed connection
already touches the native pad. No physical copper is added outside the pad.
"""
import json,hashlib
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import verify_supplier_connectivity as g
errors=json.loads((g.ROOT/'artifacts/drc-report.json').read_text())['errors'];add=[];rows=[]
for err in errors:
 if err['type']!='pcb_port_not_connected_error':continue
 for id in err['pcb_port_ids']:
  p=g.ports[id];pad=next(e for e in g.j if e['type']=='pcb_smtpad'and e['pcb_port_id']==id);key=g.key(pad);q=g.geometry(pad);segments=[]
  for e in g.j:
   if e['type']=='pcb_trace'and g.key(e)==key:
    for a,b in zip(e['route'],e['route'][1:]):
     if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']==pad['layer']:segments.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
  contact=q.buffer(-.08).intersection(unary_union(segments));assert not contact.is_empty,('Not a pad-center-only issue',err);t=contact.representative_point();pts=[(p['x'],p['y']),(t.x,t.y)];spoke=LineString(pts).buffer(.08);assert spoke.difference(q.buffer(.0000001)).area<1e-9,err
  st=next(e for e in g.j if e['type']=='source_trace'and p['source_port_id']in e['connected_source_port_ids']);ref=g.src[g.comp[p['pcb_component_id']]['source_component_id']];pin=g.sp[p['source_port_id']]['name'];tid='inside_native_pad_spoke_'+ref+'_'+pin;add.append({'type':'pcb_trace','pcb_trace_id':tid,'pcb_port_ids':[id],'source_trace_id':st['source_trace_id'],'source_net_id':st['connected_source_net_ids'][0],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0','route':[{'route_type':'wire','x':x,'y':y,'layer':pad['layer'],'width':.16}for x,y in pts]});rows.append({'reference':ref,'pin':pin,'points_mm':pts,'physical_Cu_added_outside_native_pad_mm2':0})
assert add
ids={e['pcb_trace_id']for e in add};g.path.write_text(json.dumps([e for e in g.j if e.get('pcb_trace_id')not in ids]+add,indent=2)+'\n');(g.ROOT/'artifacts/validation/service-native-pad-spokes.json').write_text(json.dumps({'rows':rows,'native_trace_center_representation_corrected':True},indent=2)+'\n');print(rows)
