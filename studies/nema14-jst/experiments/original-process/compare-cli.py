"""Assert the pinned CLI and API generated the same physical/source board; enumerate metadata deltas."""
from model import *
from routing_geometry import resolve_copper_nets
import hashlib
r=Path('artifacts/iteration-10');a=resolve_copper_nets(read(r/'final.circuit.json'));b=resolve_copper_nets(read(r/'native-cli.circuit.json'));deltas=[]
for typ in ['source_component','source_port','source_net','source_trace','pcb_component','pcb_smtpad','pcb_plated_hole','pcb_via','pcb_board','pcb_hole','pcb_keepout','pcb_courtyard_outline']:
 assert [e for e in a if e['type']==typ]==[e for e in b if e['type']==typ],('CLI replay differs',typ)
a={e['pcb_trace_id']:e for e in a if e['type']=='pcb_trace'};b={e['pcb_trace_id']:e for e in b if e['type']=='pcb_trace'};assert a.keys()==b.keys()
for k,t in a.items():
 assert t['subcircuit_connectivity_map_key']==b[k]['subcircuit_connectivity_map_key'];assert len(t['route'])==len(b[k]['route'])
 for i,(u,v) in enumerate(zip(t['route'],b[k]['route'])):
  assert {f:u.get(f) for f in ['route_type','x','y','width','layer']}=={f:v.get(f) for f in ['route_type','x','y','width','layer']}
  for f in ['start_pcb_port_id','end_pcb_port_id']:
   if u.get(f)!=v.get(f):assert f not in v;deltas.append({'trace':k,'node':i,'field':f,'API_geometrically_proven_port':u[f]})
report={'CLI_command_exit':read(r/'native-cli-exit.json'),'all_physical_copper_coordinates_widths_layers_and_nets_exact':True,'source_contract_and_all_poses_exact':True,'only_missing_nonphysical_endpoint_annotations':deltas,'counts':{'traces':len(a),'vias':22},'full_routing_attempted':False,'manufacturing_qualified':False};(r/'cli-replay.json').write_text(json.dumps(report,indent=2)+'\n');print('CLI physical replay exact; metadata-only endpoint annotations',len(deltas))
