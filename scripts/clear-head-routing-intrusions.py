"""Rip only saved traces that violate exact circular all-layer hardware clearance."""
import json
import verify_supplier_connectivity as g
circles=[e for e in g.j if e['type']=='pcb_keepout'];removed=[]
for e in g.j:
 if e['type']!='pcb_trace':continue
 hits=[]
 for a,b in zip(e['route'],e['route'][1:]):
  if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
  sh=g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
  for c in circles:
   if a['layer'] in c['layers'] and sh.distance(g.keepout_geometry(c))<.1505:hits.append({'layer':a['layer'],'keepout':c['pcb_keepout_id'],'gapMm':sh.distance(g.keepout_geometry(c))})
 if hits:removed.append({'record':e,'intrusions':hits})
for v in [e for e in g.j if e['type']=='pcb_via']:
 for c in circles:
  if set(v['layers'])&set(c['layers']):assert g.Point(v['x'],v['y']).buffer(v['outer_diameter']/2).distance(g.keepout_geometry(c))>=.15,(v,c)
g.j[:]=[e for e in g.j if not any(e is row['record'] for row in removed)];g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/head-routing-corrections.json').write_text(json.dumps({'recordsRemoved':removed,'keepoutShapes':'Unchanged exact Ø5.4 circle on all four copper layers','minimumCopperClearanceMm':.15},indent=2)+'\n');print('Ripped',len(removed),'hardware-clearance violating records')
