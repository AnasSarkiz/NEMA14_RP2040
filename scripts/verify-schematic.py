"""Independent schematic geometry/ERC and preservation analysis; no inferred trace connectivity."""
import collections, hashlib, json, pathlib, subprocess
from shapely.geometry import Point, LineString
root=pathlib.Path(__file__).resolve().parents[1]
board_path=root/'artifacts/board.circuit.json';j=json.loads(board_path.read_text())
out=root/'artifacts/schematic-redesign';out.mkdir(exist_ok=True)
preservation_path=out/'preservation.json'
revision=json.loads(preservation_path.read_text())['baseline_git_revision'] if preservation_path.exists() else subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
baseline=json.loads(subprocess.check_output(['git','show',revision+':artifacts/board.circuit.json'],cwd=root))
sha=lambda b:hashlib.sha256(b).hexdigest()
errors=[]
immutable=lambda a:sorted((e for e in a if not e['type'].startswith('schematic_')),key=lambda e:(e['type'],str(e.get(e['type']+'_id',''))))
if immutable(j)!=immutable(baseline):errors.append('Non-schematic source, PCB or CAD records changed')
archive=(root/'artifacts/nema14-gerbers.zip').read_bytes()
old_archive=subprocess.check_output(['git','show',revision+':artifacts/nema14-gerbers.zip'],cwd=root)
if archive!=old_archive:errors.append('Gerber ZIP bytes changed')
source={e['source_component_id']:e for e in j if e['type']=='source_component'}
sp={e['source_port_id']:e for e in j if e['type']=='source_port'}
ports={e['source_port_id']:e for e in j if e['type']=='schematic_port'}
components=[e for e in j if e['type']=='schematic_component'];sheets=[e for e in j if e['type']=='schematic_sheet']
if len(sheets)!=5 or any(e.get('sheet_width')!=297 or e.get('sheet_height')!=210 for e in sheets):errors.append('Expected five A4 sheets')
if collections.Counter(e['source_component_id'] for e in components)!=collections.Counter(source.keys()):errors.append('Component symbol coverage mismatch')
if ports.keys()!=sp.keys():errors.append('Physical pin coverage mismatch')
for sid,p in ports.items():
 s=sp[sid]
 if p.get('pin_number')!=s.get('pin_number') or p.get('display_pin_label')!=s.get('name'):errors.append('Physical pin identity mismatch: '+sid)
edges=[]
for t in j:
 if t['type']=='schematic_trace':
  for e in t['edges']:
   a,b=e['from'],e['to'];line=LineString([(a['x'],a['y']),(b['x'],b['y'])])
   edges.append({'trace':t,'edge':e,'line':line,'sheet':t['schematic_sheet_id'],'key':t.get('subcircuit_connectivity_map_key')})
   if abs(a['x']-b['x'])>1e-6 and abs(a['y']-b['y'])>1e-6:errors.append('Nonorthogonal wire: '+t['schematic_trace_id'])
   if not e.get('is_crossing') and any(not (.19<=q['x']<=31.81 and 2.09<=q['y']<=19.31) for q in [a,b]):errors.append('Wire outside usable drawing frame')
parent=list(range(len(edges)))
def find(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
def union(a,b):parent[find(a)]=find(b)
bridges=0;junctions=0;endpoint=lambda line,p:any(Point(q).distance(p)<1e-5 for q in line.coords)
for i,a in enumerate(edges):
 for k,b in enumerate(edges[i+1:],i+1):
  if a['sheet']!=b['sheet'] or not a['line'].intersects(b['line']):continue
  g=a['line'].intersection(b['line'])
  if a['key']==b['key']:
   union(i,k)
   if g.geom_type=='Point' and not(endpoint(a['line'],g) and endpoint(b['line'],g)):
    dots=[Point(p['x'],p['y']) for t in j if t['type']=='schematic_trace' and t.get('subcircuit_connectivity_map_key')==a['key'] and t['schematic_sheet_id']==a['sheet'] for p in t.get('junctions',[])]
    # Collinear subdivision is not a branch; a transverse T/cross needs a dot.
    av=a['line'].coords[0][0]==a['line'].coords[-1][0];bv=b['line'].coords[0][0]==b['line'].coords[-1][0]
    if av!=bv:
     junctions+=1
     if not any(p.distance(g)<1e-5 for p in dots):errors.append('Unmarked same-net branch '+g.wkt)
  elif g.geom_type!='Point':errors.append('Different-net wire overlap: '+g.wkt)
  elif endpoint(a['line'],g) or endpoint(b['line'],g):errors.append('Different-net wire T/contact: '+g.wkt)
  elif not(a['edge'].get('is_crossing') or b['edge'].get('is_crossing')):errors.append('Unmarked different-net crossing: '+g.wkt)
  else:bridges+=1
# Aggregate endpoint rays also catches T branches made from three meeting endpoints.
branch_candidates={}
for e in edges:
 for q in e['line'].coords:
  branch_candidates[(e['sheet'],e['key'],round(q[0],6),round(q[1],6))]=Point(q)
for (sheet,key,x,y),p in branch_candidates.items():
 rays=set()
 for e in edges:
  if e['sheet']!=sheet or e['key']!=key or e['line'].distance(p)>1e-5:continue
  for q in e['line'].coords:
   dx,dy=q[0]-p.x,q[1]-p.y
   if abs(dx)+abs(dy)>1e-5:rays.add(('R' if dx>0 else 'L') if abs(dx)>abs(dy) else ('U' if dy>0 else 'D'))
 if len(rays)>=3:
  dots=[Point(q['x'],q['y']) for t in j if t['type']=='schematic_trace' and t.get('subcircuit_connectivity_map_key')==key and t['schematic_sheet_id']==sheet for q in t.get('junctions',[])]
  if not any(q.distance(p)<1e-5 for q in dots):errors.append('Unmarked endpoint junction '+p.wkt)
nets={e['source_net_id']:e for e in j if e['type']=='source_net'}
labels=[e for e in j if e['type']=='schematic_net_label'];hubs={}
def at(sheet,key,p):return [i for i,e in enumerate(edges) if e['sheet']==sheet and e['key']==key and e['line'].distance(p)<1e-5]
for l in labels:
 n=nets.get(l.get('source_net_id'));key=l.get('subcircuit_connectivity_map_key')
 if not n or n['subcircuit_connectivity_map_key']!=key or n['name']!=l['text']:errors.append('Invalid named-net label');continue
 p=Point(l['anchor_position']['x'],l['anchor_position']['y']);hits=at(l['schematic_sheet_id'],key,p)
 if not hits:errors.append('Floating named-net label: '+l['text']);continue
 for h in hits[1:]:union(hits[0],h)
 if key in hubs:union(hubs[key],hits[0])
 else:hubs[key]=hits[0]
roots=collections.defaultdict(list);nc_count=0
paths=[e for e in j if e['type']=='schematic_path' and e['schematic_path_id'].startswith('pro_nc_')]
for sid,p in ports.items():
 s=sp[sid];key=s.get('subcircuit_connectivity_map_key');xy=Point(p['center']['x'],p['center']['y']);name=source[s['source_component_id']]['name']+'.'+s['name']
 if key:
  hits=at(p['schematic_sheet_id'],key,xy)
  if not hits:errors.append('Pin lacking a real own-net conductor: '+name)
  else:
   for h in hits[1:]:union(hits[0],h)
   roots[key].append((hits[0],name))
 else:
  nc_count+=1
  marks=[e for e in paths if e['schematic_sheet_id']==p['schematic_sheet_id'] and LineString([(q['x'],q['y']) for q in e['points']]).distance(xy)<1e-5]
  if len(marks)!=2:errors.append('Missing explicit NC cross: '+name)
  if any(e['sheet']==p['schematic_sheet_id'] and e['line'].distance(xy)<1e-5 for e in edges):errors.append('NC pin touches conductor: '+name)
for key,pins in roots.items():
 islands=collections.defaultdict(list)
 for i,name in pins:islands[find(i)].append(name)
 if len(islands)>1:errors.append('Visually disconnected source net '+key+': '+str(list(islands.values())))
# A port must never touch a conductor belonging to any other source net.
for sid,p in ports.items():
 xy=Point(p['center']['x'],p['center']['y']);key=sp[sid].get('subcircuit_connectivity_map_key')
 for e in edges:
  if e['sheet']==p['schematic_sheet_id'] and e['key']!=key and e['line'].distance(xy)<1e-5:errors.append('Pin contacts another net: '+sid)
report={'board_sha256':sha(board_path.read_bytes()),'passed':not errors,'sheet_count':len(sheets),'sheet_names':[s['name'] for s in sheets],'component_count':len(components),'physical_pin_count':len(ports),'connected_net_count':len(roots),'explicit_NC_pin_count':nc_count,'named_net_label_count':len(labels),'orthogonal_wire_segments':len(edges),'marked_different_net_crossings':bridges,'checked_same_net_branch_intersections':junctions,'electrical_source_and_PCB_CAD_preserved':immutable(j)==immutable(baseline),'actual_Gerber_ZIP_preserved':archive==old_archive,'errors':errors}
(out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
proof={'baseline_git_revision':revision,'baseline_board_sha256':sha(subprocess.check_output(['git','show',revision+':artifacts/board.circuit.json'],cwd=root)),'current_board_sha256':sha(board_path.read_bytes()),'non_schematic_records_identical':immutable(j)==immutable(baseline),'gerber_zip_bytes_identical':archive==old_archive,'gerber_zip_sha256':sha(archive)}
preservation_path.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
