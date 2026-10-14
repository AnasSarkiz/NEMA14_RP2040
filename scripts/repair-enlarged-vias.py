"""Relocate enlarged vias only into independently clear nearby positions.

Unrepairable old vias and conflicting trace legs are removed for physical
rerouting. This is construction, never a qualification result.
"""
import json,math
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
j=g.j;stack=['top','inner1','inner2','bottom'];src=g.src;rows=[]
def objects():
 shapes=[];owners=[];ls=[]
 for e in j:
  if e['type'] in ['pcb_smtpad','pcb_plated_hole']:shapes.append(g.geometry(e));owners.append(e);ls.append(set(e.get('layers',[e.get('layer','top')])))
  elif e['type']=='pcb_via':shapes.append(Point(e['x'],e['y']).buffer(e['outer_diameter']/2));owners.append(e);ls.append(set(stack))
  elif e['type']=='pcb_trace':
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
     shapes.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2));owners.append(e);ls.append({a['layer']})
  elif e['type']=='pcb_hole':shapes.append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.2));owners.append(e);ls.append(set(stack))
  elif e['type']=='pcb_keepout':c=e['center'];r=e['radius'];shapes.append(box(c['x']-r,c['y']-r,c['x']+r,c['y']+r));owners.append(e);ls.append(set(stack))
 return shapes,owners,ls,STRtree(shapes)
thermal=[]
for p in j:
 if p['type']=='pcb_smtpad' and p.get('width',0)>1 and p.get('height',0)>1:
  name=src[g.comp[p['pcb_component_id']]['source_component_id']]
  if name in ['U_MCU','U_DRV','U_PD']:thermal.append((p['x'],p['y']))
cached=None
for v in list(j):
 if v['type']!='pcb_via' or v.get('pcb_via_id','').startswith(('usb_','oscillator_')):continue
 if g.nets[g.key(v)]=='GND' and any(math.dist((v['x'],v['y']),p)<.001 for p in thermal):continue
 if cached is None:cached=objects()
 shapes,owners,ls,tree=cached;key=g.key(v);old=(v['x'],v['y'])
 def clear(x,y):
  shape=Point(x,y).buffer(v['outer_diameter']/2)
  if not box(-17.15,-17.15,17.15,17.15).covers(shape):return False
  for i in tree.query(shape.buffer(.153)):
   e=owners[i]
   if e is v:continue
   same=g.key(e)==key
   if same and e['type'] in ['pcb_trace','pcb_via']:continue
   margin=.015 if same and e['type'] in ['pcb_smtpad','pcb_plated_hole'] else .153
   if shape.distance(shapes[i])<margin:return False
  return True
 if clear(*old):continue
 candidate=None
 for ix,iy in sorted([(a,b) for a in range(-6,7) for b in range(-6,7) if a or b],key=lambda q:math.hypot(*q)):
  x,y=old[0]+ix*.025,old[1]+iy*.025
  if clear(x,y):candidate=(x,y);break
 cached=None
 if candidate:
  v['x'],v['y']=candidate;rows.append({'via':v['pcb_via_id'],'old_mm':old,'new_mm':candidate,'requires_physical_contact_verification':True})
 else:j.remove(v);rows.append({'removed_via_for_rerouting':v['pcb_via_id'],'net':g.nets[key]})
# Cut only foreign-clearance violations; preserve the remaining pad escapes and route legs.
shapes,owners,ls,tree=objects();out=[];cut=[]
for e in j:
 if e['type']!='pcb_trace' or e['pcb_trace_id'].startswith(('usb_','oscillator_')):out.append(e);continue
 run=[];runs=[]
 for a,b in zip(e['route'],e['route'][1:]):
  if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:raise RuntimeError('Split multilayer records before this construction step')
  shape=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2);bad=False
  for i in tree.query(shape.buffer(.150001)):
   q=owners[i]
   if q['type']!='pcb_via' or g.key(q)==g.key(e):continue
   if shape.distance(shapes[i])<.150001:bad=True;break
  if bad:
   if len(run)>=2:runs.append(run)
   run=[];cut.append(e['pcb_trace_id']);continue
  if not run:run=[a,b]
  elif run[-1]==a:run.append(b)
  else:runs.append(run);run=[a,b]
 if len(run)>=2:runs.append(run)
 for k,route in enumerate(runs):
  ports=sorted({p[tag] for p in route for tag in ['start_pcb_port_id','end_pcb_port_id'] if tag in p});out.append({**e,'pcb_trace_id':e['pcb_trace_id']+'_via_clearance_run_'+str(k),'route':route,'pcb_port_ids':ports})
g.path.write_text(json.dumps(out,indent=2)+'\n');(g.ROOT/'artifacts/upright-revision/via-reconstruction.json').write_text(json.dumps({'construction_not_qualification':True,'via_changes':rows,'trace_records_with_cut_legs':sorted(set(cut))},indent=2)+'\n');print('Relocated/removed',len(rows),'vias; cut legs in',len(set(cut)),'trace records')
