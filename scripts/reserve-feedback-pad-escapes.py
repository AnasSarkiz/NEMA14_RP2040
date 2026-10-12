"""Reserve legal supplier-pad escapes, choosing the smallest conflicting copper set.
Native pads, protected escapes and exposed-pad vias are never modified.
All changes require fresh DRC, physical connectivity and CAM qualification.
"""
import sys,json,math
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
requested=set(sys.argv[1:]);board=next(e for e in g.j if e['type']=='pcb_board');stack=['top','inner1','inner2','bottom'] if board['num_layers']==4 else ['top','bottom'];targets=[]
for net,name in g.nets.items():
 if name not in requested:continue
 elems,roots=g.groups(net)
 for e,r in zip(elems,roots):
  if e['type']!='pcb_smtpad':continue
  if any(q['type']=='pcb_via' and rr==r for q,rr in zip(elems,roots)):continue
  targets.append(e)
receipts=[]
for pad in targets:
 if pad not in g.j:continue
 net=g.key(pad);p=g.ports[pad['pcb_port_id']];s=g.sp[p['source_port_id']];name=g.src[s['source_component_id']];c=g.comp[pad['pcb_component_id']]['center'];dx,dy=p['x']-c['x'],p['y']-c['y'];normal=(1 if dx>0 else -1,0) if abs(dx)>abs(dy) else (0,1 if dy>0 else -1)
 padlayer=pad.get('layer','top');netname=g.nets[net];width=.3 if netname in ['PD_VBUS','SENSE1','SENSE2','A_PLUS','A_MINUS','B_PLUS','B_MINUS'] else .16;diam=max(board['min_via_pad_diameter'],.5 if width==.3 else .4);hole=max(board['min_via_hole_diameter'],.25 if width==.3 else .2)
 shapes=[];owners=[];ls=[];protected=[]
 for e in g.j:
  typ=e['type'];items=[];protect=False
  if typ in ['pcb_smtpad','pcb_plated_hole']:items=[(l,g.geometry(e)) for l in e.get('layers',[e.get('layer','top')])];protect=True
  elif typ=='pcb_via':
   items=[('all',Point(e['x'],e['y']).buffer(e['outer_diameter']/2))]
   protect=(e.get('pcb_via_id','').startswith('feedback_fanout_') and any(q.get('pcb_trace_id')==e['pcb_via_id'].removesuffix('_via') for q in g.j)) or any(q['type']=='pcb_smtpad' and q.get('width',0)>1 and q.get('height',0)>1 and g.geometry(q).covers(Point(e['x'],e['y'])) for q in g.j)
  elif typ=='pcb_trace':
   items=[(a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']];protect=e.get('pcb_trace_id','').startswith('feedback_fanout_')
  elif typ=='pcb_keepout':
   cc=e['center'];rad=e['radius'];items=[('all',box(cc['x']-rad,cc['y']-rad,cc['x']+rad,cc['y']+rad))];protect=True
  elif typ=='pcb_hole':items=[('all',Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1))];protect=True
  for l,sh in items:shapes.append(sh);owners.append(e);ls.append(l);protected.append(protect)
 tree=STRtree(shapes);best=None
 def conflicts(test,via):
  hits=set()
  for idx in tree.query(test.buffer(.153)):
   e=owners[idx];typ=e['type'];same=g.key(e)==net
   if not via and (same or ls[idx] not in [padlayer,'all']):continue
   if via and same and typ not in ['pcb_smtpad','pcb_plated_hole','pcb_via']:continue
   margin=.003 if via and same else .153
   if test.distance(shapes[idx])>=margin:continue
   if protected[idx] or (via and same and typ=='pcb_via'):return None
   hits.add(e.get('pcb_trace_id',e.get('pcb_via_id')))
  return hits
 for nx,ny in [normal,(-normal[0],-normal[1]),(-normal[1],normal[0]),(normal[1],-normal[0])]:
  bounds=g.geometry(pad).bounds;extent=(bounds[2]-p['x']) if nx>0 else (p['x']-bounds[0]) if nx<0 else (bounds[3]-p['y']) if ny>0 else (p['y']-bounds[1]);lead=extent+width/2+.154;tip=(p['x']+nx*lead,p['y']+ny*lead)
  for length in [.65,.7,.725,.75,.9,1.1,1.3,1.4,1.5,1.8,2.1,2.4]:
   
   for lateral in [i*.05 for i in range(-20,21)]:
    x=round((p['x']+nx*length-ny*lateral)/.025)*.025;y=round((p['y']+ny*length+nx*lateral)/.025)*.025
    via=Point(x,y).buffer(diam/2)
    if not box(-17.15,-17.15,17.15,17.15).covers(via):continue
    b=conflicts(via,True)
    if b is None:continue
    origin=(p['x'],p['y']);end=(x,y);paths=[[origin,end]]
    if length>=lead:
     paths += [[origin,tip,end],[origin,tip,(x,tip[1]) if ny else (tip[0],y),end]]
    for points in paths:
     wire=LineString(points).buffer(width/2)
     if not box(-17.15,-17.15,17.15,17.15).covers(wire):continue
     a=conflicts(wire,False)
     if a is None:continue
     hit=a|b;cost=len(hit)*10+LineString(points).length+abs(lateral)*.1
     if best is None or cost<best[0]:best=(cost,x,y,points,hit)
 if best is None:print('NO PAD-CLEAR ESCAPE',name,s['name'],flush=True);continue
 _,x,y,pts,hits=best
 if len(hits)>12:print('HIGH RIPUP',name,s['name'],len(hits),flush=True);continue
 g.j[:]=[e for e in g.j if e.get('pcb_trace_id',e.get('pcb_via_id')) not in hits]
 sid=next(e['source_trace_id'] for e in g.j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==net and p['source_port_id'] in e.get('connected_source_port_ids',[]));sn=next((e['source_net_id'] for e in g.j if e['type']=='source_net' and e['subcircuit_connectivity_map_key']==net),None);uid='feedback_fanout_'+pad['pcb_port_id']
 while any(e.get('pcb_trace_id')==uid for e in g.j):uid+='_next'
 base={'source_trace_id':sid,'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0',**({'source_net_id':sn} if sn else {})};route=[{'route_type':'wire','x':a,'y':b,'layer':padlayer,'width':width} for a,b in pts];route[0]['start_pcb_port_id']=pad['pcb_port_id'];g.j.append({'type':'pcb_trace','pcb_trace_id':uid,'route':route,'pcb_port_ids':[pad['pcb_port_id']],**base});g.j.append({'type':'pcb_via','pcb_via_id':uid+'_via','x':x,'y':y,'outer_diameter':diam,'hole_diameter':hole,'layers':stack,'from_layer':'top','to_layer':'bottom','tented_on_top':True,'tented_on_bottom':True,**base});rec={'component':name,'pin':s['name'],'net':netname,'via_xy_mm':[x,y],'removed_conflicting_copper':sorted(hits)};receipts.append(rec);print(rec,flush=True)
 g.path.write_text(json.dumps(g.j,indent=2)+'\n')
out=g.ROOT/'artifacts/reference-feedback/controlled-pad-escapes.json';hist=json.loads(out.read_text()) if out.exists() else [];hist.extend(receipts);out.write_text(json.dumps(hist,indent=2)+'\n')
