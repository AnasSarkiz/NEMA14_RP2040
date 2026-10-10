"""Independent physical pad-to-foreign-trace spacing audit supplementing native DRC."""
import json,hashlib
from shapely.geometry import LineString
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
errors=[];count=0;minimum=None
for layer in ['top','inner1','inner2','bottom']:
 pads=[e for e in g.j if e['type']in ['pcb_smtpad','pcb_plated_hole']and layer in e.get('layers',[e.get('layer','top')])];geos=[g.geometry(p)for p in pads];tree=STRtree(geos)
 for t in g.j:
  if t['type']!='pcb_trace':continue
  for a,b in zip(t['route'],t['route'][1:]):
   if a['route_type']!=b['route_type']or a['route_type']!='wire'or a['layer']!=b['layer']or a['layer']!=layer:continue
   count+=1;geo=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2,quad_segs=64)
   for i in tree.query(geo.buffer(.1501)):
    p=pads[i]
    if g.key(p)==g.key(t):continue
    d=geos[i].distance(geo);minimum=d if minimum is None else min(d,minimum)
    if d<.1499:
     port=g.ports.get(p.get('pcb_port_id'),{});ref=g.src[g.comp[p['pcb_component_id']]['source_component_id']]+'.'+g.sp.get(port.get('source_port_id'),{}).get('name','?');errors.append({'trace':t['pcb_trace_id'],'pad':ref,'layer':layer,'gapMm':d})
report={'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'status':'FAIL'if errors else'PASS','minimumRequiredMm':.15,'analyticRoundingAllowanceMm':.0001,'segmentsChecked':count,'nearbyForeignMinimumGapMm':minimum,'errors':errors,'scope':'Actual supplier polygon/pill/plated-pad copper versus saved trace strips on matching layers; does not replace actual CAM connectivity/drill/mask/paste tests.'}
(g.ROOT/'artifacts/validation/independent-native-pad-trace-clearance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'errors':errors,'segmentsChecked':count},indent=2));raise SystemExit(bool(errors))
