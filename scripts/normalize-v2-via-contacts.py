"""Reconcile redundant barrels and trace annotations without changing pad connectivity.

An annotation is never accepted as an electrical layer transition without a
real plated barrel. Added centreline brackets must be contained in existing
same-net copper, and every deletion preserves the exact physical pad islands.
"""
import copy, hashlib, json, math
from collections import defaultdict
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
import verify_supplier_connectivity as g

before_sha=hashlib.sha256(g.path.read_bytes()).hexdigest()
history=[]
def signature(net):
    elements,roots=g.groups(net);islands=defaultdict(set)
    for e,r in zip(elements,roots):
        if e.get('pcb_port_id'):islands[r].add(e['pcb_port_id'])
    return sorted(sorted(v) for v in islands.values())

def copper(net, layer):
    shapes=[]
    for e in g.j:
        if g.key(e)!=net:continue
        if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and layer in e.get('layers',[e.get('layer','top')]):shapes.append(g.geometry(e))
        elif e['type']=='pcb_via' and layer in e['layers']:shapes.append(Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
        elif e['type']=='pcb_trace':
            for a,b in zip(e['route'],e['route'][1:]):
                if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']==layer:
                    shapes.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
        elif e['type']=='pcb_copper_pour' and e['layer']==layer:
            b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']]
            shapes.append(Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]))
    return unary_union(shapes)

def bracket(trace,index,via):
    old=trace['route'];point=old[index];new=[]
    for neighbor,layer in [(old[index-1],point['from_layer']),(old[index+1],point['to_layer'])]:
        if neighbor['route_type']!='wire' or neighbor['layer']!=layer:return False
        shape=LineString([(neighbor['x'],neighbor['y']),(via['x'],via['y'])]).buffer(neighbor['width']/2)
        if shape.difference(copper(g.key(trace),layer).buffer(1e-8)).area>1e-7:return False
        new.append({'route_type':'wire','x':via['x'],'y':via['y'],'layer':layer,'width':neighbor['width']})
    marker={**point,'x':via['x'],'y':via['y'],'via_diameter':via['outer_diameter'],'via_hole_diameter':via['hole_diameter']}
    trace['route']=old[:index]+[new[0],marker,new[1]]+old[index+1:]
    return True

# All pairs currently needing consolidation are same-net ordinary signal
# barrels. A different-net pair can never be repaired by deleting a via here.
while True:
    vias=[e for e in g.j if e['type']=='pcb_via'];changed=False
    for i,a in enumerate(vias):
        for b in vias[:i]:
            gap=math.dist((a['x'],a['y']),(b['x'],b['y']))-(a['hole_diameter']+b['hole_diameter'])/2
            if gap>=.2-1e-6 or g.key(a)!=g.key(b):continue
            for remove,retain in [(a,b),(b,a)]:
                if remove['pcb_via_id'].startswith(('v2_escape_','v2_thermal_','oscillator_','usb_')):continue
                saved=copy.deepcopy(g.j);net=g.key(remove);sig=signature(net)
                g.j[:]=[e for e in g.j if e.get('pcb_via_id')!=remove['pcb_via_id']]
                if signature(net)!=sig:g.j[:]=saved;continue
                edits=[];okay=True
                for trace in list(g.j):
                    if trace['type']!='pcb_trace' or g.key(trace)!=net:continue
                    indices=[k for k,p in enumerate(trace['route']) if p['route_type']=='via' and math.dist((p['x'],p['y']),(remove['x'],remove['y']))<1e-6]
                    for k in reversed(indices):
                        if bracket(trace,k,retain):edits.append({'trace':trace['pcb_trace_id'],'retargeted_barrel':retain['pcb_via_id']});continue
                        at=g.j.index(trace);g.j.pop(at)
                        if signature(net)==sig:edits.append({'removed_obsolete_trace':trace['pcb_trace_id']});break
                        g.j.insert(at,trace);okay=False;break
                    if not okay:break
                if not okay or signature(net)!=sig:g.j[:]=saved;continue
                history.append({'removed_redundant_barrel':remove['pcb_via_id'],'retained_barrel':retain['pcb_via_id'],'edits':edits,'pad_partitions_unchanged':True})
                changed=True;break
            if changed:break
        if changed:break
    if not changed:break

# Correct exact centreline brackets around existing barrels. Do not invent
# vias for stale annotations left behind by a controlled reroute.
unresolved=[]
for trace in list(g.j):
    if trace['type']!='pcb_trace':continue
    for k in reversed([i for i,p in enumerate(trace['route']) if p['route_type']=='via']):
        p=trace['route'][k]
        via=next((v for v in g.j if v['type']=='pcb_via' and g.key(v)==g.key(trace) and math.dist((v['x'],v['y']),(p['x'],p['y']))<1e-6),None)
        if via is None:
            net=g.key(trace);sig=signature(net);at=g.j.index(trace);g.j.pop(at)
            if signature(net)==sig:
                history.append({'removed_obsolete_trace':trace['pcb_trace_id'],'orphan_annotation_mm':[p['x'],p['y']],'pad_partitions_unchanged':True});break
            g.j.insert(at,trace);unresolved.append({'trace':trace['pcb_trace_id'],'orphan_annotation_mm':[p['x'],p['y']]});continue
        if k==0 or k==len(trace['route'])-1:unresolved.append({'trace':trace['pcb_trace_id'],'unbracketed_via':via['pcb_via_id']});continue
        if all(q['route_type']=='wire' and math.dist((q['x'],q['y']),(via['x'],via['y']))<1e-8 for q in [trace['route'][k-1],trace['route'][k+1]]):continue
        sig=signature(g.key(trace));old=copy.deepcopy(trace['route'])
        if bracket(trace,k,via) and signature(g.key(trace))==sig:history.append({'trace':trace['pcb_trace_id'],'centred_brackets_at':via['pcb_via_id'],'copper_geometry_unchanged':True})
        else:trace['route']=old;unresolved.append({'trace':trace['pcb_trace_id'],'misaligned_via':via['pcb_via_id']})

g.path.write_text(json.dumps(g.j,indent=2)+'\n')
report={'before_sha256':before_sha,'after_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'repairs':history,'unresolved':unresolved}
(g.ROOT/'artifacts/v2/routing/via-contact-normalization.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'repairs':len(history),'unresolved':unresolved}))
