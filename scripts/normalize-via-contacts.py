"""Align route contact points within a real same-net via's copper land."""
import json,math
import verify_supplier_connectivity as g
changed=[]
for t in g.j:
 if t['type']!='pcb_trace':continue
 for i,v in enumerate(t['route']):
  if v['route_type']!='via':continue
  actual=next((e for e in g.j if e['type']=='pcb_via' and g.key(e)==g.key(t) and math.hypot(e['x']-v['x'],e['y']-v['y'])<1e-6),None)
  if actual is None:continue
  for idx in [i-1,i+1]:
   if not 0<=idx<len(t['route']):continue
   n=t['route'][idx]
   if n['route_type']!='wire':continue
   dist=math.hypot(n['x']-v['x'],n['y']-v['y'])
   if dist<1e-9:continue
   assert dist<=actual['outer_diameter']/2+n['width']/2,'Via contact lies outside actual copper land'
   changed.append({'trace':t['pcb_trace_id'],'old_wire_contact_mm':[n['x'],n['y']],'actual_via_mm':[v['x'],v['y']]});n['x'],n['y']=v['x'],v['y']
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/reference-feedback/via-contact-normalization.json').write_text(json.dumps(changed,indent=2)+'\n');print('Aligned',len(changed),'wire contacts to their actual plated via centres')
