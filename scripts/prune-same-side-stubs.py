"""Remove reported obsolete copper branches only when live-pad connectivity is unchanged."""
import json,sys
import verify_supplier_connectivity as g

errors=json.loads((g.ROOT/'artifacts/drc-report.json').read_text())['errors']
ids={e['pcb_trace_id'] for e in errors if 'dangling endpoint' in e.get('message','')}
def signature(net):
    elems,roots=g.groups(net);islands={}
    for e,r in zip(elems,roots):
        if e.get('pcb_port_id'):islands.setdefault(r,set()).add(e['pcb_port_id'])
    return sorted(sorted(v) for v in islands.values())
removed=[];retained=[]
for trace_id in sorted(ids):
    if trace_id.startswith(("usb_","oscillator_","reviewed_local_critical_")):continue
    if "--preserve-review-escapes" in sys.argv and trace_id.startswith(("reviewed_local_","oscillator_","usb_")):continue
    e=next((x for x in g.j if x.get('pcb_trace_id')==trace_id),None)
    if e is None:continue
    net=g.key(e);before=signature(net);i=g.j.index(e);g.j.pop(i)
    if signature(net)==before:removed.append(trace_id)
    else:g.j.insert(i,e);retained.append(trace_id)
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
p=g.ROOT/'artifacts/same-side-pruned-stubs.json'
records=json.loads(p.read_text()) if p.exists() else []
records.append({'removed_trace_ids':removed,'retained_live_traces':retained,'live_pad_connectivity_unchanged':True})
p.write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records[-1]))
