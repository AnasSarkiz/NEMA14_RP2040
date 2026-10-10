"""Adopt fresh native source/pads/models; rebind current routing by physical pins.
Only explicitly released nets are discarded. This never generates new routes.
"""
import json, pathlib, sys, copy
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json'
old=json.loads(path.read_text());fresh=json.loads((root/'artifacts/final-source.circuit.json').read_text())
assert not any(e['type'].endswith('_error')for e in fresh),'Fresh source must pass'
def maps(j):
 s={e['source_component_id']:e['name']for e in j if e['type']=='source_component'}
 sp={e['source_port_id']:(s[e['source_component_id']],e['pin_number'])for e in j if e['type']=='source_port'}
 pp={e['pcb_port_id']:sp[e['source_port_id']]for e in j if e['type']=='pcb_port'}
 nets={e['subcircuit_connectivity_map_key']:e['name']for e in j if e['type']=='source_net'}
 groups={}
 for e in j:
  if e['type']=='source_port'and e.get('subcircuit_connectivity_map_key'):groups.setdefault(e['subcircuit_connectivity_map_key'],[]).append(sp[e['source_port_id']])
 for k,v in groups.items():
  if k not in nets:nets[k]=tuple(sorted(v))
 return pp,nets
op,on=maps(old);np,nn=maps(fresh);nk={v:k for k,v in nn.items()};ports={v:k for k,v in np.items()}
traces={e['subcircuit_connectivity_map_key']:e['source_trace_id']for e in fresh if e['type']=='source_trace'}
nets={e['subcircuit_connectivity_map_key']:e['source_net_id']for e in fresh if e['type']=='source_net'}
release=set(sys.argv[1:]);copper=[]
for original in old:
 if original['type']not in ['pcb_trace','pcb_via','pcb_copper_pour']:continue
 name=on.get(original.get('subcircuit_connectivity_map_key'))
 if name in release or name not in nk:continue
 e=copy.deepcopy(original);k=nk[name];e['subcircuit_connectivity_map_key']=k
 for field,mapping in [('source_trace_id',traces),('source_net_id',nets)]:
  e.pop(field,None)
  if k in mapping:e[field]=mapping[k]
 if e['type']=='pcb_trace':
  e['pcb_port_ids']=[ports[op[p]]for p in e.get('pcb_port_ids',[])if p in op and op[p]in ports]
  for point in e['route']:
   for field in ['start_pcb_port_id','end_pcb_port_id']:
    if field in point:point[field]=ports[op[point[field]]]
 if e['type']=='pcb_via'and next(b for b in fresh if b['type']=='pcb_board')['num_layers']==4:e['layers']=['top','inner1','inner2','bottom']
 copper.append(e)
result=[e for e in fresh if e['type']not in ['pcb_trace','pcb_via','pcb_copper_pour']]+copper
# Preserve the explicitly specified filled/capped exposed-pad process. Strict
# checks separately reject every unspecified via-in-pad.
next(e for e in result if e['type']=='pcb_board')['is_via_in_pad_allowed']=next(e for e in old if e['type']=='pcb_board').get('is_via_in_pad_allowed',False)
path.write_text(json.dumps(result,indent=2)+'\n');print('Rebound',len(copper),'copper records; released nets',sorted(release))
