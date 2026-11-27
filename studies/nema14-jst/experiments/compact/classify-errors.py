"""Classify native diagnostics against actual same-net multilayer copper islands."""
from pathlib import Path
import json,sys,importlib.util,collections,hashlib
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets
from shapely.geometry import LineString
from shapely.strtree import STRtree
spec=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
p=Path('artifacts/iteration-4/normal-attempt.circuit.json');b=resolve_copper_nets(json.loads(p.read_bytes()));raw=json.loads(Path('artifacts/iteration-4/normal-native.json.all-routing.json').read_bytes());errs=[e for e in raw['findings'] if e['type']=='pcb_port_not_connected_error'];sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};nets={e['subcircuit_connectivity_map_key']:e['name'] for e in b if e['type']=='source_net'};rows=[]
for e in b:
 typ=e['type']
 if typ in ['pcb_smtpad','pcb_plated_hole','pcb_via']:
  port=e.get('pcb_port_id');key=sp[pp[port]['source_port_id']].get('subcircuit_connectivity_map_key') if port else e.get('subcircuit_connectivity_map_key');q=g.pad_shape(e)
  if typ!='pcb_smtpad':q=q.difference(g.pad_shape(e,True))
  rows.append({'geometry':q,'layers':e.get('layers',[e.get('layer','top')]),'net':key,'pid':port,'copper':typ=='pcb_via','id':e.get(typ+'_id')})
 elif typ=='pcb_trace':
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:rows.append({'geometry':LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(min(a['width'],z['width'])/2,quad_segs=128),'layers':[a['layer']],'net':e.get('subcircuit_connectivity_map_key'),'pid':None,'copper':True,'id':e['pcb_trace_id']})
parent=list(range(len(rows)))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for layer in ['top','inner1','inner2','bottom']:
 ids=[i for i,e in enumerate(rows) if layer in e['layers']];geos=[rows[i]['geometry'] for i in ids];tree=STRtree(geos)
 for j,q in enumerate(geos):
  for k in tree.query(q,predicate='intersects'):
   if k<=j:continue
   a,z=ids[j],ids[int(k)]
   if rows[a]['net'] and rows[a]['net']==rows[z]['net'] and q.intersection(geos[int(k)]).area>1e-10:parent[root(z)]=root(a)
portroot={e['pid']:root(i) for i,e in enumerate(rows) if e['pid']};islands=collections.defaultdict(list);hascu=collections.Counter()
for i,e in enumerate(rows):
 r=root(i)
 if e['pid']:islands[r].append(e['pid'])
 if e['copper']:hascu[r]+=1
byport=collections.defaultdict(list)
for e in errs:
 for pid in e['pcb_port_ids']:byport[pid].append(e)
out=[]
for pid,errors in byport.items():
 port=pp[pid];source=sp[port['source_port_id']];r=portroot.get(pid);key=source.get('subcircuit_connectivity_map_key');ports=islands[r];name=sc.get(source['source_component_id'],source['source_component_id'])+'.'+source['name'];category='unrouted_after_global_abort' if not hascu[r] else 'partial_same_net_copper_island'
 directly_owned=[t['pcb_trace_id'] for t in b if t['type']=='pcb_trace' and pid in t.get('pcb_port_ids',[])]
 if hascu[r] and not directly_owned:category='physical_contact_without_direct_trace_port_association'
 out.append({'pcb_port_id':pid,'reference':name,'net':nets.get(key,key),'message_count':len(errors),'cause_class':category,'physical_island_ports':ports,'copper_piece_count':hascu[r],'direct_trace_associations':directly_owned,'blocked_exit_proven':False})
byref={sc.get(sp[p['source_port_id']]['source_component_id'],'')+'.'+sp[p['source_port_id']]['name']:p['pcb_port_id'] for p in pp.values()}
modes={name:{'pcb_port_id':byref['U_DRV.'+name],'native_port_error':byref['U_DRV.'+name] in byport,'physical_island_ports':islands[portroot[byref['U_DRV.'+name]]]} for name in ['MS1','MS2','MS3','RESET_N','VDD']}
r={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'native_autorouting_errors':[e for e in b if e['type']=='pcb_autorouting_error'],'native_port_messages':len(errs),'unique_ports':len(byport),'duplicate_messages':len(errs)-len(byport),'by_cause':dict(collections.Counter(e['cause_class'] for e in out)),'by_net':dict(collections.Counter(e['net'] for e in out)),'mode_array':modes,'ports':out,'conclusion':'Original static MS3/RESET failure is absent; their endpoints physically join the mode-array via island. The remaining generic iteration error does not identify a unique next obstructed endpoint. Unrouted errors are downstream missing-copper reports, not proof of blocked exits.'}
Path('artifacts/iteration-5/native-error-groups.json').write_text(json.dumps(r,indent=2)+'\n');print({k:v for k,v in r.items() if k not in ['ports','mode_array']});print('mode array',modes)
