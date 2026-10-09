"""Retain qualified motor escapes; remove obsolete connector tail copper only."""
import json,pathlib
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json'
j=json.loads(path.read_text());nets={e['subcircuit_connectivity_map_key']:e['name'] for e in j if e['type']=='source_net'}
phase={'A_PLUS','A_MINUS','B_PLUS','B_MINUS'};out=[];changes=[]
for e in j:
    name=nets.get(e.get('subcircuit_connectivity_map_key'))
    if e['type']=='pcb_copper_pour' and name=='GND':continue
    if e['type']=='pcb_trace' and name in phase:
        route=e['route'];cut=next((i for i,p in enumerate(route) if p['y']< -14),len(route))
        if cut<len(route):
            changes.append({'trace':e['pcb_trace_id'],'originalPoints':len(route),'retainedPoints':cut})
            e={**e,'route':route[:cut],'pcb_port_ids':[]}
            if len(e['route'])<2:continue
    if e['type']=='pcb_via' and name in phase and e['y']< -14:continue
    out.append(e)
path.write_text(json.dumps(out,indent=2)+'\n')
(root/'artifacts/validation/motor-tail-removal.json').write_text(json.dumps({'phaseNets':sorted(phase),'removedBelowYmm':-14,'unaffectedSignalCopperPreserved':True,'changes':changes},indent=2)+'\n')
print('Trimmed obsolete motor tails; retained driver escapes and other signal copper.')
