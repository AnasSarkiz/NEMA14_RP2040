"""Vertical native-pad fanout; every added escape screened against actual foreign copper."""
import json,pathlib
import verify_supplier_connectivity as g
j=g.j;names={'J_PD','J_DATA'};records=[]
for e in j.copy():
 if e['type']!='pcb_smtpad' or g.src[g.comp[e['pcb_component_id']]['source_component_id']]not in names or not g.key(e):continue
 net=g.key(e);elems,roots=g.groups(net)
 if len({r for el,r in zip(elems,roots)if el.get('pcb_port_id')})<2:continue
 x,y=g.ports[e['pcb_port_id']]['x'],g.ports[e['pcb_port_id']]['y'];width=.16;geom=g.LineString([(x,y),(x,y-.9)]).buffer(width/2)
 conflicts=[]
 for o in j:
  if g.key(o)==net:continue
  if o['type']in['pcb_smtpad','pcb_plated_hole'] and 'top'in o.get('layers',[o.get('layer')]):shape=g.geometry(o)
  elif o['type']=='pcb_via':shape=g.Point(o['x'],o['y']).buffer(o['outer_diameter']/2)
  elif o['type']=='pcb_trace':
   shape=g.Polygon()
   for a,b in zip(o['route'],o['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='top':shape=shape.union(g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
  else:continue
  if geom.distance(shape)<.15-1e-6:conflicts.append(o.get(o['type']+'_id'))
 if conflicts:print('Not seeded',g.src[g.comp[e['pcb_component_id']]['source_component_id']],g.sp[g.ports[e['pcb_port_id']]['source_port_id']]['name'],conflicts);continue
 st=next(t for t in j if t['type']=='source_trace' and t.get('subcircuit_connectivity_map_key')==net)
 trace={'type':'pcb_trace','pcb_trace_id':'service_usb_native_escape_'+e['pcb_smtpad_id'],'source_trace_id':st['source_trace_id'],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[e['pcb_port_id']],'route':[{'route_type':'wire','x':x,'y':y,'width':width,'layer':'top','start_pcb_port_id':e['pcb_port_id']},{'route_type':'wire','x':x,'y':y-.9,'width':width,'layer':'top'}]}
 j.append(trace);records.append(trace)
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/validation/usb-native-escapes.json').write_text(json.dumps(records,indent=2)+'\n');print('Added',len(records),'screened vertical escapes')
