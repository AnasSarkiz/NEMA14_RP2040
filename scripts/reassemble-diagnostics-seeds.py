"""Restore original record grouping without changing any seeded copper geometry."""
import json, pathlib, re, copy
root=pathlib.Path(__file__).resolve().parents[1]
path=root/'artifacts/board.circuit.json';j=json.loads(path.read_text())
from diagnostics_baseline import baseline_bytes
old=json.loads(baseline_bytes('artifacts/board.circuit.json'))
original={e['pcb_trace_id']:e for e in old if e['type']=='pcb_trace'}
groups={};rest=[]
for e in j:
    m=re.fullmatch(r'(.*)_seed_(\d+)',e.get('pcb_trace_id',''))
    if m:groups.setdefault(m[1],{})[int(m[2])]=e
    else:rest.append(e)
count=0
for name,pieces in groups.items():
    before=original[name];expected={i for i,(a,b)in enumerate(zip(before['route'],before['route'][1:]))if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']}
    if set(pieces)!=expected:
        rest.extend(pieces.values());continue
    e=copy.deepcopy(pieces[min(pieces)]);e['pcb_trace_id']=name
    route=copy.deepcopy(before['route']);portrefs={}
    for part in pieces.values():
        for p in part['route']:
            for field in ['start_pcb_port_id','end_pcb_port_id']:
                if field in p:portrefs[(p['x'],p['y'],p['layer'],field)]=p[field]
    e['pcb_port_ids']=[]
    for p in route:
        for field in ['start_pcb_port_id','end_pcb_port_id']:
            p.pop(field,None)
            if p['route_type']=='wire' and (p['x'],p['y'],p['layer'],field)in portrefs:
                p[field]=portrefs[(p['x'],p['y'],p['layer'],field)];e['pcb_port_ids'].append(p[field])
    e['route']=route;rest.append(e);count+=1
ids=[e['pcb_trace_id']for e in rest if e['type']=='pcb_trace'];assert len(ids)==len(set(ids))
path.write_text(json.dumps(rest,indent=2)+'\n');print('Restored',count,'complete baseline copper record groups; partial cuts remain explicit.')
