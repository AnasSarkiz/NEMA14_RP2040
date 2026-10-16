"""Construct bounded inner1 motor transitions against actual native copper.
All removed ordinary neighbours require physical rerouting and independent gates.
"""
import json,sys,math,hashlib
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union
import verify_supplier_connectivity as g
rows=json.load(open(sys.argv[1]));j=g.j;history=[];stack=['top','inner1','inner2','bottom'];policy=json.loads((g.ROOT/'src/layer-routing-policy.json').read_text());fixed=('usb_','oscillator_','reviewed_local_critical_');power={'GND','PD_VBUS','DATA_VBUS','LOGIC_IN','V3V3','V1V1','VREG','VREF','VCP','BUCK_SW','BUCK_BST','CP1','CP2','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2'}
usb=json.loads((g.ROOT/'artifacts/engineering-fixes/usb-routing-plan.json').read_text())
osc=json.loads((g.ROOT/'artifacts/upright-revision/oscillator-plan.json').read_text());osc_region=unary_union([LineString(r['points']).buffer(osc['guard_buffer_mm']) for r in osc['routes']])
def inner_length(t):return sum(math.dist((a['x'],a['y']),(b['x'],b['y'])) for a,b in zip(t['route'],t['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='inner1')
for row in rows:
 name=row['net'];key=next(k for k,v in g.nets.items() if v==name);assert name in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS']
 start=next(e for e in j if e['type']=='pcb_via' and g.key(e)==key and math.dist([e['x'],e['y']],row['start_xy'])<.01);site=row['site'];pts=[[start['x'],start['y']]]+row.get('points',[])+[site];wire=LineString(pts).buffer(.15);via=Point(site).buffer(.25);hole=Point(site).buffer(.15);bad=[];ripped=[]
 assert box(-17.15,-17.15,17.15,17.15).covers(wire.union(via))
 assert not wire.intersects(osc_region) and not via.intersects(osc_region),'Oscillator reservation must remain clear'
 for core in usb['cores']:
  guard=LineString(core['centerline']).buffer(usb['reference_corridor_buffer_mm'])
  assert not via.intersects(guard) and (core['reference_layer']!='inner1' or not wire.intersects(guard)),'USB reference corridor must remain clear'
 for e in list(j):
  typ=e['type'];same=g.key(e)==key
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   shape=g.geometry(e);margin=.253 if typ=='pcb_plated_hole' else .153
   if same:
    if typ=='pcb_smtpad' and hole.intersects(shape):bad.append(('hole-in-pad',e[typ+'_id']))
   elif via.distance(shape)<margin or ('inner1' in e.get('layers',[e.get('layer','top')]) and wire.distance(shape)<margin):bad.append((typ,e[typ+'_id']))
  elif typ=='pcb_keepout':
   c=e['center'];shape=Point(c['x'],c['y']).buffer(e['radius']);assert min(wire.distance(shape),via.distance(shape))>=.153,'Mount keepout'
  elif typ=='pcb_hole':assert min(wire.distance(Point(e['x'],e['y']).buffer(e['hole_diameter']/2)),via.distance(Point(e['x'],e['y']).buffer(e['hole_diameter']/2)))>=.25,'NPTH clearance'
  elif typ in ['pcb_via','pcb_trace'] and not same:
   shapes=[(l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in stack] if typ=='pcb_via' else [(a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']]
   if any(via.distance(s)<.153 or (l=='inner1' and wire.distance(s)<.153) for l,s in shapes):
    identifier=e[typ+'_id'];net=g.nets.get(g.key(e));assert not identifier.startswith(fixed) and (net not in power or (row.get('reroute_sense2') and typ=='pcb_trace' and net=='SENSE2')),('Protected collision',identifier,net);ripped.append({'id':identifier,'type':typ,'net':net});j.remove(e)
 assert not bad,('Illegal phase transition',name,bad)
 total=sum(inner_length(t) for t in j if t['type']=='pcb_trace' and g.key(t)==key)+LineString(pts).length;assert total<=policy['maximum_total_phase_inner1_length_mm']
 attrs={k:start[k] for k in ['source_net_id','source_trace_id','subcircuit_connectivity_map_key','subcircuit_id'] if k in start};uid='reviewed_phase_inner1_'+name
 assert not any(e.get(e['type']+'_id') in [uid,uid+'_via'] for e in j)
 j.append(dict(type='pcb_trace',pcb_trace_id=uid,route=[dict(route_type='wire',x=x,y=y,layer='inner1',width=.3) for x,y in pts],pcb_port_ids=[],**attrs));j.append(dict(type='pcb_via',pcb_via_id=uid+'_via',x=site[0],y=site[1],outer_diameter=.5,hole_diameter=.3,layers=stack,from_layer='top',to_layer='bottom',tented_on_top=True,tented_on_bottom=True,**attrs));history.append({'net':name,'points_mm':pts,'inner1_length_mm':LineString(pts).length,'total_phase_inner1_length_mm':total,'ripped_ordinary_neighbours':ripped})
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/opposite-edge/reviewed-phase-transitions.json').write_text(json.dumps({'construction_requires_independent_checks':True,'transitions':history,'board_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest()},indent=2)+'\n');print(history)
