"""Trim obsolete copper inside native keepout setbacks; preserve real barrels.

This does not change the keepouts or relax a rule. Any newly opened pad
partition is recorded and must be routed and audited again.
"""
import hashlib,json
from shapely.geometry import Point,LineString
import verify_supplier_connectivity as g
from v2_local_rip import retained_trace_fragments

obstacles=[(layer,Point(e['center']['x'],e['center']['y']).buffer(e['radius'],quad_segs=256))
           for e in g.j if e['type']=='pcb_keepout' and not e.get('allow_traces')
           for layer in e['layers']]
used={e.get(e['type']+'_id') for e in g.j};repairs=[]
for trace in list(g.j):
    if trace['type']!='pcb_trace':continue
    bad=[]
    for a,b in zip(trace['route'],trace['route'][1:]):
        if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
        shape=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
        bad.extend(shape.distance(s) for l,s in obstacles if l==a['layer'] and shape.distance(s)<.15-1e-6)
    if not bad:continue
    assert not trace['pcb_trace_id'].startswith(('usb_','oscillator_')),'Critical trunk needs an explicit reviewed reroute'
    fragments=retained_trace_fragments(trace,obstacles,used)
    g.j.remove(trace);g.j.extend(fragments)
    repairs.append({'old_trace':trace['pcb_trace_id'],'minimum_old_gap_mm':min(bad),
                    'retained_traces':[t['pcb_trace_id'] for t in fragments]})
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
report={'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'keepout_rule_mm':.15,
        'repairs':repairs,'requires_fresh_connectivity_and_native_DRC':True}
(g.ROOT/'artifacts/v2/routing/keepout-copper-trimming.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
