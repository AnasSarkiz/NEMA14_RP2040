"""Reapply reviewed ground, filling the changed motor bay and cutting new copper.
All non-motor source geometry is immutable. No blanket global reroute/refill.
"""
import json,pathlib,subprocess,hashlib
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
import verify_supplier_connectivity as g
root=g.ROOT;path=g.path;j=g.j
start='97d4248' if root.name=='NEMA14_RP2040' else '2d69fc4'
old=json.loads(subprocess.check_output(['git','show',start+':artifacts/board.circuit.json'],cwd=root))
net=next(e for e in j if e['type']=='source_net' and e['name']=='GND');key=net['subcircuit_connectivity_map_key']
layers=['top','bottom'] if next(e for e in j if e['type']=='pcb_board')['num_layers']==2 else ['top','inner1','inner2','bottom']
original=[e for e in old if e['type']=='pcb_copper_pour' and e.get('subcircuit_connectivity_map_key')==key]
def shape(e):
    b=e['brep_shape'];coords=lambda r:[(p['x'],p['y']) for p in r['vertices']]
    return Polygon(coords(b['outer_ring']),[coords(r) for r in b.get('inner_rings',[])])
def ring(r):return {'vertices':[{'x':x,'y':y} for x,y in list(r.coords)[:-1]]}
records=[];delta=[]
for layer in layers:
    prev=unary_union([shape(e) for e in original if e['layer']==layer]);candidate=prev.union(box(-8,-17.15,8,-14)).union(box(-17.15,7.2,17.15,17.15))
    cuts=[]
    for e in j:
        typ=e['type'];foreign=g.key(e)!=key
        if typ in ['pcb_smtpad','pcb_plated_hole'] and foreign and layer in e.get('layers',[e.get('layer','top')]):cuts.append(g.geometry(e).buffer(.20,quad_segs=32))
        elif typ=='pcb_via' and foreign and layer in e['layers']:cuts.append(Point(e['x'],e['y']).buffer(e['outer_diameter']/2+.20,quad_segs=32))
        elif typ=='pcb_trace' and foreign:
            for a,b in zip(e['route'],e['route'][1:]):
                if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']==layer:cuts.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2+.20,quad_segs=32))
        elif typ=='pcb_copper_pour' and foreign and e['layer']==layer:cuts.append(shape(e).buffer(.20,quad_segs=32))
        elif typ=='pcb_keepout':
            c=e['center'];cuts.append(Point(c['x'],c['y']).buffer(e['radius'],quad_segs=64) if e.get('shape')=='circle' else box(c['x']-e['width']/2,c['y']-e['height']/2,c['x']+e['width']/2,c['y']+e['height']/2))
    candidate=candidate.difference(unary_union(cuts));template=next(e for e in original if e['layer']==layer)
    pieces=list(candidate.geoms) if hasattr(candidate,'geoms') else [candidate]
    for i,p in enumerate(pieces):
        if p.is_empty or p.area<.01:continue
        # Boolean arc intersections can produce ~1e-14 mm zero-length edges.
        # Normalize at 0.00001 mm (10 nm), below the 0.0002 mm CAM tolerance;
        # otherwise the official connectivity library divides by zero.
        p=orient(p.simplify(.00001,preserve_topology=True),1)
        assert p.is_valid
        records.append({**template,'pcb_copper_pour_id':f'service_gnd_{layer}_{i}','brep_shape':{'outer_ring':ring(p.exterior),'inner_rings':[ring(r) for r in p.interiors]}})
    delta.append({'layer':layer,'changedAreaMm2':candidate.symmetric_difference(prev).area,'usbRegionChangedAreaMm2':candidate.symmetric_difference(prev).intersection(box(-11,7,11,17.5)).area})
j[:]=[e for e in j if e['type']!='pcb_copper_pour' or g.key(e)!=key]+records
elems,roots=g.groups(key);anchored={r for e,r in zip(elems,roots) if e.get('pcb_port_id')}
drop={e['pcb_copper_pour_id'] for e,r in zip(elems,roots) if e['type']=='pcb_copper_pour' and r not in anchored}
j[:]=[e for e in j if e.get('pcb_copper_pour_id') not in drop]
# Obsolete via fragments of motor tails are removed only if no actual terminal
# belongs to their connected group. This is physical copper analysis, not net naming.
phase={e['subcircuit_connectivity_map_key'] for e in j if e['type']=='source_net' and e['name'] in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS']}
orphan=set()
for k in phase:
    elems,roots=g.groups(k);anchored={r for e,r in zip(elems,roots) if e.get('pcb_port_id')}
    orphan|={e[e['type']+'_id'] for e,r in zip(elems,roots) if e['type'] in ['pcb_trace','pcb_via'] and r not in anchored}
j[:]=[e for e in j if e.get(e['type']+'_id') not in orphan]
path.write_text(json.dumps(j,indent=2)+'\n')
(root/'artifacts/validation/service-ground-review.json').write_text(json.dumps({'baselineCommit':start,'layerChanges':delta,'floatingPourFragmentsRemoved':sorted(drop),'obsoleteMotorCopperFragmentsRemoved':sorted(orphan),'allCopperConnectivityStillRequiresIndependentAudit':True,'boardSha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps(delta));print('Removed',len(drop),'floating pours and',len(orphan),'obsolete motor fragments.')
