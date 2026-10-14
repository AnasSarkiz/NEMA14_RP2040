"""Reserve ordinary masked escapes from isolated physical lands; qualify afterward."""
import json,sys,math
from shapely.strtree import STRtree
from shapely.ops import unary_union
import verify_supplier_connectivity as g
stack=['top','inner1','inner2','bottom'];j=g.j
rows=[]
def index():
 a=[];o=[];ls=[]
 def add(e,p,l):a.append(p);o.append(e);ls.append(l)
 for e in j:
  if e['type'] in ['pcb_smtpad','pcb_plated_hole']:add(e,g.geometry(e),e.get('layers',[e.get('layer','top')]))
  elif e['type']=='pcb_via':add(e,g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2),stack)
  elif e['type']=='pcb_trace':
   for p,q in zip(e['route'],e['route'][1:]):
    if p['route_type']==q['route_type']=='wire' and p['layer']==q['layer']:add(e,g.LineString([(p['x'],p['y']),(q['x'],q['y'])]).buffer(max(p['width'],q['width'])/2),[p['layer']])
  elif e['type']=='pcb_hole':add(e,g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1),stack)
  elif e['type']=='pcb_keepout':c=e['center'];r=e['radius'];add(e,g.box(c['x']-r,c['y']-r,c['x']+r,c['y']+r),stack)
 return STRtree(a),a,o,ls
for spec in sys.argv[1:]:
 ref,role=spec.split(':');p=next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role);pad=next(e for e in j if e.get('pcb_port_id')==p['pcb_port_id'] and e['type']=='pcb_smtpad');net=g.key(pad);name=g.nets[net];w=.3 if name in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','V3V3','DATA_VBUS','LOGIC_IN','BUCK_SW'] else .55 if name=='PD_VBUS' else .16
 tree,shapes,owners,layers=index();best=None
 # Inward QFN escapes preserve the dense outer pin row and USB fanout.
 forced={}
 candidates=[forced[spec]] if spec in forced else [(round(p['x']+ix*.1,4),round(p['y']+iy*.1,4)) for ix in range(-40,41) for iy in range(-40,41) if .45<=math.hypot(ix*.1,iy*.1)<=4]
 for x,y in candidates:
  path_candidates=[[(p['x'],p['y']),(x,y)],[(p['x'],p['y']),(p['x'],y),(x,y)],[(p['x'],p['y']),(x,p['y']),(x,y)]]
  for points in path_candidates:
   wire=g.LineString(points).buffer(w/2);via=g.Point(x,y).buffer(.225);hits=set();bad=False
   policy=json.loads((g.ROOT/'artifacts/engineering-fixes/usb-routing-plan.json').read_text())
   if any(via.intersects(g.LineString(c['centerline']).buffer(.95)) for c in policy['cores']):continue
   if not g.box(-17.15,-17.15,17.15,17.15).covers(via):continue
   for geom,l in [(wire,pad['layer']),(via,None)]:
    for i in tree.query(geom.buffer(.153)):
     e=owners[i];typ=e['type'];same=g.key(e)==net
     if l is not None and l not in layers[i]:continue
     if same and l is not None:continue
     if same and typ=='pcb_trace':continue
     margin=.003 if same and typ in ['pcb_smtpad','pcb_plated_hole'] else .103 if same and typ=='pcb_via' else .153
     if geom.distance(shapes[i])>=margin:continue
     protected=typ=='pcb_trace' and (e['pcb_trace_id'].startswith(('usb_','review_escape_','oscillator_')) or g.nets.get(g.key(e)) in ['USB_DP','USB_DM','MCU_DP','MCU_DM','XIN','XOUT','XTAL_OUT'])
     if typ!='pcb_trace' or protected:bad=True;break
     hits.add(e['pcb_trace_id'])
    if bad:break
   if bad or len(hits)>5:continue
   cost=len(hits)*10+g.LineString(points).length+.05*(len(points)-2)
   if best is None or cost<best[0]:best=(cost,x,y,hits,points)
 if best is None:print('NO ESCAPE',spec,flush=True);continue
 _,x,y,hits,points=best;j[:]=[e for e in j if e.get('pcb_trace_id') not in hits]
 source=next(e['source_trace_id'] for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==net and p['source_port_id'] in e.get('connected_source_port_ids',[]));n=next(e for e in j if e['type']=='source_net' and e['subcircuit_connectivity_map_key']==net);base={'source_net_id':n['source_net_id'],'source_trace_id':source,'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0'};uid='review_escape_'+ref+'_'+role
 j.append({'type':'pcb_trace','pcb_trace_id':uid,'route':[{**{'route_type':'wire','x':a,'y':b,'width':w,'layer':pad['layer']},**({'start_pcb_port_id':p['pcb_port_id']} if i==0 else {})} for i,(a,b) in enumerate(points)],'pcb_port_ids':[p['pcb_port_id']],**base})
 j.append({'type':'pcb_via','pcb_via_id':uid+'_via','x':x,'y':y,'outer_diameter':.45,'hole_diameter':.3,'layers':stack,'from_layer':'top','to_layer':'bottom','tented_on_top':True,'tented_on_bottom':True,**base});row={'net':name,'port':spec,'via_mm':[x,y],'removed_foreign_trace_ids':sorted(hits)};rows.append(row);print(row,flush=True)
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/engineering-fixes/isolated-pad-escapes.json').write_text(json.dumps(rows,indent=2)+'\n')
