"""Transfer qualified copper by semantic physical terminal, never by generated IDs."""
import pathlib,sys,json,copy,math,hashlib,builtins
from shapely.geometry import Point,LineString,Polygon,box
from shapely.affinity import rotate
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'scripts'));import verify_supplier_connectivity as g
old=json.loads((root/('artifacts/board.circuit.json' if '--incremental' in sys.argv else 'artifacts/top-assembly/baseline.circuit.json')).read_text());fresh=json.loads((root/'artifacts/final-source.circuit.json').read_text());assert not [e for e in fresh if e['type'].endswith('_error')], 'Native source errors remain'
def index(j,t):return {e[t+'_id']:e for e in j if e['type']==t}
os,ns=index(old,'source_component'),index(fresh,'source_component');op,np=index(old,'source_port'),index(fresh,'source_port');opp,npp=index(old,'pcb_port'),index(fresh,'pcb_port')
rp=any(c.get('manufacturer_part_number')=='RP2040' for c in ns.values());debug={'VDD':'TP_3V3','GND':'TP_GND','SWCLK':'TP_SWCLK','SWDIO':'TP_SWDIO','RUN':'TP_RUN','DCK':'TP_DCK','DIO':'TP_DIO'}
def semantic(p,ss):
 name=ss[p['source_component_id']]['name'];role=p['name']
 if name=='J_DEBUG':return debug[role],'pin1'
 if name=='J_BOOT':return ('TP_BOOT' if role=='BOOT' else 'TP_BOOT_GND' if rp else 'TP_BOOT_USB_DP'),'pin1'
 if name in ['J_PD','J_DATA']:role=role.replace('DN','DM')
 return name,role
freshroles={semantic(p,ns):p for p in np.values()};remap={};netmap={}
for id,p in op.items():
 q=freshroles.get(semantic(p,os));assert q is not None,semantic(p,os);remap[id]=q['source_port_id']
 a,b=p.get('subcircuit_connectivity_map_key'),q.get('subcircuit_connectivity_map_key');assert bool(a)==bool(b),(semantic(p,os),a,b)
 if a:assert a not in netmap or netmap[a]==b;netmap[a]=b
remap.update(netmap);newpp_bysp={p['source_port_id']:p for p in npp.values()}
for id,p in opp.items():remap[id]=newpp_bysp[remap[p['source_port_id']]]['pcb_port_id']
newnets={e['subcircuit_connectivity_map_key']:e for e in fresh if e['type']=='source_net'}
for e in old:
 if e['type']=='source_net':remap[e['source_net_id']]=newnets[netmap[e['subcircuit_connectivity_map_key']]]['source_net_id']
newtraces=[e for e in fresh if e['type']=='source_trace']
for e in old:
 if e['type']!='source_trace':continue
 mapped={remap[p] for p in e['connected_source_port_ids']};key=netmap[e['subcircuit_connectivity_map_key']];candidates=[q for q in newtraces if q.get('subcircuit_connectivity_map_key')==key];assert candidates,key
 q=max(candidates,key=lambda q:len(mapped.intersection(q['connected_source_port_ids'])));remap[e['source_trace_id']]=q['source_trace_id']
def reid(v):
 if isinstance(v,str):return remap.get(v,v)
 if isinstance(v,list):return [reid(x) for x in v]
 if isinstance(v,dict):return {k:reid(x) for k,x in v.items()}
 return v
def padkey(e,pp,sp):return sp[pp[e['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key')
oldpads=[e for e in old if e['type'] in ['pcb_smtpad','pcb_plated_hole']];newpads=[e for e in fresh if e['type'] in ['pcb_smtpad','pcb_plated_hole']];padgeoms={builtins.id(p):g.geometry(p) for p in oldpads+newpads};original_geometry=g.geometry;g.geometry=lambda e:padgeoms[builtins.id(e)] if builtins.id(e) in padgeoms else original_geometry(e);newpadbyport={e['pcb_port_id']:e for e in newpads};changed=[]
def layers(e):return e.get('layers',[e.get('layer','top')])
for p in oldpads:
 q=newpadbyport[remap[p['pcb_port_id']]]
 if layers(p)!=layers(q) or g.geometry(p).symmetric_difference(g.geometry(q)).area>1e-7:changed.append(p)
changedportids={p['pcb_port_id'] for p in changed};kept=[];removed=[]
for original in old:
 if original['type'] not in ['pcb_trace','pcb_via']:continue
 e=reid(copy.deepcopy(original));key=e.get('subcircuit_connectivity_map_key');assert key in newnets,key
 hit=original['type']=='pcb_trace' and bool(set(original.get('pcb_port_ids',[]))&changedportids)
 geoms=[]
 if original['type']=='pcb_trace':
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:geoms.append((a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)))
 else:geoms=[(l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in e['layers']]
 for l,geom in geoms:
  if hit:break
  if any(l in layers(p) and netmap.get(padkey(p,opp,op))==key and geom.intersects(g.geometry(p)) for p in changed):hit=True
  if any(l in layers(p) and padkey(p,npp,np)!=key and geom.distance(g.geometry(p))<.150001 for p in newpads):hit=True
  if any(geom.distance(Point(h['x'],h['y']).buffer(h['hole_diameter']/2))<.1 for h in fresh if h['type']=='pcb_hole'):hit=True
 if original['type']=='pcb_via':
  thermal=False
  offsets=json.loads((root/'src/thermal-via-offsets.json').read_text())
  for p in newpads:
   if p['type']!='pcb_smtpad' or p.get('width',0)<=1 or p.get('height',0)<=1:continue
   ref=ns[next(c['source_component_id'] for c in fresh if c['type']=='pcb_component' and c['pcb_component_id']==p['pcb_component_id'])]['name']
   if ref not in offsets:continue
   off=offsets[ref]
   site=(p['x']+off['x'],p['y']+off['y'])
   if math.dist(site,(e['x'],e['y']))<.001 and padkey(p,npp,np)==key and g.geometry(p).covers(Point(e['x'],e['y']).buffer(e['outer_diameter']/2)):thermal=True
  drill=Point(e['x'],e['y']).buffer(e['hole_diameter']/2)
  if not thermal and any(p['type']=='pcb_smtpad' and drill.intersects(g.geometry(p)) for p in newpads):hit=True
 if hit:removed.append(original.get('pcb_trace_id',original.get('pcb_via_id')))
 else:kept.append(e)
board=[{**e,'is_via_in_pad_allowed':True} if e['type']=='pcb_board' else e for e in fresh if e['type'] not in ['pcb_trace','pcb_via','pcb_copper_pour'] and not e['type'].endswith(('_error','_warning'))]+kept
(root/'artifacts/board.circuit.json').write_text(json.dumps(board,indent=2)+'\n')
report={'baseline_sha256':hashlib.sha256((root/'artifacts/top-assembly/baseline.circuit.json').read_bytes()).hexdigest(),'changed_physical_terminals':sorted(semantic(op[opp[p['pcb_port_id']]['source_port_id']],os) for p in changed),'old_net_to_new_net':netmap,'unaffected_copper_records_retained':len(kept),'affected_copper_records_removed':removed,'requires_routing_and_independent_checks':True}
(root/'artifacts/top-assembly/copper-transfer.json').write_text(json.dumps(report,indent=2)+'\n');print(root.name,'retained',len(kept),'removed',len(removed),'changedpads',len(changed))
