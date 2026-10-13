"""Independently compare every functional terminal/net to the published baseline."""
import json,pathlib,hashlib,collections
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json';old=json.loads((root/'artifacts/top-assembly/baseline.circuit.json').read_text());new=json.loads(path.read_text());errors=[]
def circuit(j):
 s={e['source_component_id']:e for e in j if e['type']=='source_component'};rp=any(e.get('manufacturer_part_number')=='RP2040' for e in s.values());groups=collections.defaultdict(set);nc=set();pins={};debug={'VDD':'TP_3V3','GND':'TP_GND','SWCLK':'TP_SWCLK','SWDIO':'TP_SWDIO','RUN':'TP_RUN','DCK':'TP_DCK','DIO':'TP_DIO'}
 for e in j:
  if e['type']!='source_port':continue
  c=s[e['source_component_id']];name,role=c['name'],e['name']
  if name=='J_DEBUG':name,role=debug[role],'pin1'
  elif name=='J_BOOT':name,role=('TP_BOOT' if role=='BOOT' else 'TP_BOOT_GND' if rp else 'TP_BOOT_USB_DP'),'pin1'
  elif name in ['J_PD','J_DATA']:role=role.replace('DN','DM')
  if name=='J_MOTOR' and role in ['MOUNT1','MOUNT2']:
   if e.get('subcircuit_connectivity_map_key'):errors.append('Connected mechanical JST pad '+role)
   continue
  terminal=name+'.'+role;pins[terminal]=e['pin_number']
  k=e.get('subcircuit_connectivity_map_key')
  if k:groups[k].add(terminal)
  else:nc.add(terminal)
 return s,set(map(frozenset,groups.values())),nc,pins
os,og,on,op=circuit(old);ns,ng,nn,np=circuit(new)
if og!=ng:errors.append({'functional_net_changes':{'removed':[sorted(s) for s in og-ng],'added':[sorted(s) for s in ng-og]}})
if on!=nn:errors.append({'NC_changes':{'removed':sorted(on-nn),'added':sorted(nn-on)}})
oldbyname={e['name']:e for e in os.values()};newbyname={e['name']:e for e in ns.values()}
for n,c in oldbyname.items():
 if n in ['J_DEBUG','J_BOOT']:continue
 q=newbyname.get(n)
 if not q:errors.append('Missing component '+n);continue
 for key in ['resistance','capacitance','inductance','max_voltage_rating','tolerance','frequency']:
  if c.get(key)!=q.get(key):errors.append('Changed functional value '+n+'.'+key)
 if n!='J_MOTOR' and c.get('manufacturer_part_number')!=q.get('manufacturer_part_number'):errors.append('Changed fitted identity '+n)
 for terminal,pin in op.items():
  if terminal.startswith(n+'.') and pin!=np.get(terminal):errors.append('Changed physical pin number '+terminal)
pcs=[e for e in new if e['type']=='pcb_component'];bare={e['source_component_id'] for e in ns.values() if e['ftype']=='simple_test_point'}
for c in pcs:
 if c['layer']!='top':errors.append('Bottom-side population '+ns[c['source_component_id']]['name'])
 if c['source_component_id'] in bare:
  pads=[e for e in new if e['type']=='pcb_smtpad' and e['pcb_component_id']==c['pcb_component_id']]
  if len(pads)!=1 or pads[0]['shape']!='circle' or abs(pads[0]['radius']-.55)>1e-8:errors.append('Nonstandard bare test point '+ns[c['source_component_id']]['name'])
  if any(e['type']=='pcb_solder_paste' and e.get('pcb_component_id')==c['pcb_component_id'] for e in new):errors.append('Paste on bare test point')
report={'passed':not errors,'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'functional_terminal_count':len(np),'functional_net_groups_compared':len(ng),'functional_nets_preserved':og==ng,'NC_roles_preserved':on==nn,'fitted_components':len(pcs)-len(bare),'bare_top_test_points':len(bare),'assembly_face':'top','USB_housing_width_mm':10,'USB_housing_pitch_mm':12.4,'USB_nominal_housing_gap_mm':2.4,'rear_motor_compatibility_verified':False,'errors':errors}
(root/'artifacts/top-assembly/functional-preservation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
