"""NEMA14 JST star-return corridor, bypass ordering and Kelvin pickup checks.
A corridor is a reserved routing contract, not copper or a routed DRC pass.
"""
from pathlib import Path
from native_sources import source_owner_names
import json,sys,math,hashlib,importlib.util
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from routing_geometry import layer_copper,shared_outside_pad,pad_cut_topology,resolve_copper_nets
spec=importlib.util.spec_from_file_location('copper',Path(__file__).with_name('inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
contract=json.loads((Path(__file__).resolve().parents[1]/'src/critical-routing-contract.json').read_text());rc=contract['sense_returns'];WIDTH=rc['reserved_trace_width_mm'];VIA_OD=rc['via_pad_diameter_mm'];VIA_ID=rc['via_hole_diameter_mm'];LIMIT=rc['placement_path_target_mm'];reservation=next((a for a in sys.argv[3:] if not a.startswith('--')),None);routed_required='--routed' in sys.argv
raw=Path(sys.argv[1]).read_bytes();b=resolve_copper_nets(json.loads(raw));board=next(e for e in b if e['type']=='pcb_board');src=source_owner_names(b);sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};pcs={src[e['source_component_id']]:e for e in b if e['type']=='pcb_component'};ports={(src[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in pp.values()};pads=[e for e in b if e['type'] in ['pcb_smtpad','pcb_plated_hole']];byport={k:unary_union([g.pad_shape(e) for e in pads if e.get('pcb_port_id')==p['pcb_port_id']]) for k,p in ports.items()}
ground=sp[ports['U_DRV','EP']['source_port_id']]['subcircuit_connectivity_map_key'];ep=byport['U_DRV','EP'];land=ep.buffer(-VIA_OD/2);alllayers=['top','inner1','inner2','bottom'];safe=__import__('shapely').geometry.box(-board['width']/2+.25,-board['height']/2+.25,board['width']/2-.25,board['height']/2-.25);keep=[Point(e['center']['x'],e['center']['y']).buffer(e['radius'],quad_segs=128) for e in b if e['type']=='pcb_keepout']

# Cache exact obstacle geometries once; spatial queries do not change clearances.
from shapely.strtree import STRtree
obstacles={l:[] for l in alllayers};obstacle_ids={l:[] for l in alllayers};obstacle_ports={l:[] for l in alllayers}
def add_obstacle(poly,layers,ident,pid=None):
 for layer in layers:obstacles[layer].append(poly);obstacle_ids[layer].append(ident);obstacle_ports[layer].append(pid)
for e in pads:
 p=pp.get(e.get('pcb_port_id'),{});source=sp.get(p.get('source_port_id'),{})
 if source.get('subcircuit_connectivity_map_key')==ground:continue
 add_obstacle(g.pad_shape(e),e.get('layers',[e.get('layer','top')]),e[e['type']+'_id'],e.get('pcb_port_id'))
for e in b:
 if e['type'] not in ['pcb_trace','pcb_via','pcb_copper_pour'] or e.get('subcircuit_connectivity_map_key')==ground:continue
 if e['type']=='pcb_trace':
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:add_obstacle(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128),[a['layer']],e['pcb_trace_id'])
 elif e['type']=='pcb_via':add_obstacle(g.pad_shape(e),e['layers'],e['pcb_via_id'])
 else:
  q=e.get('brep_shape')
  if not q:raise ValueError('Unsupported copper-pour shape in reserved corridor')
  coords=lambda r:[(p['x'],p['y']) for p in r['vertices']];poly=__import__('shapely').geometry.Polygon(coords(q['outer_ring']),[coords(r) for r in q.get('inner_rings',[])]);add_obstacle(poly,[e['layer']],e['pcb_copper_pour_id'])
trees={l:STRtree(shapes) for l,shapes in obstacles.items()}
def conflicts(poly,layer,allowed_port=None):
 bad=[]
 if not safe.buffer(1e-6).covers(poly):bad.append('board edge')
 if any(poly.intersection(k).area>1e-8 for k in keep):bad.append('screw reserve')
 x,y,z,w=poly.bounds;query=__import__('shapely').geometry.box(x-.15,y-.15,z+.15,w+.15)
 for index in trees[layer].query(query):
  i=int(index)
  if obstacle_ports[layer][i] is not None and obstacle_ports[layer][i]==allowed_port:continue
  if poly.distance(obstacles[layer][i])<.15-1e-6:bad.append(obstacle_ids[layer][i])
 return sorted(set(bad))
returns=[]
for phase,name in [('A','R_SA'),('B','R_SB')]:
 p=ports[name,'pin2'];other=ports[name,'pin1'];x,y=p['x'],p['y'];dx,dy=x-other['x'],y-other['y'];norm=math.hypot(dx,dy);dx,dy=dx/norm,dy/norm;options=[]
 for extension in rc['stub_extension_candidates_mm']:
  for lateral in [0,-.35,.35]:
   vx,vy=x+dx*extension-dy*lateral,y+dy*extension+dx*lateral;target=nearest_points(land,Point(vx,vy))[0];tx,ty=target.x,target.y
   for middle in [(vx,ty),(tx,vy)]:
    top=LineString([(x,y),(vx,vy)]).buffer(WIDTH/2,quad_segs=128);inner=LineString([(vx,vy),middle,(tx,ty)]).buffer(WIDTH/2,quad_segs=128);via=Point(vx,vy).buffer(VIA_OD/2,quad_segs=128);endvia=Point(tx,ty).buffer(VIA_OD/2,quad_segs=128);bad=conflicts(top,'top',p['pcb_port_id'])+conflicts(inner,'inner1')
    for l in alllayers:bad+=conflicts(via,l,p['pcb_port_id'])+conflicts(endvia,l,ports['U_DRV','EP']['pcb_port_id'])
    length=math.hypot(vx-x,vy-y)+abs(vx-tx)+abs(vy-ty);options.append({'source':name+'.pin2','source_pcb_port_id':p['pcb_port_id'],'source_pad_ids':[e[e['type']+'_id'] for e in pads if e.get('pcb_port_id')==p['pcb_port_id']],'target':'U_DRV.EP','top_stub':[[x,y],[vx,vy]],'inner1_path':[[vx,vy],list(middle),[tx,ty]],'via_centers':[[vx,vy],[tx,ty]],'reserved_width_mm':WIDTH,'via_pad_diameter_mm':VIA_OD,'via_hole_diameter_mm':VIA_ID,'path_length_mm':length,'engineering_length_target_mm':LIMIT,'conflicts':sorted(set(bad)),'corridor_geometry_pass':not bad,'locality_pass':length<=LIMIT+1e-6})
 best=min(options,key=lambda q:(bool(q['conflicts']),q['path_length_mm']));best['placement_corridor_pass']=best['corridor_geometry_pass'] and best['locality_pass'];best['routed_width_and_continuity_verified']=False;returns.append(best)

if reservation:
 fixed=json.loads(Path(reservation).read_text())['return_corridors'];returns=[]
 for ret in fixed:
  name=ret['source'].split('.')[0];p=ports[name,'pin2'];start=ret['top_stub'][0]
  if abs(start[0]-p['x'])+abs(start[1]-p['y'])>1e-6:raise ValueError('Reserved return corridor belongs to another placement')
  bad=conflicts(LineString(ret['top_stub']).buffer(WIDTH/2,quad_segs=128),'top',p['pcb_port_id'])+conflicts(LineString(ret['inner1_path']).buffer(WIDTH/2,quad_segs=128),'inner1')
  for v in ret['via_centers']:
   for l in alllayers:bad+=conflicts(Point(*v).buffer(VIA_OD/2,quad_segs=128),l,p['pcb_port_id'])
  ret={**ret,'conflicts':sorted(set(bad)),'corridor_geometry_pass':not bad,'placement_corridor_pass':not bad and ret['locality_pass']};returns.append(ret)
def l1(a,z):return abs(a['x']-z['x'])+abs(a['y']-z['y'])
bypass=[{'supply_pin':pin,'ceramic_distance_mm':l1(ports['C_VM','pin1'],ports['U_DRV',pin]),'bulk_distance_mm':l1(ports['C_BULK','pin1'],ports['U_DRV',pin])} for pin in ['VBB1','VBB2']]
for e in bypass:e['ceramic_closer_than_bulk']=e['ceramic_distance_mm']<e['bulk_distance_mm']
st={e.get('name'):e for e in b if e['type']=='source_trace'};trace={e['source_trace_id']:e for e in b if e['type']=='source_trace'};routed=[e for e in b if e['type']=='pcb_trace'];kelvin=[]
def layer_shapes(ts):return layer_copper(ts,b,g.pad_shape)
for phase in 'AB':
 for pole,pin,power in [('POS','pin1','DRV'),('NEG','pin2','COIL')]:
  name='KELVIN_'+phase+'_'+pole;s=st[name];pickup=ports['R_SHUNT_'+phase,pin];expected=pickup['source_port_id'];source_intent=expected in s['connected_source_port_ids'];kt=[e for e in routed if e.get('source_trace_id')==s['source_trace_id']];pt=[e for e in routed if e.get('source_trace_id')==st['POWER_'+phase+'_'+power]['source_trace_id']];ks,ps=layer_shapes(kt),layer_shapes(pt);pad=byport['R_SHUNT_'+phase,pin];shared=shared_outside_pad(ks,ps,pad,pcs['R_SHUNT_'+phase]['layer']);touch=any(poly.intersection(pad).area>1e-8 for l,poly in ks.items() if l=='top')
  kelvin.append({'branch':name,'source_pickup_port':expected,'source_intent_starts_at_shunt':source_intent,'pickup_pad_ids':[e[e['type']+'_id'] for e in pads if e.get('pcb_port_id')==pickup['pcb_port_id']],'routed_branch_traces':len(kt),'routed_power_traces':len(pt),'touches_actual_shunt_pad':touch,'shared_copper_outside_shunt_mm2':shared if kt and pt else None,'named_branch_overlap_measurement_available':bool(kt and pt),'pickup_geometry_pass':bool(kt and pt and touch and shared<=1e-8),'full_branch_continuity_verified':False})
# Width/continuity cannot be inferred from source names or zero routed copper.
# This conservative check requires a routed >=0.6 mm GND path to the EP region.
wide=[]
for t in routed:
 if t.get('subcircuit_connectivity_map_key')!=ground:continue
 for a,z in zip(t['route'],t['route'][1:]):
  if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer'] and min(a['width'],z['width'])>=WIDTH-1e-6:wide.append({'type':'pcb_trace','pcb_trace_id':t['pcb_trace_id'],'source_trace_id':t.get('source_trace_id'),'subcircuit_connectivity_map_key':ground,'route':[a,z]})
def physically_connected(ts,ends,min_width=0,ground_mode=False):
 from shapely.strtree import STRtree
 records=[]
 selected_via_points={(round(n['x'],6),round(n['y'],6)) for tr in ts for n in tr['route'] if n['route_type']=='via'}
 for pad in pads:
  pid=pad.get('pcb_port_id');s=sp.get(pp.get(pid,{}).get('source_port_id'),{})
  if pid not in ends and not(ground_mode and s.get('subcircuit_connectivity_map_key')==ground):continue
  poly=g.pad_shape(pad)
  if pad['type']=='pcb_plated_hole':poly=poly.difference(g.pad_shape(pad,True))
  records.append((poly,pad.get('layers',[pad.get('layer','top')]),pid))
 for via in b:
  if via['type']!='pcb_via':continue
  if ground_mode:
   if via.get('subcircuit_connectivity_map_key')!=ground:continue
  elif (round(via['x'],6),round(via['y'],6)) not in selected_via_points:continue
  records.append((g.pad_shape(via).difference(g.pad_shape(via,True)),via['layers'],None))
 for tr in ts:
  for a,z in zip(tr['route'],tr['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer'] and min(a['width'],z['width'])>=min_width-1e-6:
    records.append((LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(min(a['width'],z['width'])/2,quad_segs=128),[a['layer']],None))
 parent=list(range(len(records)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for layer in alllayers:
  ids=[i for i,r in enumerate(records) if layer in r[1]];polys=[records[i][0] for i in ids];tree=STRtree(polys)
  for i,poly in enumerate(polys):
   for j in tree.query(poly,predicate='intersects'):
    if poly.intersection(polys[int(j)]).area>1e-10:parent[root(ids[int(j)])]=root(ids[i])
 roots=[{root(i) for i,r in enumerate(records) if r[2]==pid} for pid in ends]
 return bool(ts and all(roots) and set.intersection(*roots))
for ret in returns:
 ret['wide_ground_wire_segments_found']=len(wide)
 ret['routed_width_and_continuity_verified']=physically_connected([tr for tr in routed if tr.get('subcircuit_connectivity_map_key')==ground],[ret['source_pcb_port_id'],ports['U_DRV','EP']['pcb_port_id']],WIDTH,True)
for row in kelvin:
 s=st[row['branch']];kt=[tr for tr in routed if tr.get('source_trace_id')==s['source_trace_id']];ends=[next(p['pcb_port_id'] for p in pp.values() if p['source_port_id']==sid) for sid in s['connected_source_port_ids']]
 row['named_branch_continuity_verified']=physically_connected(kt,ends,.16)
 phase=row['branch'].split('_')[1];positive=row['branch'].endswith('POS');shunt=ports['R_SHUNT_'+phase,'pin1' if positive else 'pin2'];amplifier=ports['U_I'+phase,'IN_POS' if positive else 'IN_NEG'];power=ports['U_DRV','OUT1A' if phase=='A' else 'OUT2A'] if positive else ports['J_MOTOR',phase+'_PLUS'];net=sp[shunt['source_port_id']]['subcircuit_connectivity_map_key'];topology=pad_cut_topology(b,net,shunt['pcb_port_id'],amplifier['pcb_port_id'],power['pcb_port_id'],byport['R_SHUNT_'+phase,'pin1' if positive else 'pin2'],pcs['R_SHUNT_'+phase]['layer'],g.pad_shape)
 row['pad_cut_topology']=topology;row['full_branch_continuity_verified']=topology['all_three_terminals_connected_before_cut'];row['pickup_geometry_pass']=topology['actual_shunt_pad_is_required_pickup'] and row['source_intent_starts_at_shunt'] and (row['shared_copper_outside_shunt_mm2'] is None or row['shared_copper_outside_shunt_mm2']<=1e-8)

usb_keys={e['subcircuit_connectivity_map_key'] for e in b if e['type']=='source_net' and e['name'] in ['USB_DM','USB_DP','MCU_DM','MCU_DP']}
usb_traces=[tr for tr in routed if tr.get('subcircuit_connectivity_map_key') in usb_keys];ground_pours={}
for pour in b:
 if pour['type']!='pcb_copper_pour' or pour.get('subcircuit_connectivity_map_key')!=ground or not pour.get('brep_shape'):continue
 q=pour['brep_shape'];coords=lambda r:[(p['x'],p['y']) for p in r['vertices']];poly=__import__('shapely').geometry.Polygon(coords(q['outer_ring']),[coords(r) for r in q.get('inner_rings',[])]);ground_pours.setdefault(pour['layer'],[]).append(poly)
ground_pours={l:unary_union(gs) for l,gs in ground_pours.items()};usb_segments=[]
for tr in usb_traces:
 for a,z in zip(tr['route'],tr['route'][1:]):
  if a['route_type']!=z['route_type'] or a['route_type']!='wire' or a['layer']!=z['layer']:continue
  ref={'top':'inner1','bottom':'inner2'}.get(a['layer']);poly=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128);covered=bool(ref in ground_pours and ground_pours[ref].buffer(1e-6).covers(poly));usb_segments.append({'trace':tr['pcb_trace_id'],'layer':a['layer'],'reference_layer':ref,'full_width_ground_reference':covered})
usb={'routed_traces':len(usb_traces),'segments':usb_segments,'uninterrupted_ground_reference_verified':bool(usb_segments) and all(s['full_width_ground_reference'] for s in usb_segments),'differential_impedance_verified':False,'limitation':'No fabricator dielectric stackup or impedance calculation is supplied. Empty copper is not a return-path pass.'}
report={'board_sha256':hashlib.sha256(raw).hexdigest(),'placement_only':not bool(routed),'usb_return_path':usb,'return_corridors':returns,'return_corridor_screen_pass':all(e['placement_corridor_pass'] for e in returns),'bypass_ordering':bypass,'bypass_ordering_pass':all(e['ceramic_closer_than_bulk'] for e in bypass),'kelvin_pickups':kelvin,'sense_return_source_ground_pass':all(sp[ports[n,'pin2']['source_port_id']]['subcircuit_connectivity_map_key']==ground for n in ['R_SA','R_SB']),'kelvin_source_intent_pass':all(e['source_intent_starts_at_shunt'] for e in kelvin),'routed_return_width_and_continuity_verified':all(r['routed_width_and_continuity_verified'] for r in returns),'routed_kelvin_full_continuity_verified':all(r['full_branch_continuity_verified'] and r['pickup_geometry_pass'] for r in kelvin),'shared_copper_error_example':{'shunt_ohms':.05,'shared_ohms':.001,'fractional_error':.02,'current_A':.4,'gain':20,'output_error_V':.008},'limits':['5 mm return length is an engineering placement target, not an Allegro numerical limit','Reserved top stubs, all-layer via barrels and inner1 strips must remain clear of unrelated future copper','Corridors are not actual vias or traces and do not prove width, physical continuity, return-plane integrity or thermal performance','Kelvin layer intersections screen shared winding copper, but full branch continuity requires independent routed connectivity']}
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['return_corridors','kelvin_pickups']},indent=2));print('Return corridor passes',sum(e['placement_corridor_pass'] for e in returns),'of',len(returns));passed=report['return_corridor_screen_pass'] and report['bypass_ordering_pass'] and report['sense_return_source_ground_pass'] and report['kelvin_source_intent_pass'];passed=passed and (not routed_required or report['routed_return_width_and_continuity_verified'] and report['routed_kelvin_full_continuity_verified'] and usb['uninterrupted_ground_reference_verified']);raise SystemExit(0 if passed else 1)
