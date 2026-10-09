"""Remove obsolete tail stubs at the actual new branch points; keep live copper."""
import json,pathlib,math
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json';j=json.loads(path.read_text())
phase={e['subcircuit_connectivity_map_key']:e['name'] for e in j if e['type']=='source_net' and e['name'] in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS']}
new={k:next(e for e in reversed(j) if e['type']=='pcb_trace' and e.get('subcircuit_connectivity_map_key')==k) for k in phase};changes=[]
for k,t in new.items():
    oldid=t['pcb_trace_id'];t['pcb_trace_id']='service_motor_repair_'+phase[k]
    start=t['route'][0]
    for old in j:
        if old is t:continue
        if old['type']=='pcb_trace' and old.get('subcircuit_connectivity_map_key')==k:
            match=next((i for i,p in enumerate(old['route']) if p['route_type']=='wire' and p.get('layer')==start.get('layer') and math.hypot(p['x']-start['x'],p['y']-start['y'])<1e-8),None)
            if match is not None and match<len(old['route'])-1:
                changes.append({'trace':old['pcb_trace_id'],'removedStubPoints':len(old['route'])-match-1});old['route']=old['route'][:match+1]
    # Only repair-owned vias after this newly appended trace are renamed.
    index=j.index(t)
    for e in j[index+1:]:
        if e['type']=='pcb_via' and e.get('pcb_trace_id')==oldid:
            e['pcb_trace_id']=t['pcb_trace_id'];e['pcb_via_id']='service_'+e['pcb_via_id']
j=[e for e in j if e['type']!='pcb_trace' or len(e['route'])>=2]
ids=[e.get(e['type']+'_id') for e in j if e['type'] in ['pcb_trace','pcb_via']]
assert len(ids)==len(set(ids)),'Duplicate copper ID'
path.write_text(json.dumps(j,indent=2)+'\n')
(root/'artifacts/validation/motor-stub-removal.json').write_text(json.dumps({'actualBranchPointsUsed':True,'changes':changes,'copperIdsUnique':True},indent=2)+'\n')
print(changes)
