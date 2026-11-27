"""Independent Circuit JSON copper geometry, connectivity and clearance screen.
This is not a Gerber/CAM audit or hardware signoff. No geometry is repaired.
"""
from pathlib import Path
import json,math,hashlib,sys
from collections import defaultdict
from shapely.geometry import Point,Polygon,LineString,box
from shapely.affinity import rotate
from shapely.strtree import STRtree
from routing_geometry import resolve_copper_nets
P=128;TOL=1e-6

def pad_shape(e,drill=False):
 typ=e['type'];x,y=e['x'],e['y'];shape=e.get('shape',e.get('hole_shape','circle'))
 if shape=='polygon':
  if drill:raise ValueError('Polygon drill is unsupported')
  return Polygon([(p['x'],p['y']) for p in e['points']])
 if drill:
  w=e.get('hole_width',e.get('hole_diameter',0));h=e.get('hole_height',w)
 else:
  w=e.get('width',e.get('outer_width',e.get('outer_diameter',2*e.get('radius',0))));h=e.get('height',e.get('outer_height',w))
 if w<=0 or h<=0:raise ValueError('Unknown pad dimensions '+str(e))
 if shape=='circle' or typ in ['pcb_via','pcb_hole'] and shape=='circle':g=Point(x,y).buffer(w/2,quad_segs=P)
 elif shape in ['pill','rotated_pill']:
  dx,dy=((w-h)/2,0) if w>=h else (0,(h-w)/2);g=LineString([(x-dx,y-dy),(x+dx,y+dy)]).buffer(min(w,h)/2,quad_segs=P)
 elif shape in ['rect','rotated_rect']:g=box(x-w/2,y-h/2,x+w/2,y+h/2)
 else:raise ValueError('Unsupported pad shape '+shape)
 return rotate(g,e.get('ccw_rotation',0),origin=(x,y))

def inspect(path,scope=None):
 raw=Path(path).read_bytes();b=resolve_copper_nets(json.loads(raw));board=next(e for e in b if e['type']=='pcb_board');layers=['top','inner1','inner2','bottom'];src={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};names={e['subcircuit_connectivity_map_key']:e['name'] for e in b if e['type']=='source_net'}
 records=[];unsupported=[]
 def append(e,geom,ls,pid=None):
  port=pp.get(pid,{});source=sp.get(port.get('source_port_id'),{});key=source.get('subcircuit_connectivity_map_key') if pid else e.get('subcircuit_connectivity_map_key');ref=(src.get(source.get('source_component_id'),'')+'.'+source.get('name','')) if pid else None
  records.append({'id':e.get(e['type']+'_id',e.get('pcb_trace_id')),'kind':e['type'],'net':key,'layers':ls,'geometry':geom,'port':pid,'reference':ref})
 for e in b:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole','pcb_via']:
   g=pad_shape(e)
   if typ in ['pcb_plated_hole','pcb_via']:g=g.difference(pad_shape(e,True))
   append(e,g,e.get('layers',[e.get('layer','top')]),e.get('pcb_port_id'))
  elif typ=='pcb_trace':
   for a,z in zip(e['route'],e['route'][1:]):
    if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:
     g=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=P);append(e,g,[a['layer']])
  elif typ=='pcb_copper_pour':
   shape=e.get('brep_shape');coords=lambda r:[(v['x'],v['y']) for v in r['vertices']]
   if not shape:unsupported.append(e);continue
   append(e,Polygon(coords(shape['outer_ring']),[coords(r) for r in shape.get('inner_rings',[])]),[e['layer']])
 parent=list(range(len(records)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 shorts=[];clearance=[];seen=set();limit=board['min_trace_to_pad_edge_clearance']
 for l in layers:
  ids=[i for i,r in enumerate(records) if l in r['layers']];gs=[records[i]['geometry'] for i in ids];tree=STRtree(gs)
  for local,g in enumerate(gs):
   for other in tree.query(g.buffer(limit),predicate='intersects'):
    i,j=ids[local],ids[int(other)]
    if j<=i:continue
    a,z=records[i],records[j];same=a['net'] and a['net']==z['net'];dist=g.distance(gs[int(other)])
    if same:
     if g.intersection(gs[int(other)]).area>1e-10:parent[find(j)]=find(i)
    elif dist<limit-TOL:
     k=(a['id'],z['id'],l,round(dist,6))
     if k in seen:continue
     seen.add(k);row={'a':a['id'],'b':z['id'],'a_ref':a['reference'],'b_ref':z['reference'],'a_net':names.get(a['net'],a['net']),'b_net':names.get(z['net'],z['net']),'layer':l,'clearance_mm':dist,'required_mm':limit};clearance.append(row)
     if g.intersection(gs[int(other)]).area>1e-10:shorts.append(row)
 islands=defaultdict(lambda:defaultdict(set));portroots={}
 for i,r in enumerate(records):
  if r['port'] and r['net']:islands[r['net']][find(i)].add(r['reference']);portroots[r['port']]=find(i)
 opens=[{'net':names.get(k,k),'islands':[sorted(x) for x in v.values()]} for k,v in islands.items() if len(v)>1]
 outline=box(-board['width']/2,-board['height']/2,board['width']/2,board['height']/2);safe=outline.buffer(-board['min_board_edge_clearance'],join_style=2);edge=[];keep=[]
 for r in records:
  if not safe.buffer(TOL).covers(r['geometry']):edge.append({'id':r['id'],'kind':r['kind']})
  for e in b:
   if e['type']=='pcb_keepout' and set(r['layers'])&set(e['layers']):
    if e['shape']!='circle':raise ValueError('Unsupported keepout')
    k=Point(e['center']['x'],e['center']['y']).buffer(e['radius'],quad_segs=P)
    if k.intersection(r['geometry']).area>1e-8:keep.append({'id':r['id'],'keepout':e.get('pcb_keepout_id')})
 drills=[];drill_violations=[];hole_trace=[]
 for e in b:
  if e['type'] in ['pcb_via','pcb_plated_hole','pcb_hole']:drills.append((e,pad_shape(e,True)))
 for i,(a,ga) in enumerate(drills):
  for z,gz in drills[i+1:]:
   limit_drill=board.get('min_via_hole_edge_to_via_hole_edge_clearance',.2) if a['type']==z['type']=='pcb_via' else board.get('min_plated_hole_drill_edge_to_drill_edge_clearance',.45)
   distance=ga.distance(gz)
   if distance<limit_drill-TOL:drill_violations.append({'a':a.get(a['type']+'_id'),'b':z.get(z['type']+'_id'),'clearance_mm':distance,'required_mm':limit_drill})
 for e,drill in drills:
  if e['type']!='pcb_hole':continue
  for record in records:
   if record['kind']=='pcb_trace' and record['geometry'].distance(drill)<board.get('min_trace_to_hole_edge_clearance',.2)-TOL:hole_trace.append({'trace':record['id'],'hole':e['pcb_hole_id']})
 scoped=[]
 if scope:
  srj=json.loads(Path(scope).read_text())
  for c in srj['connections']:
   ids=[p['pcb_port_id'] for p in c['pointsToConnect'] if p.get('pcb_port_id')];roots={portroots.get(p,'missing:'+p) for p in ids};scoped.append({'connection':c['name'],'terminals':len(ids),'islands':len(roots),'connected':len(roots)==1})
 return {'input_sha256':hashlib.sha256(raw).hexdigest(),'scope':'Independent Circuit JSON polygonal copper; not CAM, impedance, thermal or hardware validation','round_curve_quad_segments':P,'numerical_comparison_tolerance_mm':TOL,'pcb_traces':sum(e['type']=='pcb_trace' for e in b),'pcb_vias':sum(e['type']=='pcb_via' for e in b),'copper_primitives':len(records),'layers_checked':layers,'shorts':shorts,'clearance_violations':clearance,'drill_spacing_violations':drill_violations,'hole_trace_violations':hole_trace,'board_edge_violations':edge,'screw_keepout_violations':keep,'disconnected_nets':opens,'scoped_connections':scoped,'scope_connected':all(x['connected'] for x in scoped) if scope else None,'unsupported':unsupported,'geometric_clearance_pass':not(shorts or clearance or drill_violations or hole_trace or edge or keep or unsupported),'full_board_connectivity_pass':not(opens or shorts or unsupported),'manufacturing_qualified':False}
if __name__=='__main__':
 r=inspect(sys.argv[1],sys.argv[3] if len(sys.argv)>3 else None);Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['shorts','clearance_violations','disconnected_nets','scoped_connections']},indent=2));print('shorts',len(r['shorts']),'clearance violations',len(r['clearance_violations']),'disconnected nets',len(r['disconnected_nets']));raise SystemExit(0 if r['geometric_clearance_pass'] and r['full_board_connectivity_pass'] else 1)
