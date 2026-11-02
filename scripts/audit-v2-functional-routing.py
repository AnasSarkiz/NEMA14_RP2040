"""Check current-carrying paths, Kelvin pickups and the oscillator's real copper.

These checks complement, rather than replace, all-net connectivity and DRC.
"""
import hashlib
import json
from collections import defaultdict

from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree
import verify_supplier_connectivity as g

layers = ['top', 'inner1', 'inner2', 'bottom']
def reference(e):
    return g.src[g.comp[e['pcb_component_id']]['source_component_id']]
def pin(e):
    return g.sp[g.ports[e['pcb_port_id']]['source_port_id']]['pin_number']
def pad(ref, number):
    return next(e for e in g.j if e['type'] in ['pcb_smtpad', 'pcb_plated_hole']
                and reference(e) == ref and pin(e) == number)

def connected(net, first, second, minimum_width=0, cut=None):
    """Union only actual same-layer intersections and physical plated barrels."""
    items=[]
    def add(shape, on_layers, port=None):
        if cut is not None: shape=shape.difference(cut)
        pieces=list(shape.geoms) if hasattr(shape, 'geoms') else [shape]
        for piece in pieces:
            if not piece.is_empty: items.append((piece, on_layers, port))
    for e in g.j:
        if g.key(e) != net: continue
        t=e['type']
        if t in ['pcb_smtpad', 'pcb_plated_hole']:
            add(g.geometry(e), e.get('layers', [e.get('layer', 'top')]), e.get('pcb_port_id'))
        elif t == 'pcb_via':
            add(Point(e['x'],e['y']).buffer(e['outer_diameter']/2), e['layers'])
        elif t == 'pcb_trace':
            for a,b in zip(e['route'],e['route'][1:]):
                if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
                    width=min(a['width'],b['width'])
                    if width >= minimum_width-1e-6:
                        add(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(width/2), [a['layer']])
        elif t == 'pcb_copper_pour':
            shape=e['brep_shape'];coords=lambda r:[(p['x'],p['y']) for p in r['vertices']]
            add(Polygon(coords(shape['outer_ring']),[coords(r) for r in shape.get('inner_rings',[])]), [e['layer']])
    parents=list(range(len(items)))
    def root(i):
        while parents[i]!=i: parents[i]=parents[parents[i]];i=parents[i]
        return i
    for layer in layers:
        ids=[i for i,(_,ls,_) in enumerate(items) if layer in ls]
        shapes=[items[i][0] for i in ids];tree=STRtree(shapes)
        for i,s in enumerate(shapes):
            for other in tree.query(s,predicate='intersects'):
                a,b=root(ids[i]),root(ids[other])
                if a!=b: parents[b]=a
    roots=lambda port:{root(i) for i,(_,_,p) in enumerate(items) if p==port}
    return bool(roots(first['pcb_port_id']) & roots(second['pcb_port_id']))

checks=[]
def check(name, passed, **evidence):
    checks.append({'check':name,'passed':bool(passed),**evidence})

for phase,driver_pin,motor_pin,amp in [('A',24,1,'U_IA'),('B',21,3,'U_IB')]:
    # Physical driver pin assignments are resolved from the source symbol below,
    # rather than assumed from the package's viewing orientation.
    driver=next(e for e in g.j if e['type']=='pcb_smtpad' and reference(e)=='U_DRV'
                and g.sp[g.ports[e['pcb_port_id']]['source_port_id']]['name']=='OUT'+('1A' if phase=='A' else '2A'))
    shunt1,shunt2=pad('R_SHUNT_'+phase,1),pad('R_SHUNT_'+phase,2)
    motor=next(e for e in g.j if e['type']=='pcb_plated_hole' and reference(e)=='J_MOTOR'
               and g.sp[g.ports[e['pcb_port_id']]['source_port_id']]['name']==phase+'_PLUS')
    for label,start,goal in [('driver_to_shunt',driver,shunt1),('shunt_to_motor',shunt2,motor)]:
        net=g.key(start)
        check(phase+' '+label+' has a >=0.30 mm current path', connected(net,start,goal,.30))
    for label,number,target,main in [('positive',2,shunt1,driver),('negative',3,shunt2,motor)]:
        sense=pad(amp,number);net=g.key(sense)
        joins=connected(net,sense,target)
        bypass=connected(net,sense,main,cut=g.geometry(target).buffer(.10))
        check(phase+' '+label+' Kelvin pickup joins only at shunt',joins and not bypass,
              connected_to_shunt=joins,joins_main_outside_shunt=bypass)

clock_keys={k for k,n in g.nets.items() if n in ['XIN','XOUT','XTAL_OUT']}
clock_vias=[e['pcb_via_id'] for e in g.j if e['type']=='pcb_via' and g.key(e) in clock_keys]
clock_layers={q['layer'] for e in g.j if e['type']=='pcb_trace' and g.key(e) in clock_keys
              for q in e['route'] if q['route_type']=='wire'}
check('Oscillator uses top copper without vias',not clock_vias and clock_layers=={'top'},vias=clock_vias,layers=sorted(clock_layers))
report={'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'checks':checks,
        'passed':all(c['passed'] for c in checks),'fabrication_ready':False}
output=g.ROOT/'artifacts/v2/routing/functional-routing-audit.json'
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(not report['passed'])
