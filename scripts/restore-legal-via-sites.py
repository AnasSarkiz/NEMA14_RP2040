"""Restore legal baseline via sites with the revised drill/pad sizes.

Same-net annular copper may join its own SMT land, but the drill must stay
outside every SMT pad except the three declared thermal sites. Foreign
clearances are measured from the full copper land on every plated layer.
"""
import json,copy,math
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
j=g.j;old=json.loads((g.ROOT/'artifacts/upright-revision/baseline-board.circuit.json').read_text());oldnames={e['subcircuit_connectivity_map_key']:e['name'] for e in old if e['type']=='source_net'};nets={e['name']:e for e in j if e['type']=='source_net'};stack=['top','inner1','inner2','bottom'];thermal=[]
for p in j:
 if p['type']=='pcb_smtpad' and p.get('width',0)>1 and p.get('height',0)>1 and g.src[g.comp[p['pcb_component_id']]['source_component_id']] in ['U_MCU','U_DRV','U_PD']:thermal.append((p['x'],p['y']))
static=[];owners=[]
for p in j:
 if p['type'] in ['pcb_smtpad','pcb_plated_hole']:static.append(g.geometry(p));owners.append(p)
 elif p['type']=='pcb_trace':
  for a,b in zip(p['route'],p['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:static.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2));owners.append(p)
tree=STRtree(static);rows=[]
for original in old:
 if original['type']!='pcb_via':continue
 n=oldnames[original['subcircuit_connectivity_map_key']]
 if n in ['USB_DP','USB_DM','MCU_DP','MCU_DM','XIN','XOUT','XTAL_OUT']:continue
 v=copy.deepcopy(original);v['outer_diameter']=max(.45,v['outer_diameter']);v['hole_diameter']=max(.3,v['hole_diameter']);net=nets[n];v['source_net_id']=net['source_net_id'];v['subcircuit_connectivity_map_key']=net['subcircuit_connectivity_map_key'];v['source_trace_id']=next(e['source_trace_id'] for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==net['subcircuit_connectivity_map_key']);key=g.key(v);shape=Point(v['x'],v['y']).buffer(v['outer_diameter']/2);hole=Point(v['x'],v['y']).buffer(v['hole_diameter']/2);bad=False
 for i in tree.query(shape.buffer(.153)):
  p=owners[i];same=g.key(p)==key
  if same:
   if p['type']=='pcb_smtpad' and hole.intersects(static[i]) and not(n=='GND' and any(math.dist((v['x'],v['y']),c)<.001 for c in thermal)):bad=True;break
  elif shape.distance(static[i])<.153:bad=True;break
 if not bad:
  for p in j:
   if p['type']=='pcb_via' and g.key(p)!=key and shape.distance(Point(p['x'],p['y']).buffer(p['outer_diameter']/2))<.153:bad=True;break
 if bad:continue
 current=next((q for q in j if q.get('pcb_via_id')==v['pcb_via_id']),None)
 if current and math.dist((current['x'],current['y']),(v['x'],v['y']))<1e-9:continue
 if current:j.remove(current)
 j.append(v);rows.append({'via':v['pcb_via_id'],'net':n,'restored_baseline_xy_mm':[v['x'],v['y']]})
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/upright-revision/restored-via-sites.json').write_text(json.dumps({'construction_not_qualification':True,'sites':rows},indent=2)+'\n');print('Restored',len(rows),'baseline via sites with .30 mm minimum drills and .45 mm minimum lands')
