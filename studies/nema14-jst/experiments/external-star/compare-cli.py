"""Compare real native CLI/API source/physical copper and list only nonphysical annotation differences."""
from model import *
from routing_geometry import resolve_copper_nets
r=Path('artifacts/iteration-12');out=[]
for mode in ['external','direct']:
 a=resolve_copper_nets(read(r/(mode+'.circuit.json')));b=resolve_copper_nets(read(r/(mode+'-cli.circuit.json')));deltas=[]
 for typ in ['source_component','source_port','source_net','source_trace','pcb_component','pcb_smtpad','pcb_plated_hole','pcb_via','pcb_board','pcb_hole','pcb_keepout','pcb_courtyard_outline']:assert [e for e in a if e['type']==typ]==[e for e in b if e['type']==typ],(mode,'CLI physical/source mismatch',typ)
 a={e['pcb_trace_id']:e for e in a if e['type']=='pcb_trace'};b={e['pcb_trace_id']:e for e in b if e['type']=='pcb_trace'};assert a.keys()==b.keys()
 for k,t in a.items():
  assert t['subcircuit_connectivity_map_key']==b[k]['subcircuit_connectivity_map_key'];assert len(t['route'])==len(b[k]['route'])
  for i,(u,v) in enumerate(zip(t['route'],b[k]['route'])):
   assert {f:u.get(f) for f in ['route_type','x','y','width','layer']}=={f:v.get(f) for f in ['route_type','x','y','width','layer']}
   for f in ['start_pcb_port_id','end_pcb_port_id']:
    if u.get(f)!=v.get(f):assert f not in v;deltas.append({'trace':k,'node':i,'field':f,'API_port':u[f]})
 out.append({'mode':mode,'source_and_physical_copper_exact':True,'missing_nonphysical_CLI_endpoint_annotations':deltas,'native_routing_attempted':False,'manufacturing_qualified':False})
(r/'cli-replay.json').write_text(json.dumps({'runs':out,'exit':read(r/'cli-exit.json')},indent=2)+'\n');print([(e['mode'],len(e['missing_nonphysical_CLI_endpoint_annotations'])) for e in out])
