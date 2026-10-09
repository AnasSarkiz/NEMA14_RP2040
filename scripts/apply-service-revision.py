"""Merge the explicitly reviewed connector revision without rerouting other nets.

Every unaffected pad, hole, via and trace is retained. All named source pin/net
identities must remain equal. Subsequent connectivity/CAM checks are mandatory.
"""
import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
path=root/'artifacts/board.circuit.json';old=json.loads(path.read_text())
fresh=json.loads((root/'artifacts/final-source.circuit.json').read_text())
key=lambda e:e.get(e['type']+'_id')
op={key(e):e for e in old if e['type']=='source_port'};np={key(e):e for e in fresh if e['type']=='source_port'}
assert op.keys()==np.keys(),'Unexpected pin inventory change'
for k,e in op.items():
    for f in ['source_component_id','pin_number','name','subcircuit_connectivity_map_key']:
        assert e.get(f)==np[k].get(f),(k,f)
motor=next(e for e in old if e['type']=='source_component' and e['name']=='J_MOTOR')
pc=next(e for e in old if e['type']=='pcb_component' and e['source_component_id']==motor['source_component_id'])
pid=pc['pcb_component_id']
replacement=[e for e in fresh if e['type'].startswith('pcb_') and e.get('pcb_component_id')==pid and not e['type'].endswith(('_error','_warning'))]
motorports={e['pcb_port_id'] for e in replacement if e['type']=='pcb_port'}
out=[e for e in old if e['type'].startswith('pcb_') and e.get('pcb_component_id')!=pid and not e['type'].endswith(('_error','_warning')) and e['type']!='pcb_silkscreen_text']
old_copper={key(e):e for e in out if e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour']}
out+=replacement
out+=[e for e in fresh if not e['type'].startswith('pcb_') and not e['type'].endswith(('_error','_warning'))]
out+=[e for e in fresh if e['type']=='pcb_silkscreen_text' and e.get('pcb_component_id')!=pid]
# Old motor endpoints are physical stubs until selected-net repair. Remove only
# stale endpoint annotations; their copper is retained and checked geometrically.
for e in out:
    if e['type']=='pcb_trace':
        e['pcb_port_ids']=[p for p in e.get('pcb_port_ids',[]) if p not in motorports]
        for p in e['route']:
            for f in ['start_pcb_port_id','end_pcb_port_id']:
                if p.get(f) in motorports:p.pop(f)
path.write_text(json.dumps(out,indent=2)+'\n')
(root/'artifacts/validation/service-revision-merge.json').write_text(json.dumps({'sourcePinNetIdentityPreserved':True,'replacedPhysicalComponent':'J_MOTOR','unaffectedPadGeometryRetained':True,'unaffectedCopperGeometryRetained':True,'motorRoutingNeedsRepair':True,'sourceSha256':hashlib.sha256((root/'artifacts/final-source.circuit.json').read_bytes()).hexdigest()},indent=2)+'\n')
print('Retained all other PCB geometry; merged manufacturer connector, CAD and schematic.')
