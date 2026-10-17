"""Transfer the CH224A source change onto saved copper without global autorouting.

Run after npm run source:check. The initial Git commit is the frozen v1.12.2
baseline. Only the old PD straps and any copper conflicting with the new CFG
resistor are removed; existing mechanical geometry and placements are retained.
"""
import copy, hashlib, json, pathlib, subprocess, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
baseline_commit = subprocess.check_output(['git','rev-list','--max-parents=0','HEAD'],cwd=ROOT,text=True).strip()
baseline_bytes = subprocess.check_output(['git','show',baseline_commit+':index.circuit.json'],cwd=ROOT)
old = json.loads(baseline_bytes)
fresh = json.loads((ROOT/'artifacts/final-source.circuit.json').read_text())
assert not any(e['type'].endswith('_error') for e in fresh)

def index(records, typ): return {e[typ+'_id']: e for e in records if e['type']==typ}
os, ns = index(old,'source_component'), index(fresh,'source_component')
op, np = index(old,'source_port'), index(fresh,'source_port')
oc, nc = index(old,'pcb_component'), index(fresh,'pcb_component')
opp, npp = index(old,'pcb_port'), index(fresh,'pcb_port')
on = {e['name']:e for e in old if e['type']=='source_net'}
nn = {e['name']:e for e in fresh if e['type']=='source_net'}
remap = {}
oldnames = {v['name']:v for v in os.values()}
for ident, c in ns.items():
    if c['name'] in oldnames: remap[ident] = oldnames[c['name']]['source_component_id']
oldroles = {(os[p['source_component_id']]['name'],p['pin_number']):p for p in op.values()}
for ident,p in np.items():
    prev=oldroles.get((ns[p['source_component_id']]['name'],p['pin_number']))
    if prev: remap[ident]=prev['source_port_id']
for name,net in nn.items():
    prev=on.get('PD_VDD' if name=='PD_VHV' else name)
    if prev:
        remap[net['source_net_id']]=prev['source_net_id']
        remap[net['subcircuit_connectivity_map_key']]=prev['subcircuit_connectivity_map_key']
    else:
        remap[net['subcircuit_connectivity_map_key']]='ch224a_'+name.lower()
oldcompnames = {os[c['source_component_id']]['name']:c for c in oc.values()}
for ident,c in nc.items():
    prev=oldcompnames.get(ns[c['source_component_id']]['name'])
    if prev: remap[ident]=prev['pcb_component_id']
oldppbysp={p['source_port_id']:p for p in opp.values()}
for ident,p in npp.items():
    prev=oldppbysp.get(remap.get(p['source_port_id'],p['source_port_id']))
    if prev: remap[ident]=prev['pcb_port_id']

def reid(v):
    if isinstance(v,str):return remap.get(v,v)
    if isinstance(v,list):return [reid(x) for x in v]
    if isinstance(v,dict):return {k:reid(x) for k,x in v.items()}
    return v

# Keep old source-trace identities whenever the actual terminal set is unchanged.
oldtraces={frozenset(e['connected_source_port_ids']):e for e in old if e['type']=='source_trace'}
used_trace_ids=set()
for t in fresh:
    if t['type']!='source_trace':continue
    prev=oldtraces.get(frozenset(reid(t['connected_source_port_ids'])))
    dest=prev['source_trace_id'] if prev else 'ch224a_'+t['source_trace_id']
    assert dest not in used_trace_ids
    used_trace_ids.add(dest);remap[t['source_trace_id']]=dest
fresh=reid(fresh)
fresh_sources=index(fresh,'source_component');fresh_ports=index(fresh,'source_port')
fresh_copper_ports=index(fresh,'pcb_port')
newres=next(c for c in fresh_sources.values() if c['name']=='R_PD_CFG')
newrespc=next(c for c in fresh if c['type']=='pcb_component' and c['source_component_id']==newres['source_component_id'])
newrespcid=newrespc['pcb_component_id']
assert all(fresh_sources[c['source_component_id']]['name']==os[c['source_component_id']]['name'] for c in oc.values())

# Validate the intended electrical delta against every physical pin before merging.
oldnetnames={e['subcircuit_connectivity_map_key']:e['name'] for e in old if e['type']=='source_net'}
newnetnames={e['subcircuit_connectivity_map_key']:e['name'] for e in fresh if e['type']=='source_net'}
electrical=[]
for ident,p in op.items():
    q=fresh_ports[ident];ref=os[p['source_component_id']]['name'];pin=p['pin_number']
    before=oldnetnames.get(p.get('subcircuit_connectivity_map_key'))
    after=newnetnames.get(q.get('subcircuit_connectivity_map_key'))
    if before=='PD_VDD':before='PD_VHV'
    if before!=after:
        assert ref=='U_PD' and pin in [2,3,9],(ref,pin,before,after)
        electrical.append({'reference':ref,'pin':pin,'before':before,'after':after})

pcb=[copy.deepcopy(e) for e in old if e['type'].startswith('pcb_') and not e['type'].endswith(('_error','_warning'))]
for e in pcb:
    if e['type']=='pcb_port':
        q=fresh_copper_ports[e['pcb_port_id']]
        for field in ['subcircuit_connectivity_map_key','port_hints']:
            if field in q:e[field]=q[field]
            else:e.pop(field,None)
pcb.extend(e for e in fresh if e['type'].startswith('pcb_') and e.get('pcb_component_id')==newrespcid and not e['type'].endswith(('_error','_warning')))
source=[e for e in fresh if not e['type'].startswith('pcb_') and not e['type'].endswith(('_error','_warning'))]
j=source+pcb
# Old copper can keep its geometric identity, but must reference valid source traces.
sts=[e for e in j if e['type']=='source_trace']
valid={e['source_trace_id'] for e in sts}
netkeys={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}
for e in pcb:
    if e['type'] not in ['pcb_trace','pcb_via']:continue
    key=e.get('subcircuit_connectivity_map_key')
    if e.get('source_trace_id') not in valid:
        candidates=[s for s in sts if s.get('subcircuit_connectivity_map_key')==key]
        assert candidates,key
        actual={opp[p]['source_port_id'] for p in e.get('pcb_port_ids',[]) if p in opp}
        e['source_trace_id']=max(candidates,key=lambda s:len(actual&set(s['connected_source_port_ids'])))['source_trace_id']
pd=next(c for c in os.values() if c['name']=='U_PD')
pdports={p['pin_number']:p for p in op.values() if p['source_component_id']==pd['source_component_id']}
pdpp={pin:oldppbysp[p['source_port_id']]['pcb_port_id'] for pin,p in pdports.items()}
removed=[]
for e in list(j):
    if e.get('pcb_via_id')=='reviewed_local_U_PD_CFG1_via':
        removed.append(e['pcb_via_id']);j.remove(e);continue
    if e['type']!='pcb_trace':continue
    # Pin 2/3 strap ladder is no longer used. Pin 9 must cease being grounded.
    hit=bool(set(e.get('pcb_port_ids',[]))&{pdpp[2],pdpp[3]}) or e['pcb_trace_id']=='reviewed_local_U_PD_CFG1'
    # The CH32 ladder's pin-1 branch ends on the removed pin-2 junction.
    if ROOT.name.endswith('CH32X035G8U6') and e['pcb_trace_id']=='review_baseline_review_baseline_freerouted_trace_112_run_0_run_0':hit=True
    if hit:removed.append(e['pcb_trace_id']);j.remove(e)

out=ROOT/'artifacts/ch224a-migration';out.mkdir(exist_ok=True)
(ROOT/'artifacts/board.circuit.json').write_text(json.dumps(j,indent=2)+'\n')
(out/'transfer.json').write_text(json.dumps({'baseline_commit':baseline_commit,'baseline_board_sha256':hashlib.sha256(baseline_bytes).hexdigest(),'electrical_pin_changes':electrical,'removed_old_strap_traces':removed,'new_resistor':newrespc,'requires_routing_and_validation':True},indent=2)+'\n')
print(ROOT.name,'removed',len(removed),'old strap traces; all existing placements retained.')
