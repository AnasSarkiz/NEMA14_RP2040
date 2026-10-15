"""Explicit short, top-only A4988 charge-pump loop on the actual RP2040 lands."""
import json
from shapely.geometry import LineString,Point
import verify_supplier_connectivity as g
j=g.j;names={e['name']:e for e in j if e['type']=='source_net'};keys={names[n]['subcircuit_connectivity_map_key'] for n in ['CP1','CP2']}
def port(ref,role):return next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role)
j[:]=[e for e in j if not (e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour'] and (e['type']=='pcb_copper_pour' or g.key(e) in keys))]
rows=[];new=[];removed=set()
for name,role in [('CP1','pin1'),('CP2','pin2')]:
 p,q=port('U_DRV',name),port('C_CP',role)
 points=[(p['x'],p['y']),(0.3,p['y']),(0,-11.775),(q['x'],-11.775),(q['x'],q['y'])] if name=='CP1' else [(p['x'],p['y']),(q['x'],p['y']),(q['x'],q['y'])]
 shape=LineString(points).buffer(.08);key=names[name]['subcircuit_connectivity_map_key']
 for e in j:
  if g.key(e)==key:continue
  if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and 'top' in e.get('layers',[e.get('layer','top')]):assert shape.distance(g.geometry(e))>=.15-1e-6,(name,e[e['type']+'_id'],shape.distance(g.geometry(e)))
  if e['type']=='pcb_via':
   if shape.distance(Point(e['x'],e['y']).buffer(e['outer_diameter']/2))<.153:removed.add(e['pcb_via_id'])
  if e['type']=='pcb_trace' and any(a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='top' and shape.distance(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))<.153 for a,b in zip(e['route'],e['route'][1:])):removed.add(e['pcb_trace_id'])
 source=next(e['source_trace_id'] for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==key and p['source_port_id'] in e['connected_source_port_ids']);rr=[dict(route_type='wire',x=x,y=y,width=.16,layer='top') for x,y in points];rr[0]['start_pcb_port_id']=p['pcb_port_id'];rr[-1]['end_pcb_port_id']=q['pcb_port_id'];new.append(dict(type='pcb_trace',pcb_trace_id='reviewed_local_critical_'+name,route=rr,pcb_port_ids=[p['pcb_port_id'],q['pcb_port_id']],source_net_id=names[name]['source_net_id'],source_trace_id=source,subcircuit_connectivity_map_key=key,subcircuit_id='subcircuit_source_group_0'));rows.append(dict(net=name,length_mm=LineString(points).length,layers=['top'],signal_vias=0,points=points))
for e in j:
 id=e.get(e['type']+'_id','')
 if id in removed:assert not id.startswith(('usb_','oscillator_','thermal_via_','reviewed_local_critical_')),('Protected copper collision',id)
j[:]=[e for e in j if e.get(e['type']+'_id') not in removed];j.extend(new);g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/opposite-edge/charge-pump-plan.json').write_text(json.dumps({'constructed_requires_full_verification':True,'routes':rows,'displaced_copper':sorted(removed)},indent=2)+'\n');print(rows,'Removed',sorted(removed))
