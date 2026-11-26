"""Physical copper helpers shared by critical-path checks and regressions."""
from shapely.geometry import LineString
from shapely.ops import unary_union

def layer_copper(traces,board,pad_shape):
 layers={};points={}
 for trace in traces:
  for a,z in zip(trace['route'],trace['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:layers.setdefault(a['layer'],[]).append(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128))
  for node in trace['route']:
   if node['route_type']=='via':points[(round(node['x'],6),round(node['y'],6))]=trace.get('subcircuit_connectivity_map_key')
 for via in board:
  if via['type']!='pcb_via':continue
  key=(round(via['x'],6),round(via['y'],6))
  if key not in points or points[key]!=via.get('subcircuit_connectivity_map_key'):continue
  copper=pad_shape(via).difference(pad_shape(via,True))
  for layer in via['layers']:layers.setdefault(layer,[]).append(copper)
 return {layer:unary_union(shapes) for layer,shapes in layers.items()}

def shared_outside_pad(kelvin,power,pad,pad_layer):
 # An SMT pad masks permissible pickup sharing only on its physical layer.
 # A common current-carrying barrel below it is not the top-side pickup pad.
 return sum((kelvin[layer].intersection(power[layer]).difference(pad) if layer==pad_layer else kelvin[layer].intersection(power[layer])).area for layer in kelvin if layer in power)

def pad_cut_topology(board,net,shunt_port,amplifier_port,power_port,pad,pad_layer,pad_shape):
 """Kelvin pickup proof independent of per-trace names: remove only the real pad.
 The amplifier and winding conductor must become disconnected without that pad.
 """
 from shapely.geometry import Polygon
 from shapely.strtree import STRtree
 source_ports={e['source_port_id']:e for e in board if e['type']=='source_port'};ports={e['pcb_port_id']:e for e in board if e['type']=='pcb_port'};raw=[]
 for e in board:
  typ=e['type']
  if typ in ['pcb_smtpad','pcb_plated_hole']:
   pid=e.get('pcb_port_id');sp=source_ports.get(ports.get(pid,{}).get('source_port_id'),{})
   if sp.get('subcircuit_connectivity_map_key')!=net:continue
   poly=pad_shape(e)
   if typ=='pcb_plated_hole':poly=poly.difference(pad_shape(e,True))
   raw.append((poly,e.get('layers',[e.get('layer','top')]),pid,typ=='pcb_plated_hole'))
  elif typ=='pcb_via' and e.get('subcircuit_connectivity_map_key')==net:raw.append((pad_shape(e).difference(pad_shape(e,True)),e['layers'],None,True))
  elif typ=='pcb_trace' and e.get('subcircuit_connectivity_map_key')==net:
   for a,z in zip(e['route'],e['route'][1:]):
    if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:raw.append((LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(min(a['width'],z['width'])/2,quad_segs=128),[a['layer']],None,False))
  elif typ=='pcb_copper_pour' and e.get('subcircuit_connectivity_map_key')==net:
   q=e.get('brep_shape')
   if not q:raise ValueError('Unsupported pour in Kelvin topology')
   coords=lambda r:[(p['x'],p['y']) for p in r['vertices']];raw.append((Polygon(coords(q['outer_ring']),[coords(r) for r in q.get('inner_rings',[])]),[e['layer']],None,False))
 def graph(cut):
  nodes=[];bylayer={}
  def pieces(poly):return [g for g in poly.geoms if not g.is_empty and g.area>1e-10] if hasattr(poly,'geoms') else [poly] if not poly.is_empty and poly.area>1e-10 else []
  for poly,layers,pid,barrel in raw:
   if barrel:
    owner=len(nodes);nodes.append(pid)
    for layer in layers:
     q=poly.difference(pad) if cut and layer==pad_layer else poly
     for piece in pieces(q):bylayer.setdefault(layer,[]).append((owner,piece))
   else:
    for layer in layers:
     q=poly.difference(pad) if cut and layer==pad_layer else poly
     for piece in pieces(q):owner=len(nodes);nodes.append(pid);bylayer.setdefault(layer,[]).append((owner,piece))
  parents=list(range(len(nodes)))
  def root(i):
   while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
   return i
  for layer,entries in bylayer.items():
   shapes=[p for i,p in entries];tree=STRtree(shapes)
   for i,p in enumerate(shapes):
    for j in tree.query(p,predicate='intersects'):
     if p.intersection(shapes[int(j)]).area>1e-10:parents[root(entries[int(j)][0])]=root(entries[i][0])
  return {pid:{root(i) for i,p in enumerate(nodes) if p==pid} for pid in [shunt_port,amplifier_port,power_port]}
 original=graph(False);cut=graph(True);all_connected=bool(set.intersection(*(original[p] for p in [shunt_port,amplifier_port,power_port])));bypass=bool(cut[amplifier_port]&cut[power_port]);return {'all_three_terminals_connected_before_cut':all_connected,'amplifier_connected_to_winding_without_shunt_pad':bypass,'actual_shunt_pad_is_required_pickup':all_connected and not bypass,'cut_layer':pad_layer,'method':'Remove actual SMT pad copper on its own layer; preserve physical barrels and split disconnected wire/pour pieces. Trace names are not used.'}


def resolve_copper_nets(board):
 """Resolve omitted copper net keys only through native source-trace/trace IDs.
 Geometry is untouched; conflicting explicit identities fail closed.
 """
 sources={e['source_trace_id']:e.get('subcircuit_connectivity_map_key') for e in board if e['type']=='source_trace'}
 traces={};out=[]
 for original in board:
  e=dict(original)
  if e['type']=='pcb_trace':
   expected=sources.get(e.get('source_trace_id'));actual=e.get('subcircuit_connectivity_map_key')
   if actual and expected and actual!=expected:raise ValueError('Copper/source identity conflict '+e['pcb_trace_id'])
   if not actual and expected:e['subcircuit_connectivity_map_key']=expected
   traces[e['pcb_trace_id']]=e.get('subcircuit_connectivity_map_key')
  out.append(e)
 for e in out:
  if e['type']=='pcb_via':
   expected=traces.get(e.get('pcb_trace_id'));actual=e.get('subcircuit_connectivity_map_key')
   if actual and expected and actual!=expected:raise ValueError('Via/trace identity conflict')
   if not actual and expected:e['subcircuit_connectivity_map_key']=expected
 return out
