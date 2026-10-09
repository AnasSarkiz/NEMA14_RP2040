"""Clear obsolete upper-bay traces before repairing widened USB ports.
Retain all copper below Y7.2mm and all inner-layer copper; report affected nets.
"""
import json,pathlib
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json';j=json.loads(path.read_text());nets={e['subcircuit_connectivity_map_key']:e['name']for e in j if e['type']=='source_net'};out=[];changes=[];affected=set()
for e in j:
 if e['type']=='pcb_via'and e['y']>7.2:affected.add(nets.get(e.get('subcircuit_connectivity_map_key'),'GND'));continue
 if e['type']!='pcb_trace':out.append(e);continue
 # Unchanged direct BOOT/debug contacts have no named source_net. Their
 # copper is retained and independently checked, not repaired by net-name filters.
 if e.get('subcircuit_connectivity_map_key')not in nets:out.append(e);continue
 pieces=[];piece=[]
 for p in e['route']:
  if p['y']>7.2 and (p.get('layer')in['top','bottom'] or p['route_type']=='via'):
   if len(piece)>=2:pieces.append(piece)
   piece=[]
  else:piece.append(p)
 if len(piece)>=2:pieces.append(piece)
 if len(pieces)==1 and pieces[0]==e['route']:out.append(e);continue
 name=nets.get(e.get('subcircuit_connectivity_map_key'));assert name is not None
 affected.add(name);changes.append({'trace':e['pcb_trace_id'],'net':name,'before':len(e['route']),'after':sum(len(r)for r in pieces)})
 for i,r in enumerate(pieces):
  for p in r:p.pop('start_pcb_port_id',None);p.pop('end_pcb_port_id',None)
  out.append({**e,'pcb_trace_id':e['pcb_trace_id']+f'_upperbay_{i}','route':r,'pcb_port_ids':[]})
path.write_text(json.dumps(out,indent=2)+'\n');(root/'artifacts/validation/usb-upperbay-trim.json').write_text(json.dumps({'threshold_y_mm':7.2,'affected_nets':sorted(affected),'changes':changes},indent=2)+'\n');print(','.join(sorted(affected-{'GND'})))
