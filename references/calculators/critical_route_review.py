"""Measure final saved RP critical trace centerlines, without changing copper.

Composite results exclude pad spreading and via barrel length. This is a
layout measurement aid, not connectivity, switching-loop or qualification proof.
"""
import json,math,hashlib,heapq,collections
from pathlib import Path
from shapely.geometry import LineString,Point,box
from shapely.ops import unary_union
p=Path(__file__).resolve().parents[2];d=json.loads((p/'artifacts/board.circuit.json').read_text());sc={e['source_component_id']:e['name'] for e in d if e['type']=='source_component'};sp={e['source_port_id']:e for e in d if e['type']=='source_port'};ports={e['pcb_port_id']:e for e in d if e['type']=='pcb_port'};names={k:sc[sp[e['source_port_id']]['source_component_id']]+'.'+sp[e['source_port_id']]['name'] for k,e in ports.items()};byname={v:ports[k] for k,v in names.items()};traces=[e for e in d if e['type']=='pcb_trace'];netnames={e['source_net_id']:e['name'] for e in d if e['type']=='source_net'}
def tidports(e):
 ids=set(e.get('pcb_port_ids',[]));ids.update(v for pt in e['route'] for k,v in pt.items() if k in ['start_pcb_port_id','end_pcb_port_id']);return ids
def summarize(e):
 r=e['route'];return {'trace_ids':[e['pcb_trace_id']],'length_mm':sum(math.hypot(a['x']-b['x'],a['y']-b['y']) for a,b in zip(r,r[1:]) if all(k in a and k in b for k in ['x','y'])),'layers':sorted(set(pt['layer'] for pt in r if pt.get('layer'))),'width_range_mm':[min(pt['width'] for pt in r if pt.get('width')),max(pt['width'] for pt in r if pt.get('width'))],'vias':sum(pt.get('route_type')=='via' for pt in r),'method':'Complete actual saved trace polyline with both physical endpoint port IDs.'}
def shortest(a,b):
 pa,pb=byname[a],byname[b];net=sp[pa['source_port_id']]['subcircuit_connectivity_map_key'];pieces=[]
 for t in traces:
  if t.get('subcircuit_connectivity_map_key')!=net:continue
  for u,v in zip(t['route'],t['route'][1:]):
   if u.get('route_type')=='wire' and v.get('route_type')=='wire' and u['layer']==v['layer'] and (u['x'],u['y'])!=(v['x'],v['y']):pieces.append({'layer':u['layer'],'line':LineString([(u['x'],u['y']),(v['x'],v['y'])]),'width':min(u['width'],v['width']),'trace':t['pcb_trace_id']})
 graphs=collections.defaultdict(list)
 def node(layer,xy):return(layer,round(xy[0],6),round(xy[1],6))
 def edge(x,y,length,meta):graphs[x].append((y,length,meta));graphs[y].append((x,length,meta))
 # Nodes split at all true same-layer centerline intersections.
 raw=[]
 for layer in sorted(set(z['layer'] for z in pieces)):
  union=unary_union([z['line'] for z in pieces if z['layer']==layer]);lines=list(union.geoms) if union.geom_type=='MultiLineString' else [union]
  for line in lines:
   for u,v in zip(line.coords,list(line.coords)[1:]):
    g=LineString([u,v]);m=min((z for z in pieces if z['layer']==layer and z['line'].buffer(1e-7).covers(g)),key=lambda z:z['width']);raw.append({'layer':layer,'line':g,'meta':m,'cuts':{0.,g.length}})
 connectors=[]
 for e in d:
  if e['type']=='pcb_via' and e.get('subcircuit_connectivity_map_key')==net:
   connectors.append({'id':e['pcb_via_id'],'layers':e['layers'],'point':Point(e['x'],e['y']),'geometry':Point(e['x'],e['y']).buffer(e['outer_diameter']/2),'type':'via'})
  if e['type']=='pcb_smtpad' and e.get('pcb_port_id') in ports and sp[ports[e['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key')==net:
   if e['shape']=='rect':g=box(e['x']-e['width']/2,e['y']-e['height']/2,e['x']+e['width']/2,e['y']+e['height']/2)
   elif e['shape']=='circle':g=Point(e['x'],e['y']).buffer(e.get('radius',e.get('width',0)/2))
   else:continue
   connectors.append({'id':e['pcb_port_id'],'layers':[e['layer']],'point':Point(ports[e['pcb_port_id']]['x'],ports[e['pcb_port_id']]['y']),'geometry':g,'type':'pad'})
 for c in connectors:
  hub=('connector',c['id']);c['hub']=hub
  for z in raw:
   if z['layer'] not in c['layers'] or not z['line'].buffer(z['meta']['width']/2).intersects(c['geometry']):continue
   t=z['line'].project(c['point']);pt=z['line'].interpolate(t);z['cuts'].add(t)
   # No trace-length credit for internal pad/barrel current spreading; counted separately.
   edge(hub,node(z['layer'],pt.coords[0]),0,{'connector':c['id'],'type':c['type']})
 for z in raw:
  ts=sorted(z['cuts'])
  for u,v in zip(ts,ts[1:]):edge(node(z['layer'],z['line'].interpolate(u).coords[0]),node(z['layer'],z['line'].interpolate(v).coords[0]),v-u,{'layer':z['layer'],'width':z['meta']['width'],'trace':z['meta']['trace']})
 start,end=('connector',pa['pcb_port_id']),('connector',pb['pcb_port_id']);dist={start:0};prev={};counter=0;q=[(0,counter,start)]
 while q:
  cost,_,n=heapq.heappop(q)
  if cost!=dist[n]:continue
  if n==end:break
  for nxt,w,meta in graphs[n]:
   new=cost+w
   if new<dist.get(nxt,math.inf):dist[nxt]=new;prev[nxt]=(n,meta);counter+=1;heapq.heappush(q,(new,counter,nxt))
 if end not in dist:return {'method':'graph','error':'No centerline graph path; broad copper contact needs separate resolution.'}
 mm=[];n=end
 while n!=start:n,meta=prev[n];mm.append(meta)
 widths=[z['width'] for z in mm if 'width'in z];vs=sorted(set(z['connector'] for z in mm if z.get('type')=='via'))
 return {'length_mm':dist[end],'layers':sorted(set(z['layer'] for z in mm if 'layer'in z)),'width_range_mm':[min(widths),max(widths)],'via_ids':vs,'vias':len(vs),'trace_ids':sorted(set(z['trace'] for z in mm if 'trace'in z)),'method':'Shortest actual saved same-net centerline path, true intersections noded, copper pad/via connector contacts; excludes internal pad spreading and vertical barrel length.'}
pairs=[(z['from'],z['to']) for z in json.loads((p/'artifacts/engineering-local-routes.json').read_text())['routes']]+[('U_DRV.VBB1','C_VM2.pin1'),('U_DRV.GND','U_DRV.EP'),('U_DRV.GND18','U_DRV.EP')]
rows=[]
for a,b in pairs:
 ids={byname[a]['pcb_port_id'],byname[b]['pcb_port_id']};direct=[t for t in traces if ids<=tidports(t)]
 result=summarize(min(direct,key=lambda e:summarize(e)['length_mm'])) if direct else shortest(a,b)
 row={'from':a,'to':b,**result};rows.append(row);print(a,b,json.dumps(result))
out={'board_sha256':hashlib.sha256((p/'artifacts/board.circuit.json').read_bytes()).hexdigest(),'scope':'Final actual native saved copper; historical seeded-route length records are not treated as current. Lengths are planar centerline measures, not switching loop area/inductance/impedance or thermal qualification. Composite path excludes copper-pad spreading and via barrel length.','routes':rows}
(p/'artifacts/validation/critical-route-review.json').write_text(json.dumps(out,indent=2)+'\n')
