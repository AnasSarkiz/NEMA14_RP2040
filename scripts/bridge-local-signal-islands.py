import sys,json,math
sys.path.insert(0,'scripts')
import verify_supplier_connectivity as g
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
requested=next(q.split('=',1)[1] for q in sys.argv if q.startswith('--net='));net=next(k for k,v in g.nets.items() if v==requested);stack=['top','inner1','inner2','bottom'];shapes=[];owners=[]
for e in g.j:
 typ=e['type']
 if typ in ['pcb_smtpad','pcb_plated_hole']:
  if 'inner1' in e.get('layers',[e.get('layer','top')]):shapes.append(g.geometry(e));owners.append(e)
 elif typ=='pcb_via':shapes.append(Point(e['x'],e['y']).buffer(e['outer_diameter']/2));owners.append(e)
 elif typ=='pcb_trace':
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='inner1':shapes.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2));owners.append(e)
 elif typ=='pcb_keepout':
  c=e['center'];r=e['radius'];shapes.append(box(c['x']-r,c['y']-r,c['x']+r,c['y']+r));owners.append(e)
 elif typ=='pcb_hole':shapes.append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1));owners.append(e)
tree=STRtree(shapes);es,rs=g.groups(net);lands={}
for e,r in zip(es,rs):
 if e.get('pcb_port_id'):lands.setdefault(r,[]).append(e)
best=None
for ra in lands:
 for rb in lands:
  if ra>=rb:continue
  va=[e for e,r in zip(es,rs) if r==ra and e['type']=='pcb_via'];vb=[e for e,r in zip(es,rs) if r==rb and e['type']=='pcb_via']
  for aa in va:
   for bb in vb:
    a=(aa['x'],aa['y']);b=(bb['x'],bb['y'])
    for pts in [[a,b],[a,(b[0],a[1]),b],[a,(a[0],b[1]),b]]:
     length=LineString(pts).length
     if length>15:continue
     geom=LineString(pts).buffer(.08);hits=set();bad=False
     if not box(-17.15,-17.15,17.15,17.15).covers(geom):continue
     for i in tree.query(geom.buffer(.153)):
      e=owners[i]
      if g.key(e)==net or geom.distance(shapes[i])>=.153:continue
      if e['type']!='pcb_trace' or e['pcb_trace_id'].startswith(('feedback_fanout_','usb_','review_escape_')) or g.nets.get(g.key(e)) in ['PD_VBUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','GND','LOGIC_IN','BUCK_SW','BUZZER_SINK']:bad=True;break
      hits.add(e['pcb_trace_id'])
     if bad or len(hits)>2:continue
     cost=len(hits)*100+length
     if best is None or cost<best[0]:best=(cost,aa,pts,hits)
if best is None:print('NO LOCAL BRIDGE');raise SystemExit(1)
_,via,pts,hits=best;print('LOCAL BRIDGE',pts,'RIP',sorted(hits),flush=True)
if '--apply' in sys.argv:
 g.j[:]=[e for e in g.j if e.get('pcb_trace_id') not in hits];uid='reviewed_local_signal_bridge_'+requested
 while any(e.get('pcb_trace_id')==uid for e in g.j):uid+='_next'
 base={k:via[k] for k in ['source_net_id','source_trace_id','subcircuit_connectivity_map_key','subcircuit_id'] if k in via}
 g.j.append({'type':'pcb_trace','pcb_trace_id':uid,'route':[{'route_type':'wire','x':x,'y':y,'layer':'inner1','width':.16} for x,y in pts],'pcb_port_ids':[],**base});g.path.write_text(json.dumps(g.j,indent=2)+'\n')
 out=g.ROOT/'artifacts/reference-feedback/local-power-bridges.json';history=json.loads(out.read_text()) if out.exists() else [];history.append({'trace':uid,'points_mm':pts,'removed_foreign_trace_ids':sorted(hits),'independent_physical_branch_cut_and_thermal_screen_required':True});out.write_text(json.dumps(history,indent=2)+'\n')
