"""Trim obsolete endpoint branches only when live physical-pad partitions remain identical."""
import json,math
from shapely.ops import unary_union
import verify_supplier_connectivity as g
errors=json.loads((g.ROOT/'artifacts/drc-report.json').read_text())['errors']
def signature(net):
 elems,roots=g.groups(net);out={}
 for e,r in zip(elems,roots):
  if e.get('pcb_port_id'):out.setdefault(r,set()).add(e['pcb_port_id'])
 return sorted(sorted(v) for v in out.values())
records=[]
for err in errors:
 if 'dangling endpoint' not in err.get('message',''):continue
 e=next((e for e in g.j if e.get('pcb_trace_id')==err['pcb_trace_id']),None)
 if e is None:continue
 isstart=err['pcb_trace_error_id'].endswith('_start');route=e['route']
 ordered=list(reversed(route)) if not isstart else list(route)
 if any(p['route_type']!='wire' or p['layer']!=ordered[0]['layer'] for p in ordered):continue
 net=g.key(e);layer=ordered[0]['layer'];geoms=[]
 for other in g.j:
  if other is e or g.key(other)!=net:continue
  if other['type'] in ['pcb_smtpad','pcb_plated_hole'] and layer in other.get('layers',[other.get('layer','top')]):geoms.append(g.geometry(other))
  # A dangling via must not anchor an obsolete branch.
  elif other['type']=='pcb_trace':
   for a,b in zip(other['route'],other['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']==layer:geoms.append(g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(min(a['width'],b['width'])/2))
 path=g.LineString([(p['x'],p['y']) for p in ordered]);hit=path.intersection(unary_union(geoms).buffer(-.015));
 if hit.is_empty:continue
 pieces=list(hit.geoms) if hasattr(hit,'geoms') else [hit]
 offsets=[path.project(g.Point(*p.coords[0])) for p in pieces if hasattr(p,'coords') and len(p.coords)]
 offsets += [path.project(g.Point(*p.coords[-1])) for p in pieces if hasattr(p,'coords') and len(p.coords)]
 if not offsets:continue
 offset=min(offsets)+.015
 if offset>=path.length-.01:continue
 pt=path.interpolate(offset);new=[dict(ordered[0],x=pt.x,y=pt.y)];new[0].pop('start_pcb_port_id',None);new[0].pop('end_pcb_port_id',None)
 dist=0
 for a,b in zip(ordered,ordered[1:]):
  dist+=math.hypot(b['x']-a['x'],b['y']-a['y'])
  if dist>offset+1e-8:new.append(b)
 candidate=new if isstart else list(reversed(new));before=signature(net);old=e['route'];e['route']=candidate
 if signature(net)!=before:e['route']=old;continue
 e['pcb_port_ids']=[p[k] for p in candidate for k in ['start_pcb_port_id','end_pcb_port_id'] if k in p]
 records.append({'trace_id':e['pcb_trace_id'],'endpoint':'start' if isstart else 'end','removed_length_mm':offset,'new_endpoint_mm':[pt.x,pt.y],'live_pad_connectivity_unchanged':True})
g.path.write_text(json.dumps(g.j,indent=2)+'\n');p=g.ROOT/'artifacts/same-side-trimmed-stubs.json';history=json.loads(p.read_text()) if p.exists() else [];history.extend(records);p.write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(records))
