import json,pathlib,sys,math,heapq
from collections import defaultdict
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
p=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(p/'scripts'));import verify_supplier_connectivity as g
j=g.j;src={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'};sp=g.sp;pc=g.comp
port={}
for e in j:
 if e['type']=='pcb_port':
  s=sp[e['source_port_id']];port[src[s['source_component_id']],s['pin_number']]=e
netkey={e['name']:e['subcircuit_connectivity_map_key'] for e in j if e['type']=='source_net'}
def graph(net):
 lines=defaultdict(list);pads=[];vias=[]
 for e in j:
  if e['type'] not in ['pcb_trace','pcb_smtpad','pcb_plated_hole','pcb_via'] or g.key(e)!=netkey[net]:continue
  if e['type']=='pcb_trace':
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'] and math.hypot(a['x']-b['x'],a['y']-b['y'])>1e-9:lines[a['layer']].append(LineString([(a['x'],a['y']),(b['x'],b['y'])]))
  elif e['type']=='pcb_via':vias.append(e)
  else:pads.append(e)
 adj=defaultdict(list);nodes={};key=lambda l,x,y:(l,round(x,3),round(y,3))
 def connect(a,b,weight):adj[a].append((b,weight));adj[b].append((a,weight))
 for layer,ls in lines.items():
  geometry=unary_union(ls);parts=geometry.geoms if hasattr(geometry,'geoms') else [geometry]
  for part in parts:
   for a,b in zip(list(part.coords),list(part.coords)[1:]):
    ka,kb=key(layer,*a),key(layer,*b);nodes[ka]=a;nodes[kb]=b;connect(ka,kb,math.dist(a,b))
 for v in vias:
  ks=[key(l,v['x'],v['y']) for l in v['layers']]
  for a,b in zip(ks,ks[1:]):connect(a,b,0)
 for pad in pads:
  s=sp[g.ports[pad['pcb_port_id']]['source_port_id']];ref=src[s['source_component_id']];terminal=(ref,s['pin_number']);shape=g.geometry(pad).buffer(.001)
  for node,xy in nodes.items():
   if node[0] in pad.get('layers',[pad.get('layer','top')]) and shape.covers(Point(xy)):connect(terminal,node,math.dist(xy,(pad['x'],pad['y'])))
 return adj
pairs=[('LOGIC_IN',('U_BUCK',3),('C_BUCK_IN',1)),('BUCK_SW',('U_BUCK',5),('L_BUCK',1)),('BUCK_SW',('U_BUCK',5),('C_BOOTSTRAP',2)),('BUCK_BST',('U_BUCK',6),('C_BOOTSTRAP',1)),('V3V3',('L_BUCK',2),('C_BUCK_OUT1',1)),('V3V3',('U_BUCK',1),('C_BUCK_OUT1',1)),('V3V3',('U_MCU',44),('C_VREG_IN',1)),('V1V1',('U_MCU',45),('C_VREG_OUT',1)),('SENSE1',('U_DRV',23),('R_SA',1)),('SENSE2',('U_DRV',27),('R_SB',1)),('PD_VBUS',('U_DRV',22),('C_BULK',1)),('PD_VBUS',('U_DRV',22),('C_VM',1))]
rows=[];cache={}
for net,a,b in pairs:
 adj=cache.setdefault(net,graph(net)) if net not in cache else cache[net]
 distances={a:0};queue=[(0,0,a)];counter=0;previous={}
 while queue:
  d,_,node=heapq.heappop(queue)
  if d!=distances[node]:continue
  if node==b:break
  for nxt,w in adj.get(node,[]):
   nd=d+w
   if nd<distances.get(nxt,float('inf')):
    distances[nxt]=nd;previous[nxt]=node;counter+=1;heapq.heappush(queue,(nd,counter,nxt))
 aa=port[a];bb=port[b];path=[];node=b
 if b in distances:
  while node!=a:path.append(node);node=previous[node]
  path.append(a);path.reverse()
 row={'net':net,'from':f'{a[0]}.{a[1]}','to':f'{b[0]}.{b[1]}','pad_center_distance_mm':math.hypot(aa['x']-bb['x'],aa['y']-bb['y']),'found_centerline_path_mm':distances.get(b),'centerline_path':path}
 rows.append(row);print({k:v for k,v in row.items() if k!='centerline_path'})
report={'board_sha256':__import__('hashlib').sha256((p/'artifacts/board.circuit.json').read_bytes()).hexdigest(),'method':'Trace-chain screening through saved centerlines and real vias, preserving layers and joining terminals within pad geometry. Coordinates rounded to 1 um. This graph does not model every thickness-based copper overlap; a null result is an unresolved graph path, not an open circuit. Found paths are centerline witnesses, not guaranteed shortest physical current paths or parasitic simulations. Ground planes are excluded. Independent full-copper connectivity checks pass separately.','paths':rows}
(p/'artifacts/final-order-review-2026-10-17/critical-copper-paths.json').write_text(json.dumps(report,indent=2)+'\n')
