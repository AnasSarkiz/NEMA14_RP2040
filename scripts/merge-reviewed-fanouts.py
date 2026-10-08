"""Independently verify proposed native-pad escapes against CURRENT copper before merge."""
import json,hashlib,sys
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
j=g.j;proposals=[json.loads((g.ROOT/('artifacts/'+name)).read_text()) for name in (sys.argv[1:] or ['rp-ground-fanout-proposal.json','rp-control-fanout-proposal.json'])];ids=set(x for p in proposals for x in p['removeTraceIds']);removed=[e for e in j if e['type']=='pcb_trace' and e['pcb_trace_id'] in ids];assert len(removed)==len(ids),ids
j=[e for e in j if e not in removed];adds=[e for p in proposals for e in p['additions']];assert not any(e.get(e['type']+'_id')==a.get(a['type']+'_id') for e in j for a in adds)
def pieces(e):
 t=e['type']
 if t in ['pcb_smtpad','pcb_plated_hole']:
  for l in e.get('layers',[e.get('layer','top')]):yield l,g.geometry(e)
 elif t=='pcb_via':
  for l in e['layers']:yield l,g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
 elif t=='pcb_trace':
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:yield a['layer'],g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
 elif t=='pcb_keepout':
  for l in e['layers']:yield l,g.keepout_geometry(e)
 elif t=='pcb_hole':
  for l in ['top','inner1','inner2','bottom']:yield l,g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1)
report=[]
for a in adds:
 gaps=[]
 for l,sh in pieces(a):
  for e in j+adds:
   if e is a or g.key(e)==g.key(a):continue
   for el,other in pieces(e):
    if el==l:gaps.append((sh.distance(other),e.get(e['type']+'_id'),l))
 minimum=min(gaps);assert minimum[0]>=.158-1e-6,(a,minimum);report.append({'id':a[a['type']+'_id'],'minimumForeignGap':minimum})
j+=adds;g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/('artifacts/fanout-merge-'+(sys.argv[1] if len(sys.argv)>1 else 'initial')+'-proof.json')).write_text(json.dumps({'proposals':proposals,'removedCurrentTraceRecords':removed,'nativeGeometryChanged':False,'minimumForeignClearanceMm':.158,'mergeChecks':report,'savedSHA256':hashlib.sha256(g.path.read_bytes()).hexdigest()},indent=2)+'\n');print('Merged',len(adds),'verified records and removed',len(removed),'explicit blockers')
