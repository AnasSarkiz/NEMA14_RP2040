"""Prune redundant same-net overlapping drill sites only if physical pad connectivity is unchanged."""
import sys,json,math
import verify_supplier_connectivity as g

def sig(net):
 es,rs=g.groups(net);a={}
 for e,r in zip(es,rs):
  if e.get('pcb_port_id'):a.setdefault(r,set()).add(e['pcb_port_id'])
 return sorted(sorted(v) for v in a.values())
removed=[];retained=[]
for a in list(g.j):
 if a['type']!='pcb_via' or a not in g.j:continue
 for b in list(g.j):
  if b['type']!='pcb_via' or b is a or b not in g.j:continue
  d=math.hypot(a['x']-b['x'],a['y']-b['y']);min_spacing=(a['hole_diameter']+b['hole_diameter'])/2+.1
  if d>=min_spacing-1e-6:continue
  if g.key(a)!=g.key(b):retained.append([a['pcb_via_id'],b['pcb_via_id'],d]);continue
  before=sig(g.key(b));at=g.j.index(b);g.j.remove(b)
  if sig(g.key(a))==before:removed.append({'removed_via':b['pcb_via_id'],'retained_via':a['pcb_via_id'],'centre_spacing_mm':d,'physical_pad_connectivity_unchanged':True})
  else:g.j.insert(at,b);retained.append([a['pcb_via_id'],b['pcb_via_id'],d])
g.path.write_text(json.dumps(g.j,indent=2)+'\n');out=g.ROOT/'artifacts/reference-feedback/close-drill-pruning.json';out.write_text(json.dumps({'removed_redundant_same_net_sites':removed,'remaining_close_sites':retained},indent=2)+'\n');print(json.dumps({'removed':removed,'remaining':retained}));raise SystemExit(bool(retained))
