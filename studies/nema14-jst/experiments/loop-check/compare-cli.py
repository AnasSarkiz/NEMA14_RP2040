from pathlib import Path
import json,hashlib
r=Path('artifacts/iteration-14');a=json.load(open(r/'candidate.circuit.json'));b=json.load(open(r/'native-cli.circuit.json'))
for typ in ['source_component','source_port','source_net','source_trace','pcb_board','pcb_component','pcb_smtpad','pcb_plated_hole','pcb_via','pcb_hole','pcb_keepout','pcb_courtyard_outline']:
 assert [e for e in a if e['type']==typ]==[e for e in b if e['type']==typ],typ
left={e['pcb_trace_id']:e for e in a if e['type']=='pcb_trace'};right={e['pcb_trace_id']:e for e in b if e['type']=='pcb_trace'};fields=['route_type','x','y','width','layer'];deltas=[]
for k,t in left.items():
 assert [{f:q.get(f) for f in fields} for q in t['route']]==[{f:q.get(f) for f in fields} for q in right[k]['route']]
 assert t['source_trace_id']==right[k]['source_trace_id'] and t['trace_length']==right[k]['trace_length']
 for i,(u,v) in enumerate(zip(t['route'],right[k]['route'])):
  for f in ['start_pcb_port_id','end_pcb_port_id']:
   if u.get(f)!=v.get(f):assert f not in v;deltas.append({'trace':k,'node':i,'missing_CLI_annotation':f,'API_value':u[f]})
api=json.load(open(r/'native.json.all-routing.json'));cli=json.load(open(r/'cli-native.json.all-routing.json'));assert {k:v for k,v in api['by_type'].items() if k!='pcb_port_not_connected_error'}=={k:v for k,v in cli['by_type'].items() if k!='pcb_port_not_connected_error'};assert len([e for e in cli['findings'] if e['type']=='pcb_trace_too_long_error'])==1
(r/'cli-comparison.json').write_text(json.dumps({'API_CLI_source_physical_geometry_and_actual_lengths_exact':True,'source_generation_CLI_exit':0,'source_generation_is_not_routing_DRC':True,'explicit_pinned_routing_check_by_type':cli['by_type'],'API_pinned_routing_check_by_type':api['by_type'],'extra_CLI_port_diagnostics':[e for e in cli['findings'] if e['type']=='pcb_port_not_connected_error' and e.get('message') not in {q.get('message') for q in api['findings'] if q['type']=='pcb_port_not_connected_error'}],'missing_nonphysical_CLI_endpoint_annotations':deltas,'normal_config_restored':True},indent=2)+'\n');print('CLI/API physical source exact; missing endpoint annotations',len(deltas),'explicit routing checks',cli['by_type'])
