"""Merge widened USB/native support poses, preserve all other source connectivity.
Trim only selected USB tails above Y9.3; preserve accepted motor/MCU copper.
"""
import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json';j=json.loads(path.read_text());fresh=json.loads((root/'artifacts/final-source.circuit.json').read_text());byname={e['name']:e for e in j if e['type']=='source_component'};ids={e['pcb_component_id'] for e in j if e['type']=='pcb_component' and e['source_component_id']in[byname[n]['source_component_id']for n in ['J_PD','J_DATA','J_MOTOR','R_CC2','R_SLEEP']]}
old={e['source_port_id']:e for e in j if e['type']=='source_port'};new={e['source_port_id']:e for e in fresh if e['type']=='source_port'};assert old.keys()==new.keys()
for k in old:
 for f in ['source_component_id','pin_number','name','subcircuit_connectivity_map_key']:assert old[k].get(f)==new[k].get(f),(k,f)
removed=[];out=[];globaltypes=['pcb_hole','pcb_keepout','pcb_silkscreen_text','pcb_silkscreen_circle'];usb_nets={'PD_VBUS','DATA_VBUS','USB_DP','USB_DM','PD_CC1','PD_CC2','DATA_CC1','DATA_CC2','GND','SLEEP'};nets={e['subcircuit_connectivity_map_key']:e['name']for e in j if e['type']=='source_net'}
for e in j:
 if not e['type'].startswith('pcb_') or e['type'].endswith(('_error','_warning')):continue
 if e.get('pcb_component_id')in ids or e['type']in globaltypes:continue
 name=nets.get(e.get('subcircuit_connectivity_map_key'))
 if e['type']=='pcb_copper_pour' and name=='GND':continue
 if e['type']=='pcb_via' and name in usb_nets and e['y']>9.3:continue
 if e['type']=='pcb_trace' and name in usb_nets:
  pieces=[];piece=[]
  for p in e['route']:
   if p['y']>9.3:
    if len(piece)>=2:pieces.append(piece)
    piece=[]
   else:piece.append(p)
  if len(piece)>=2:pieces.append(piece)
  if len(pieces)==1 and pieces[0]==e['route']:out.append(e);continue
  removed.append({'trace':e['pcb_trace_id'],'before_points':len(e['route']),'retained_points':sum(len(p)for p in pieces)})
  for i,r in enumerate(pieces):
   for p in r:
    p.pop('start_pcb_port_id',None);p.pop('end_pcb_port_id',None)
   out.append({**e,'pcb_trace_id':e['pcb_trace_id']+f'_usbtrim_{i}','route':r,'pcb_port_ids':[]})
  continue
 out.append(e)
out += [e for e in fresh if (not e['type'].startswith('pcb_') or e.get('pcb_component_id')in ids or e['type']in globaltypes) and not e['type'].endswith(('_error','_warning'))]
path.write_text(json.dumps(out,indent=2)+'\n');(root/'artifacts/validation/usb-spacing-revision.json').write_text(json.dumps({'sourcePinNetIdentityPreserved':True,'USB_centers_x_mm':[-7,7],'USB_mouth_y_mm':17.5,'PCB_support_centers_mm':[[-13,-13],[-14.8,13],[13,-13],[14.8,13]],'motor_finished_holes_mm':.75,'trim_y_mm':9.3,'trimmed_traces':removed,'selected_nets_need_repair':sorted(usb_nets)},indent=2)+'\n');print('Merged exact poses; trimmed',len(removed),'USB-tail traces.')
