"""Compare real pad topology and clearance on the frozen native A/B coupons."""
from pathlib import Path
import json,importlib.util
from routing_geometry import resolve_copper_nets,pad_cut_topology,layer_copper,shared_outside_pad
spec=importlib.util.spec_from_file_location('g',Path(__file__).with_name('inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
results=[]
for stack in ['current','tagged']:
 for mode in ['authored','automatic']:
  path=Path(f'artifacts/iteration-4/compatibility/{stack}-{mode}.circuit.json');b=resolve_copper_nets(json.loads(path.read_bytes()));cu=g.inspect(path);assert cu['geometric_clearance_pass'] and cu['full_board_connectivity_pass']
  sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={(sc[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'};pads={e['pcb_port_id']:e for e in b if e['type']=='pcb_smtpad'};st={e['source_trace_id']:e.get('name') for e in b if e['type']=='source_trace'};tr={st[e['source_trace_id']]:e for e in b if e['type']=='pcb_trace'};cuts=[]
  for pole,pin in [('POS','pin1'),('NEG','pin2')]:
   sh=pp['R_SHUNT_A',pin];amp=pp['U_IA','IN_'+pole];load=pp['P_A_'+pole,'pin1'];pad=g.pad_shape(pads[sh['pcb_port_id']]);net=sp[sh['source_port_id']]['subcircuit_connectivity_map_key'];cut=pad_cut_topology(b,net,sh['pcb_port_id'],amp['pcb_port_id'],load['pcb_port_id'],pad,'top',g.pad_shape);assert cut['all_three_terminals_connected_before_cut'] and cut['actual_shunt_pad_is_required_pickup']
   shared=shared_outside_pad(layer_copper([tr['KELVIN_A_'+pole]],b,g.pad_shape),layer_copper([tr['POWER_A_'+pole]],b,g.pad_shape),pad,'top');assert shared<=1e-8;cuts.append({'pole':pole,'cut':cut,'shared_copper_outside_pad_mm2':shared})
  results.append({'stack':stack,'mode':mode,'input_sha256':cu['input_sha256'],'geometric_clearance_pass':True,'full_coupon_connectivity_pass':True,'cuts':cuts})
Path('.config/compatibility-physical.json').write_text(json.dumps(results,indent=2)+'\n');print('Four native coupons clear; all eight actual-pad cut checks pass with zero shared copper outside the pads.')
