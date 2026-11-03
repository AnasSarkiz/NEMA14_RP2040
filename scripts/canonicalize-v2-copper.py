"""Represent each trace as same-layer wire runs and retain every real PCB via.

This is the same explicit-barrel representation used by the SES importer.
Every original physical wire segment and all physical pad partitions must
remain identical. Trace annotations cannot substitute for a plated barrel.
"""
import hashlib,json
from collections import defaultdict
from v2_route_io import g

def segments():
    return sorted((g.key(t),a['layer'],a['x'],a['y'],b['x'],b['y'],a['width'],b['width'])
                  for t in g.j if t['type']=='pcb_trace' for a,b in zip(t['route'],t['route'][1:])
                  if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'])
def partitions():
    result={}
    for net in g.nets:
        elements,roots=g.groups(net);islands=defaultdict(set)
        for e,r in zip(elements,roots):
            if e.get('pcb_port_id'):islands[r].add(e['pcb_port_id'])
        result[net]=sorted(sorted(v) for v in islands.values())
    return result
old_segments=segments();old_partitions=partitions()
old_sha=hashlib.sha256(g.path.read_bytes()).hexdigest()
used={e.get('pcb_trace_id') for e in g.j if e['type']=='pcb_trace'}
result=[];changes=[]
for trace in g.j:
    if trace['type']!='pcb_trace':result.append(trace);continue
    runs=[];run=[]
    for q in trace['route']:
        if q['route_type']!='wire':
            if len(run)>1:runs.append(run)
            run=[];continue
        if run and q['layer']!=run[-1]['layer']:
            if len(run)>1:runs.append(run)
            run=[]
        run.append(q)
    if len(run)>1:runs.append(run)
    if len(runs)==1 and runs[0]==trace['route']:result.append(trace);continue
    ids=[]
    for i,run in enumerate(runs):
        uid=trace['pcb_trace_id'] if i==0 else trace['pcb_trace_id']+'_run_'+str(i)
        if i:
            while uid in used:uid+='_r'
            used.add(uid)
        result.append({**trace,'pcb_trace_id':uid,'route':run,'pcb_port_ids':[]});ids.append(uid)
    changes.append({'old_trace':trace['pcb_trace_id'],'same_layer_runs':ids})
g.j[:]=result
assert segments()==old_segments,'Physical wire geometry changed'
assert partitions()==old_partitions,'Physical pad connectivity changed'
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
report={'before_sha256':old_sha,'after_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),
        'physical_wire_segments_unchanged':len(old_segments),'pad_partitions_unchanged':True,
        'real_barrels_unchanged':sum(e['type']=='pcb_via' for e in g.j),'changes':changes}
(g.ROOT/'artifacts/v2/routing/copper-representation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='changes'}))
