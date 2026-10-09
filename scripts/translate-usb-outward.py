"""Move both complete native ports outward0.4mm; extend exact pad endpoint tails.
No rescaling of supplier land patterns. Functional labels regenerated from source.
"""
import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1];p=root/'artifacts/board.circuit.json';j=json.loads(p.read_text());fresh=json.loads((root/'artifacts/final-source.circuit.json').read_text());src={e['source_component_id']:e for e in j if e['type']=='source_component'};ids={e['pcb_component_id']for e in j if e['type']=='pcb_component'and src[e['source_component_id']]['name']in['J_PD','J_DATA']};old={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'and e['pcb_component_id']in ids};new={e['pcb_port_id']:e for e in fresh if e['type']=='pcb_port'and e['pcb_component_id']in ids};assert old.keys()==new.keys()
poses=[]
for k,e in old.items():
 assert abs(new[k]['x']-e['x'])<1e-6 and abs(new[k]['y']-e['y']-.4)<1e-6
 poses.append((e['x'],e['y'],new[k]['y']))
changed=[]
for e in j:
 if e['type']!='pcb_trace':continue
 for q in e['route']:
  if q['route_type']!='wire':continue
  hits=[v for v in poses if abs(q['x']-v[0])<1e-6 and abs(q['y']-v[1])<1e-6]
  if hits:q['y']=hits[0][2];changed.append(e['pcb_trace_id'])
j=[e for e in j if e['type'].startswith('pcb_')and e.get('pcb_component_id')not in ids and e['type']!='pcb_silkscreen_text'and not e['type'].endswith(('_error','_warning'))]+[e for e in fresh if (not e['type'].startswith('pcb_')or e.get('pcb_component_id')in ids or e['type']=='pcb_silkscreen_text')and not e['type'].endswith(('_error','_warning'))]
p.write_text(json.dumps(j,indent=2)+'\n');(root/'artifacts/validation/usb-outward-overhang.json').write_text(json.dumps({'supplierFootprintTranslationOnly':True,'outward_mm':.4,'mouthY_mm':17.9,'PCB_edge_nominal_y_mm':17.5,'extendedNativeEndpoints':sorted(set(changed)),'sourceSha256':hashlib.sha256((root/'artifacts/final-source.circuit.json').read_bytes()).hexdigest()},indent=2)+'\n');print('Extended',len(changed),'USB pad endpoints')
