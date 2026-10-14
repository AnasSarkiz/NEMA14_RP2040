"""Reserve short inner1 signal escapes; refill and verify all ground regions afterward."""
import json,sys,math
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
requested={q for q in sys.argv[1:] if not q.startswith('--')};requested_ref=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--start-ref=')),None);reachable_path=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--reachable-sites=')),None);reachable=__import__('numpy').load(reachable_path) if reachable_path else None;construction_layer=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--layer=')),'inner1');assert construction_layer in ['inner1','inner2'];requested_width=float(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--width=')),.16));assert .16<=requested_width<=.3;via_radius=.25 if requested_width>=.3 else .225;stack=['top','inner1','inner2','bottom'];board=next(e for e in g.j if e['type']=='pcb_board');assert board['num_layers']==4
receipts=[]
def build_index():
 shapes=[];owners=[];physical_layers=[]
 def add(e,geom,ls):shapes.append(geom);owners.append(e);physical_layers.append(ls)
 for e in g.j:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole']:add(e,g.geometry(e),e.get('layers',[e.get('layer','top')]))
  elif typ=='pcb_via':add(e,Point(e['x'],e['y']).buffer(e['outer_diameter']/2),stack)
  elif typ=='pcb_trace':
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:add(e,LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2),[a['layer']])
  elif typ=='pcb_keepout':
   c=e['center'];r=e['radius'];add(e,box(c['x']-r,c['y']-r,c['x']+r,c['y']+r),stack)
  elif typ=='pcb_hole':add(e,Point(e['x'],e['y']).buffer(e['hole_diameter']/2),stack)
 return STRtree(shapes),shapes,owners,physical_layers
tree,shapes,owners,physical_layers=build_index()
def clear(poly,layer,net,via=False):
 if not box(-17.15,-17.15,17.15,17.15).covers(poly):return False
 if g.nets.get(net)!='GND':
  plan=json.loads((g.ROOT/'artifacts/engineering-fixes/usb-routing-plan.json').read_text())
  for core in plan['cores']:
   if via or layer==core['reference_layer']:
    for track in core['tracks']:
     if poly.distance(LineString(track['points']).buffer(.125))<.203:return False

 for i in tree.query(poly.buffer(.253)):
  e=owners[i];typ=e['type'];same=g.key(e)==net
  if not via and layer not in physical_layers[i]:continue
  if same and not via:continue
  if typ=='pcb_copper_pour':continue
  if via and same and typ=='pcb_trace':continue
  margin=.003 if via and same and typ in ['pcb_smtpad','pcb_plated_hole'] else .103 if via and same and typ=='pcb_via' else .25 if typ=='pcb_hole' else .153
  if poly.distance(shapes[i])<margin:return False
 return True
for net,name in g.nets.items():
 if name not in requested:continue
 width=requested_width  # Independent physical branch-cut/current screening remains mandatory.
 assert construction_layer=='inner2' or (name in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS'] and width>=.3) or name not in ['GND','PD_VBUS','LOGIC_IN','DATA_VBUS','BUCK_SW','BUZZER_SINK','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2'],'Local inner1 escapes are restricted to low-current signals'
 es,rs=g.groups(net);lands={}
 for e,r in zip(es,rs):
  if e.get('pcb_port_id'):lands.setdefault(r,[]).append(e)
 if len(lands)<2:continue
 phase=name in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS']
 existing_inner=sum(math.dist((a['x'],a['y']),(b['x'],b['y'])) for t in g.j if t['type']=='pcb_trace' and g.key(t)==net for a,b in zip(t['route'],t['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='inner1')
 remaining_inner=8-existing_inner if phase and construction_layer=='inner1' else float('inf')
 direct=None
 for ra in lands:
  for rb in lands:
   if ra==rb:continue
   va=[e for e,r in zip(es,rs) if r==ra and e['type']=='pcb_via'];vb=[e for e,r in zip(es,rs) if r==rb and e['type']=='pcb_via']
   for aa in va:
    for bb in vb:
     a=(aa['x'],aa['y']);b=(bb['x'],bb['y'])
     for pts in [[a,b],[a,(b[0],a[1]),b],[a,(a[0],b[1]),b]]:
      length=LineString(pts).length
      if length<=min(15,remaining_inner) and clear(LineString(pts).buffer(width/2),construction_layer,net) and (direct is None or length<direct[0]):direct=(length,aa,pts)
 if direct:
  length,v,pts=direct;uid='inner1_local_escape_'+name+'_direct'
  while any(e.get('pcb_trace_id')==uid for e in g.j):uid+='_next'
  base={k:v[k] for k in ['source_net_id','source_trace_id','subcircuit_connectivity_map_key','subcircuit_id'] if k in v}
  g.j.append({'type':'pcb_trace','pcb_trace_id':uid,'route':[{'route_type':'wire','x':a,'y':b,'layer':construction_layer,'width':width} for a,b in pts],'pcb_port_ids':[],**base});rec={'net':name,'start_mm':pts[0],'end_mm':pts[-1],'length_mm':length,'connects_existing_actual_via_barrels':True};receipts.append(rec);print(rec,flush=True);tree,shapes,owners,physical_layers=build_index();continue
 phase=name in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS']
 existing_inner=sum(math.dist((a['x'],a['y']),(b['x'],b['y'])) for t in g.j if t['type']=='pcb_trace' and g.key(t)==net for a,b in zip(t['route'],t['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='inner1')
 remaining_inner=8-existing_inner if phase and construction_layer=='inner1' else float('inf')
 for root in sorted(lands,key=lambda r:len(lands[r])):
  if requested_ref and not any(g.src[g.sp[g.ports[p['pcb_port_id']]['source_port_id']]['source_component_id']]==requested_ref for p in lands[root]):continue
  vs=[e for e,r in zip(es,rs) if r==root and e['type']=='pcb_via'];found=None
  for v in vs:
   origin=(v['x'],v['y']);candidates=[]
   for ix in range(-40,41):
    for iy in range(-40,41):
     dist=math.hypot(ix*.1,iy*.1)
     if .7<=dist<=(4 if phase else 2.5):candidates.append((dist,round(origin[0]+ix*.1,3),round(origin[1]+iy*.1,3)))
   for _,x,y in sorted(candidates):
    if reachable is not None and not reachable[round((y+17.5)/.025),round((x+17.5)/.025)]:continue
    via=Point(x,y).buffer(via_radius)
    if not clear(via,None,net,True):continue
    paths=[[origin,(x,y)],[origin,(x,origin[1]),(x,y)],[origin,(origin[0],y),(x,y)]]
    for pts in paths:
     if LineString(pts).length>min(4 if phase else 3,remaining_inner):continue
     if clear(LineString(pts).buffer(width/2),construction_layer,net):found=(v,x,y,pts);break
    if found:break
   if found:break
  if not found:continue
  v,x,y,pts=found;uid='inner1_local_escape_'+name+'_'+str(len(receipts))
  while any(e.get('pcb_trace_id')==uid for e in g.j):uid+='_next'
  base={k:v[k] for k in ['source_net_id','source_trace_id','subcircuit_connectivity_map_key','subcircuit_id'] if k in v}
  g.j.append({'type':'pcb_trace','pcb_trace_id':uid,'route':[{'route_type':'wire','x':a,'y':b,'layer':construction_layer,'width':width} for a,b in pts],'pcb_port_ids':[],**base})
  g.j.append({'type':'pcb_via','pcb_via_id':uid+'_via','x':x,'y':y,'outer_diameter':via_radius*2,'hole_diameter':.3,'layers':stack,'from_layer':'top','to_layer':'bottom','tented_on_top':True,'tented_on_bottom':True,**base})
  rec={'net':name,'start_mm':pts[0],'end_mm':[x,y],'length_mm':LineString(pts).length,'ground_plane_requires_refill_and_connectivity_verification':True};receipts.append(rec);print(rec,flush=True)
  tree,shapes,owners,physical_layers=build_index()
  break
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/reference-feedback/local-inner1-escapes.json').write_text(json.dumps(receipts,indent=2)+'\n')
