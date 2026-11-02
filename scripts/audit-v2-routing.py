"""Check a V2 routing candidate independently of the router's success flag.

All four copper layers, actual plated transitions, NPTH slots, full circular
mounting keepouts and named physical pin assignments are checked. This is an
engineering screen; it does not replace final CAM or electrical qualification.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from shapely.affinity import rotate
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
import verify_supplier_connectivity as g

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
data=g.j
baseline_path=ROOT/'artifacts/v2/source.circuit.json'
baseline=json.loads(baseline_path.read_text())
trace_keys={e['source_trace_id']:e.get('subcircuit_connectivity_map_key') for e in data if e['type']=='source_trace'}
net_keys={e['source_net_id']:e.get('subcircuit_connectivity_map_key') for e in data if e['type']=='source_net'}
original_key=g.key
def key(e):
    return original_key(e) or trace_keys.get(e.get('source_trace_id')) or net_keys.get(e.get('source_net_id'))
g.key=key

def physical_nets(records):
    components={e['source_component_id']:e['name'] for e in records if e['type']=='source_component'}
    ports={e['source_port_id']:e for e in records if e['type']=='source_port'}
    nets={e['source_net_id']:e['name'] for e in records if e['type']=='source_net'}
    pins={}
    for e in records:
        if e['type']!='source_trace':continue
        names={nets[n] for n in e.get('connected_source_net_ids',[]) if n in nets}
        if len(names)>1:raise ValueError('Source shorts named nets: '+str(names))
        if not names:continue
        name=next(iter(names))
        for pid in e.get('connected_source_port_ids',[]):
            p=ports[pid];identity=(components[p['source_component_id']],p['pin_number'])
            if identity in pins and pins[identity]!=name:raise ValueError('Pin shorts named nets: '+str(identity))
            pins[identity]=name
    return pins

before,after=physical_nets(baseline),physical_nets(data)
pin_changes=[{'component':n,'pin':p,'before':before.get((n,p)),'after':after.get((n,p))}
             for n,p in sorted(before.keys()|after.keys()) if before.get((n,p))!=after.get((n,p))]
placement_types={'pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_hole','pcb_keepout'}
def placement_records(records):
    return {(e['type'],e[e['type']+'_id']):e for e in records if e['type'] in placement_types}
before_placement,after_placement=placement_records(baseline),placement_records(data)
placement_changes=[{'type':t,'id':uid} for t,uid in sorted(before_placement.keys()|after_placement.keys())
                   if before_placement.get((t,uid))!=after_placement.get((t,uid))]
opens=[]
for net,name in g.nets.items():
    elements,roots=g.groups(net)
    islands=defaultdict(set)
    for e,r in zip(elements,roots):
        if not e.get('pcb_port_id'):continue
        p=g.ports[e['pcb_port_id']];component=g.src[g.comp[p['pcb_component_id']]['source_component_id']]
        islands[r].add(component+'.'+g.sp[p['source_port_id']]['name'])
    if len(islands)>1:opens.append({'net':name,'islands':[sorted(v) for v in islands.values()]})

board=next(e for e in data if e['type']=='pcb_board')
boundary=box(-board['width']/2,-board['height']/2,board['width']/2,board['height']/2)
layers=['top','inner1','inner2','bottom']
copper={l:defaultdict(list) for l in layers}
errors=[]
widths=defaultdict(list)
def add(e,geometry,on_layers):
    net=key(e)
    if net is None:
        if e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour']:
            errors.append({'kind':'unassigned_routed_copper','record':e})
        net='unconnected:'+e.get('pcb_smtpad_id',e.get('pcb_plated_hole_id','unknown'))
    for layer in on_layers:
        if layer not in copper:raise ValueError('Unknown copper layer: '+str(layer))
        copper[layer][net].append(geometry)

for e in data:
    typ=e['type']
    if typ in ['pcb_smtpad','pcb_plated_hole']:
        add(e,g.geometry(e),e.get('layers',[e.get('layer','top')]))
    elif typ=='pcb_via':
        if e['hole_diameter']<.3-1e-6 or e['outer_diameter']<.45-1e-6:
            errors.append({'kind':'undersized_via','via':e['pcb_via_id'],'hole_mm':e['hole_diameter'],'outer_mm':e['outer_diameter']})
        if e['outer_diameter']-e['hole_diameter']<.15-1e-6:
            errors.append({'kind':'undersized_via_annulus','via':e['pcb_via_id'],
                           'annular_ring_mm':(e['outer_diameter']-e['hole_diameter'])/2})
        if e.get('layers')!=layers:errors.append({'kind':'via_stack','via':e})
        add(e,Point(e['x'],e['y']).buffer(e['outer_diameter']/2,quad_segs=64),layers)
    elif typ=='pcb_trace':
        for a,b in zip(e['route'],e['route'][1:]):
            if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
            width=max(a['width'],b['width'])
            widths[g.nets.get(key(e),str(key(e)))].append(width)
            if width<.16-1e-6:errors.append({'kind':'undersized_trace','trace':e['pcb_trace_id'],'width_mm':width})
            add(e,LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(width/2,quad_segs=64),[a['layer']])
    elif typ=='pcb_copper_pour':
        shape=e['brep_shape'];coords=lambda r:[(p['x'],p['y']) for p in r['vertices']]
        add(e,Polygon(coords(shape['outer_ring']),[coords(r) for r in shape.get('inner_rings',[])]),[e['layer']])

holes=[];mount_holes=[];supplier_holes=[]
for e in data:
    if e['type']!='pcb_hole':continue
    if e['hole_shape']=='circle':shape=Point(e['x'],e['y']).buffer(e['hole_diameter']/2,quad_segs=64)
    else:
        w,h=e['hole_width'],e['hole_height'];dx,dy=((w-h)/2,0) if w>=h else (0,(h-w)/2)
        shape=rotate(LineString([(e['x']-dx,e['y']-dy),(e['x']+dx,e['y']+dy)]).buffer(min(w,h)/2,quad_segs=64),e.get('ccw_rotation',0),origin=(e['x'],e['y']))
    holes.append(shape)
    (supplier_holes if e.get('pcb_component_id') else mount_holes).append(shape)
keepouts=[]
for e in data:
    if e['type']!='pcb_keepout':continue
    c=e['center']
    shape=Point(c['x'],c['y']).buffer(e['radius'],quad_segs=128) if e['shape']=='circle' else box(c['x']-e['width']/2,c['y']-e['height']/2,c['x']+e['width']/2,c['y']+e['height']/2)
    keepouts.append((e['layers'],shape))

clearance=[];shorts=[];edge=[];forbidden=[];minimum_gaps=[];hole_clearance=[];hole_gaps=[];supplier_hole_gaps=[]
for layer,by_net in copper.items():
    names=list(by_net);shapes=[unary_union(by_net[n]) for n in names];tree=STRtree(shapes)
    for i,shape in enumerate(shapes):
        if not boundary.buffer(-.25+1e-6).covers(shape):edge.append({'layer':layer,'net':g.nets.get(names[i],names[i])})
        if any(shape.intersection(h).area>1e-8 for h in holes):forbidden.append({'layer':layer,'net':g.nets.get(names[i],names[i]),'kind':'NPTH_copper_overlap'})
        for hole in mount_holes:
            gap=shape.distance(hole);hole_gaps.append(gap)
            if gap<.25-2e-5:hole_clearance.append({'layer':layer,'net':g.nets.get(names[i],names[i]),'gap_mm':gap})
        supplier_hole_gaps.extend(shape.distance(hole) for hole in supplier_holes)
        if any(layer in ls and shape.intersection(k).area>1e-8 for ls,k in keepouts):forbidden.append({'layer':layer,'net':g.nets.get(names[i],names[i]),'kind':'mount_keepout_overlap'})
        for j in tree.query(shape.buffer(.15),predicate='intersects'):
            if j<=i:continue
            distance=shape.distance(shapes[j]);row={'layer':layer,'nets':[g.nets.get(names[q],names[q]) for q in [i,j]],'gap_mm':distance}
            minimum_gaps.append(distance)
            if distance<=1e-8:shorts.append(row)
            elif distance<.15-2e-5:clearance.append(row)

report={'stage':'routing engineering screen, not fabrication approval',
        'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'placement_source_sha256':hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
        'physical_pin_nets_checked':len(before),'changed_pin_nets':pin_changes,
        'changed_placement_records':placement_changes,
        'nets_checked':len(g.nets),'disconnected_nets':opens,
        'traces':sum(e['type']=='pcb_trace' for e in data),'vias':sum(e['type']=='pcb_via' for e in data),
        'shorts':shorts,'clearance_violations':clearance,'copper_edge_violations':edge,
        'mount_hole_copper_clearance_violations':hole_clearance,
        'minimum_mount_hole_copper_clearance_mm':min(hole_gaps,default=None),
        'minimum_supplier_locating_hole_copper_gap_mm':min(supplier_hole_gaps,default=None),
        'forbidden_copper':forbidden,'construction_errors':errors,
        'minimum_foreign_net_gap_within_0_15_mm':min(minimum_gaps,default=None),
        'trace_width_ranges_mm':{n:[min(v),max(v)] for n,v in widths.items()},
        'passed':not any([pin_changes,placement_changes,opens,shorts,clearance,edge,hole_clearance,forbidden,errors]),
        'fabrication_ready':False,
        'remaining':['Native DRC and final Gerber/drill checks','USB pair/reference and Kelvin current-sense review','Thermal/power integrity, exact motor-wire fit and procurement']}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in report.items() if k!='trace_width_ranges_mm'}))
if not report['passed']:raise SystemExit(1)
