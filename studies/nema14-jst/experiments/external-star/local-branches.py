"""Independent CP and buzzer branch continuity with actual drill subtraction, plus loop travel."""
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
r=Path('artifacts/iteration-12');outputs=[]
for mode in ['external','direct']:
 j=resolve_copper_nets(read(r/(mode+'.circuit.json')));nm,cs,pc,ss,pp,ps,ct=index(j);st={e['source_trace_id']:e.get('name','') for e in j if e['type']=='source_trace'};tr={st[e['source_trace_id']]:e for e in j if e['type']=='pcb_trace'};pads={e['pcb_port_id']:e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole']};vias=[e for e in j if e['type']=='pcb_via'];holes=unary_union([g.pad_shape(e,True) for e in j if e['type'] in ['pcb_via','pcb_hole','pcb_plated_hole']]);spec=read('experiments/reconnect/vias.json')
 def port(ref):
  owner,pin=ref.split('.');hits=[e for (n,p),e in ps.items() if n==owner and pin in ss[e['source_port_id']].get('port_hints',[p])];assert len(hits)==1,ref;return hits[0]
 def connected(names,refs,missing=None):
  records=[]
  def add(p,ls,pid=None):
   for q in list(p.geoms) if hasattr(p,'geoms') else [p]:
    if q.area>1e-10:records.append((q,ls,pid))
  for n in names:
   for a,z in zip(tr[n]['route'],tr[n]['route'][1:]):
    if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:add(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(min(a['width'],z['width'])/2,quad_segs=128).difference(holes),[a['layer']])
  for ref in refs:
   p=port(ref);e=pads[p['pcb_port_id']];add(g.pad_shape(e).difference(holes),e.get('layers',[e.get('layer','top')]),ref)
  if len(names)==3:
   for v in spec:
    e=next(e for e in vias if math.dist([e['x'],e['y']],[v['x'],v['y']])<1e-9);ring=g.pad_shape(e).difference(g.pad_shape(e,True))
    if v['name']==missing:
     for layer in e['layers']:add(ring,[layer])
    else:add(ring,e['layers'])
  parent=list(range(len(records)))
  def find(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  for i,(a,ls,_) in enumerate(records):
   for k,(b,lt,_) in enumerate(records[:i]):
    if set(ls)&set(lt) and a.intersection(b).area>1e-10:parent[find(k)]=find(i)
  return bool(set.intersection(*[{find(i) for i,r in enumerate(records) if r[2]==ref} for ref in refs]))
 definitions=[('CP1',['AUTHORED_CP1_CORRIDOR'],['U_DRV.CP1','C_CP.pin1']),('CP2',['AUTHORED_CP2_CORRIDOR'],['U_DRV.CP2','C_CP.pin2']),('flyback_sink',['BUZ_FLYBACK_SINK'],['BZ1._NEG','D_BUZZER.anode']),('flyback_supply',['BUZ_FLYBACK_SUPPLY'],['D_BUZZER.cathode','BZ1._POS']),('switch_supply',['BUZ_SWITCH_SUPPLY__0','BUZ_SWITCH_SUPPLY__1','BUZ_SWITCH_SUPPLY__2'],['C_BUZZER.pin1','BZ1._POS']),('switch_drain',['BUZ_SWITCH_DRAIN'],['BZ1._NEG','Q_BUZZER.D']),('switch_return',['BUZ_SWITCH_RETURN'],['Q_BUZZER.S','C_BUZZER.pin2']),('gate_series',['BUZ_GATE_SERIES'],['R_BUZZER_GATE.pin2','Q_BUZZER.G']),('gate_pulldown',['BUZ_GATE_PULLDOWN'],['R_BUZZER_PD.pin1','Q_BUZZER.G'])];rows=[];cp=[]
 for label,names,refs in definitions:
  assert connected(names,refs),refs;wire=sum(math.dist([a['x'],a['y']],[z['x'],z['y']]) for n in names for a,z in zip(tr[n]['route'],tr[n]['route'][1:]));depth=.035/2+.1164+.0152+1.265+.0152/2;barrels=2*depth if len(names)==3 else 0
  if len(names)==3:assert all(not connected(names,refs,v['name']) for v in spec)
  rows.append({'branch':label,'real_terminals':refs,'hole_subtracted_continuity':True,'wire_mm':wire,'conducted_barrels':2 if len(names)==3 else 0,'conducted_barrel_travel_mm':barrels,'external_wire_plus_barrel_mm':wire+barrels,'package_internal_travel_not_measured':True})
  if label in ['CP1','CP2']:
   t=tr[names[0]];stress=unary_union([LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(.096,quad_segs=128) for a,z in zip(t['route'],t['route'][1:])]);ep=g.pad_shape(pads[ps['U_DRV','EP']['pcb_port_id']]);gaps={'real_EP':stress.distance(ep),'native_square':stress.distance(box(9.8,9.8,16.2,16.2)),'real_screw_circle':stress.distance(Point(13,13).buffer(3.2,quad_segs=128))};assert min(gaps.values())>=.15;cp.append({'name':label,'actual_width_mm':.16,'stress_width_mm':.192,'stressed_gaps_mm':gaps})
 result={'mode':mode,'branches':rows,'CP':cp,'buzzer_external_loop_lengths_mm':{'flyback':sum(e['external_wire_plus_barrel_mm'] for e in rows if e['branch'] in ['flyback_sink','flyback_supply']),'switch':sum(e['external_wire_plus_barrel_mm'] for e in rows if e['branch'] in ['switch_supply','switch_drain','switch_return'])},'board_copper_pours':sum(e['type']=='pcb_copper_pour' for e in j),'drill_centres_inside_driver_EP':sum(g.pad_shape(pads[ps['U_DRV','EP']['pcb_port_id']]).covers(Point(e['x'],e['y'])) for e in vias),'full_board_or_VREG_loop_qualified':False,'manufacturing_qualified':False};outputs.append(result)
(r/'local-branches.json').write_text(json.dumps(outputs,indent=2)+'\n');print([(e['mode'],e['buzzer_external_loop_lengths_mm']) for e in outputs])
