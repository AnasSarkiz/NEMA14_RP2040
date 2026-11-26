"""NEMA14 JST placement-only pin-distance screen; not copper or PI qualification."""
from pathlib import Path
import json,hashlib,math,sys
p=Path(sys.argv[1]);raw=p.read_bytes();b=json.loads(raw);root=Path(__file__).resolve().parents[1];contract=json.loads((root/'scripts/locality-contract.json').read_text())
src={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};ports={e['source_port_id']:(src[e['source_component_id']],e['name']) for e in b if e['type']=='source_port'};pos={ports[e['source_port_id']]:(e['x'],e['y']) for e in b if e['type']=='pcb_port'}
rows=[]
for e in contract:
 a,z=pos[e['a'],e['pa']],pos[e['b'],e['pb']];l1=abs(a[0]-z[0])+abs(a[1]-z[1]);euclid=math.dist(a,z)
 rows.append({**e,'distance_l1_mm':round(l1,6),'straight_distance_mm':round(euclid,6),'pass':l1<=e['limit']+1e-6})
report={'board_sha256':hashlib.sha256(raw).hexdigest(),'locality_screen_pass':all(e['pass'] for e in rows),'routed_copper_verified':False,'criteria':'Engineering placement targets, not manufacturer limits or routed length acceptance','rows':rows}
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');bad=[e for e in rows if not e['pass']]
print('NEMA14 JST locality targets:',len(rows)-len(bad),'of',len(rows),'pass')
for e in bad:print(f"{e['a']}.{e['pa']} -> {e['b']}.{e['pb']}: {e['distance_l1_mm']:.3f} mm > {e['limit']} mm")
raise SystemExit(0 if not bad else 1)
