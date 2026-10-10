"""Restore unique identities for geometrically distinct inherited seed barrels."""
import json,pathlib,collections
from diagnostics_baseline import baseline_bytes
r=pathlib.Path(__file__).resolve().parents[1];p=r/'artifacts/board.circuit.json';j=json.loads(p.read_text());b=json.loads(baseline_bytes('artifacts/board.circuit.json'));old={e['pcb_via_id']:(e['x'],e['y'])for e in b if e['type']=='pcb_via'};counts=collections.Counter(e['pcb_via_id']for e in j if e['type']=='pcb_via');changes=[]
for e in j:
 if e['type']=='pcb_via'and counts[e['pcb_via_id']]>1 and old.get(e['pcb_via_id'])!=(e['x'],e['y']):
  a=e['pcb_via_id'];e['pcb_via_id']='diagnostics_seed_via_'+str(e['x'])+'_'+str(e['y']);changes.append({'old':a,'new':e['pcb_via_id'],'x':e['x'],'y':e['y']})
assert len({e['pcb_via_id']for e in j if e['type']=='pcb_via'})==sum(e['type']=='pcb_via'for e in j)
p.write_text(json.dumps(j,indent=2)+'\n');(r/'artifacts/diagnostics/seed-identity-repair.json').write_text(json.dumps(changes,indent=2)+'\n');print('Identity-only repairs',len(changes))
