"""Remove exact duplicate vias and copper islands without any real connected land."""
import json
import verify_supplier_connectivity as g
records=[];seen={}
protected=('usb_','oscillator_','reviewed_local_critical_')
for e in list(g.j):
 if e['type']!='pcb_via':continue
 key=(round(e['x'],6),round(e['y'],6),e['outer_diameter'],e['hole_diameter'],tuple(e['layers']),g.key(e))
 if key in seen:g.j.remove(e);records.append({'duplicate_via_removed':e['pcb_via_id'],'kept':seen[key]})
 else:seen[key]=e['pcb_via_id']
for net in g.nets:
 elems,roots=g.groups(net);anchored={r for e,r in zip(elems,roots) if e.get('pcb_port_id')}
 trace_roots={}
 for e,r in zip(elems,roots):
  if e['type']=='pcb_trace':trace_roots.setdefault(e['pcb_trace_id'],set()).add(r);continue
  if r not in anchored and e['type'] in ['pcb_via','pcb_copper_pour'] and not e.get(e['type']+'_id','').startswith(protected):
   g.j.remove(e);records.append({'unanchored_copper_removed':e.get('pcb_via_id',e.get('pcb_copper_pour_id')),'net':g.nets[net]})
 for id,rs in trace_roots.items():
  if not rs&anchored and not id.startswith(protected):
   e=next(e for e in g.j if e.get('pcb_trace_id')==id);g.j.remove(e);records.append({'unanchored_copper_removed':id,'net':g.nets[net]})
g.path.write_text(json.dumps(g.j,indent=2)+'\n');p=g.ROOT/'artifacts/same-side-copper-cleanup.json';h=json.loads(p.read_text()) if p.exists() else [];h.extend(records);p.write_text(json.dumps(h,indent=2)+'\n');print(json.dumps(records))
