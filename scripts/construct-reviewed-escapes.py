"""Construct exact local escapes after independent pad/via/trace collision screening."""
import json,sys,math
from shapely.geometry import Point,LineString,box
import verify_supplier_connectivity as g
j=g.j;stack=['top','inner1','inner2','bottom'];nets={e['name']:e for e in j if e['type']=='source_net'};rows=[]
def add(ref,role,points,site,replace_near=None,width=.16):
 uid='reviewed_local_'+ref+'_'+role
 j[:]=[e for e in j if e.get(e['type']+'_id') not in [uid,uid+'_via']]
 p=next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role);key=g.sp[p['source_port_id']]['subcircuit_connectivity_map_key'];name=g.nets[key];wire=LineString([(p['x'],p['y'])]+points+[site]).buffer(width/2);via=Point(*site).buffer(.225);hole=Point(*site).buffer(.15);ripped=set();bad=[]
 for e in j:
  typ=e['type'];same=g.key(e)==key
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   if same:
    if typ=='pcb_smtpad' and hole.intersects(g.geometry(e)):bad.append(('hole-in-pad',e['pcb_smtpad_id']))
    continue
   if ('top' in e.get('layers',[e.get('layer','top')]) and wire.distance(g.geometry(e))<.153) or via.distance(g.geometry(e))<.153:bad.append((typ,e[typ+'_id']))
  elif typ=='pcb_via' and not same:
   s=Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
   if via.distance(s)<.153 or wire.distance(s)<.153:bad.append(('via',e['pcb_via_id']))
  elif typ=='pcb_trace' and not same:
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
     s=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
     if via.distance(s)<.153 or a['layer']=='top' and wire.distance(s)<.153:ripped.add(e['pcb_trace_id']);break
 if bad:raise RuntimeError('Illegal reviewed escape '+ref+':'+role+' '+str(bad))
 protected=[t for t in j if t.get('pcb_trace_id') in ripped and t['pcb_trace_id'].startswith(('usb_','oscillator_','reviewed_local_critical_'))]
 assert not protected, ('Reviewed escape conflicts with fixed critical copper', [t['pcb_trace_id'] for t in protected])
 j[:]=[e for e in j if e.get('pcb_trace_id') not in ripped]
 n=nets[name];source=next(e['source_trace_id'] for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==key and p['source_port_id'] in e.get('connected_source_port_ids',[]));attrs=dict(source_trace_id=source,source_net_id=n['source_net_id'],subcircuit_connectivity_map_key=key,subcircuit_id='subcircuit_source_group_0');uid='reviewed_local_'+ref+'_'+role
 if replace_near:
  v=next((v for v in j if v['type']=='pcb_via' and g.key(v)==key and math.dist((v['x'],v['y']),replace_near)<.12),None)
 else:v=None
 if v:v['x'],v['y']=site;v['outer_diameter'],v['hole_diameter']=.45,.3
 else:j.append(dict(type='pcb_via',pcb_via_id=uid+'_via',x=site[0],y=site[1],outer_diameter=.45,hole_diameter=.3,layers=stack,from_layer='top',to_layer='bottom',tented_on_top=True,tented_on_bottom=True,**attrs))
 pts=[(p['x'],p['y'])]+points+[site];route=[dict(route_type='wire',x=x,y=y,layer='top',width=width) for x,y in pts];route[0]['start_pcb_port_id']=p['pcb_port_id'];j.append(dict(type='pcb_trace',pcb_trace_id=uid,route=route,pcb_port_ids=[p['pcb_port_id']],**attrs));rows.append(dict(terminal=ref+':'+role,via_mm=site,removed_foreign_trace_records=sorted(ripped)))
# Caller supplies JSON so every proposed point is explicit and reviewable.
for row in json.load(open(sys.argv[1])):add(**row)
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/upright-revision/reviewed-local-escapes.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
