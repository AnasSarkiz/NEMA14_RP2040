"""Release a specified local fanout before moving its via to a new legal site.

Every affected net remains physically open until the router reconnects it.
Supplier pads, pin assignments, USB, oscillator and thermal copper stay fixed.
"""
import json,sys
from v2_route_io import g

port=next(q.split('=',1)[1] for q in sys.argv if q.startswith('--port='))
selected=[e for e in g.j if e['type']=='pcb_trace' and e['pcb_trace_id'].startswith('v2_escape_')
          and port in e.get('pcb_port_ids',[])]
assert selected,'No explicit local fanout for '+port
keys={g.key(t) for t in selected}
sites={(p['x'],p['y']) for t in selected for p in t['route'] if p['route_type']=='via'}
dead=[e for e in g.j if e['type']=='pcb_via' and g.key(e) in keys
      and any(abs(e['x']-x)<1e-6 and abs(e['y']-y)<1e-6 for x,y in sites)]
removed={e[e['type']+'_id'] for e in selected+dead}
for e in g.j:
    if e['type']!='pcb_trace':continue
    if any(any(abs(p['x']-v['x'])<1e-6 and abs(p['y']-v['y'])<1e-6 for p in e['route']) for v in dead):
        assert not e['pcb_trace_id'].startswith(('usb_','oscillator_','v2_thermal_'))
        removed.add(e['pcb_trace_id'])
g.j[:]=[e for e in g.j if e['type']!='pcb_copper_pour' and e.get(e['type']+'_id') not in removed]
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
path=g.ROOT/'artifacts/v2/routing/escape-relocations.json'
history=json.loads(path.read_text()) if path.exists() else []
row={'port':port,'removed':sorted(removed),'supplier_pads_and_source_nets_unchanged':True}
history.append(row);path.write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(row))
