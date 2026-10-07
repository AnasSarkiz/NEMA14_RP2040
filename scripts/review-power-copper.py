"""Widen saved power copper only where native geometry permits; never reroute.

Run before fill-ground.py. All new widths retain 0.15 mm foreign-net clearance.
The result is recorded alongside the original SES for reproducible replay.
"""
import json, copy
import verify_supplier_connectivity as g
from shapely.geometry import Point, LineString, box
from shapely.strtree import STRtree

layers = ['top', 'bottom'] if next(e for e in g.j if e['type']=='pcb_board')['num_layers']==2 else ['top','inner1','inner2','bottom']
targets = {'PD_VBUS':.60, 'A_PLUS':.45, 'A_MINUS':.45, 'B_PLUS':.45,
           'B_MINUS':.45, 'SENSE1':.45, 'SENSE2':.45, 'GND':.45,
           'DATA_VBUS':.30, 'LOGIC_IN':.30, 'V3V3':.30,
           'V1V1':.30, 'BUCK_SW':.60}
g.j[:]=[e for e in g.j if e['type']!='pcb_copper_pour']

def pieces(e, width=None):
    typ=e['type']
    if typ in ['pcb_smtpad','pcb_plated_hole']:
        for l in e.get('layers',[e.get('layer','top')]): yield l,g.geometry(e)
    elif typ=='pcb_via':
        for l in e['layers']: yield l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
    elif typ=='pcb_trace':
        for a,b in zip(e['route'],e['route'][1:]):
            if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
                yield a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer((width or max(a['width'],b['width']))/2)

fixed={l:[] for l in layers}; fixedkeys={l:[] for l in layers}
for e in g.j:
    if e['type'] in ['pcb_smtpad','pcb_plated_hole','pcb_via']:
        for l,p in pieces(e):
            if l in fixed: fixed[l].append(p); fixedkeys[l].append(g.key(e))
    elif e['type']=='pcb_hole':
        for l in layers: fixed[l].append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.10)); fixedkeys[l].append(None)
    elif e['type']=='pcb_keepout':
        c=e['center'];p=box(c['x']-e['width']/2,c['y']-e['height']/2,c['x']+e['width']/2,c['y']+e['height']/2)
        for l in e.get('layers',layers):
            if l in fixed:fixed[l].append(p);fixedkeys[l].append(None)
trees={l:STRtree(p) for l,p in fixed.items()}
traces=[e for e in g.j if e['type']=='pcb_trace'];changes=[]
for e in traces:
    name=g.nets.get(g.key(e));target=targets.get(name)
    if not target:continue
    points=[p for p in e['route'] if p['route_type']=='wire']
    if not points:continue
    old=max(p['width'] for p in points)
    if old>=target:continue
    others={l:[] for l in layers}
    for other in traces:
        if g.key(other)==g.key(e):continue
        for l,p in pieces(other):others[l].append(p)
    ot={l:STRtree(p) for l,p in others.items()}
    def safe(w):
        for l,p in pieces(e,w):
            if not box(-17.25,-17.25,17.25,17.25).covers(p):return False
            for i in trees[l].query(p.buffer(.1505)):
                if fixedkeys[l][i]!=g.key(e) and p.distance(fixed[l][i])<.1505:return False
            for i in ot[l].query(p.buffer(.1505)):
                if p.distance(others[l][i])<.1505:return False
        return True
    if safe(target):width=target
    else:
        lo,hi=old,target
        for _ in range(12):
            mid=(lo+hi)/2
            if safe(mid):lo=mid
            else:hi=mid
        width=int(lo*1000)/1000
    if width<=old+.009:continue
    before=copy.deepcopy(e)
    for p in points:p['width']=width
    changes.append({'id':e['pcb_trace_id'],'net':name,'oldWidthMm':old,'newWidthMm':width,'before':before,'after':copy.deepcopy(e)})
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
(g.ROOT/'artifacts/power-copper-adjustments.json').write_text(json.dumps({'clearanceMm':.15,'targetsMm':targets,'changes':changes},indent=2)+'\n')
print('Widened',len(changes),'saved trace records without changing their paths')
