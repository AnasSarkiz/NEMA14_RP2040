"""Fresh endpoint/corridor probe bound to the final eight-path native geometry."""
from pathlib import Path
import json,math,hashlib,itertools
exec(Path('experiments/integrated/corridor-geometry.py').read_text());raw=Path('artifacts/iteration-3/authored.circuit.json').read_bytes();j=json.loads(raw);placed.clear()
for e in j:
 if e['type']=='pcb_trace':
  cu=[]
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:cu.append(([a['layer']],LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128)))
  placed.append({'name':e['pcb_trace_id'],'copper':cu})
 if e['type']=='pcb_via':placed.append({'name':e['pcb_via_id'],'copper':[(e['layers'],Point(e['x'],e['y']).buffer(e['outer_diameter']/2,quad_segs=128))]})
base=list(placed);ground=sp[pp['R_SA','pin2']['source_port_id']]['subcircuit_connectivity_map_key'];port_sources={p['pcb_port_id']:sp[p['source_port_id']] for p in pp.values()};foreign=[shape for e,shape in padrows if port_sources.get(e.get('pcb_port_id'),{}).get('subcircuit_connectivity_map_key')!=ground]
def top_ok(points):
 poly=LineString(points).buffer(.3,quad_segs=128)
 if poly.distance(keep)<.15-1e-6:return False
 if any(poly.distance(p)<.15-1e-6 for p in foreign):return False
 return all(poly.distance(p)>=.15-1e-6 for item in base for layers,p in item['copper'] if 'top' in layers)
def via_clear(v):
 disk=Point(*v).buffer(.225,quad_segs=128);hole=Point(*v).buffer(.15,quad_segs=128)
 if disk.distance(keep)<.15-1e-6:return False
 if any(hole.intersection(shape).area>1e-9 for _,shape in padrows):return False
 if any(disk.distance(p)<.15-1e-6 for p in foreign):return False
 return all(disk.distance(p)>=.15-1e-6 for item in base for layers,p in item['copper'])
ends=[[7.4488762,4.200887],[10.9511238,3.7]];starts={'R_SA':[[7.3,.45],[7.237,-.4684992],[8.1782149,-1.5320043]],'R_SB':[[6.481258,16.66],[5.53,15.5955202]]};trials=[];out=[]
for name in ['R_SA','R_SB']:
 source=xy(pp[name,'pin2']);lower=g.pad_shape(pads[pp[name,'pin2']['pcb_port_id']]).distance(g.pad_shape(pads[pp['U_DRV','EP']['pcb_port_id']]));routes=[]
 for sv,tv in itertools.product(starts[name],ends):
  row={'source':name,'via':sv,'ep_landing':tv,'top_source_clear':top_ok([source,sv]),'top_target_clear':top_ok([tv,xy(pp['U_DRV','EP'])]),'source_via_clear':via_clear(sv),'target_via_clear':via_clear(tv)}
  if all(row[k] for k in ['top_source_clear','top_target_clear','source_via_clear','target_via_clear']):
   row['layer_trials']=[]
   for layer in ['bottom','inner1','inner2']:
    attempt={'layer':layer}
    try:
     reserved=[sv,tv];path=plan(sv,tv,layer,.6);attempt['route_found']=True;attempt['path']=path;attempt['source_to_ep_landing_mm']=math.dist(source,sv)+sum(math.dist(a,z) for a,z in zip(path,path[1:]));attempt['engineering_locality_pass']=attempt['source_to_ep_landing_mm']<=5;routes.append({**row,**attempt})
    except AssertionError as e:attempt['route_found']=False;attempt['reason']=str(e)
    row['layer_trials'].append(attempt)
  trials.append(row)
 out.append({'source':name,'pad_to_ep_minimum_distance_mm':lower,'unchanged_engineering_limit_mm':5,'feasible_probed_corridors':routes,'physical_width_continuity_verified':False,'corridors_are_not_copper':True})
r={'input_sha256':hashlib.sha256(raw).hexdigest(),'width_mm':.6,'via_pad_mm':.45,'via_drill_mm':.3,'fresh_geometry_only':True,'source_placement_unchanged':True,'returns':out,'endpoint_trials':trials,'full_routing_qualified':False};Path('artifacts/iteration-3/ground-probe.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='endpoint_trials'},indent=2))
