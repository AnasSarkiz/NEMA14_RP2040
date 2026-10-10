import sys,json;sys.path.insert(0,'scripts');import verify_supplier_connectivity as g
from shapely.geometry import LineString,Point
links=[('DIR','inner2',.16,[(1.1,-.55),(1.5,-.95),(1.5,-3.3),(1.2,-3.6),(1.2,-4.6),(2,-5.4),(2,-7),(2.57,-7.57),(2.57,-8.349493)]),('V1V1','inner2',.16,[(6.179884,-5.5),(8.6,-5.5),(8.6,3.1165),(8.8281,3.3446)])]
findings=[]
for n,l,w,pts in links:
 z=LineString(pts).buffer(w/2);print('\nLINK',n)
 for e in g.j:
  typ=e['type'];net=g.nets.get(g.key(e));geo=None
  if net==n:continue
  if typ=='pcb_via':geo=Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
  elif typ in ['pcb_smtpad','pcb_plated_hole']and l in e.get('layers',[e.get('layer','top')]):geo=g.geometry(e)
  elif typ=='pcb_trace':
   from shapely.ops import unary_union
   parts=[LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)for a,b in zip(e['route'],e['route'][1:])if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']==l]
   if parts:geo=unary_union(parts)
  if geo is not None and z.distance(geo)<.1499:findings.append({'link':n,'type':typ,'id':e.get(typ+'_id'),'net':net,'gap':z.distance(geo)})

allowed={'diagnostics_85ca7134_trace_390_new_0','diagnostics_f01e5913_trace_109_new_0'}
assert all(f['type']=='pcb_trace'and f['id']in allowed for f in findings),findings
removed=[e for e in g.j if e.get('pcb_trace_id')in allowed];assert len(removed)==2
g.j[:]=[e for e in g.j if e not in removed and e['type']!='pcb_copper_pour']
for n,l,w,pts in links:
 net=next(e for e in g.j if e['type']=='source_net'and e['name']==n)
 g.j.append({'type':'pcb_trace','pcb_trace_id':'diagnostics_manual_link_'+n,'route':[{'route_type':'wire','x':x,'y':y,'width':w,'layer':l}for x,y in pts],'source_net_id':net['source_net_id'],'subcircuit_connectivity_map_key':net['subcircuit_connectivity_map_key'],'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[]})
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/diagnostics/manual-links.json').write_text(json.dumps({'coordinates':links,'conflicts':findings,'removedForOfficialReroute':removed,'physicalConnectivityRequired':True},indent=2)+'\n');print('Applied explicit links; reroute two obstructing signal records with official router')
