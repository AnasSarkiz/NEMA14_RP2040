"""Represent each continuous same-layer wire section separately; actual vias remain authoritative."""
import json
import verify_supplier_connectivity as g
original=g.j;output=[];count=0;used={e.get('pcb_trace_id') for e in original if e['type']=='pcb_trace'}
for e in original:
 if e['type']!='pcb_trace':output.append(e);continue
 groups=[];current=[]
 for point in e['route']:
  if point['route_type']!='wire':
   if len(current)>=2:groups.append(current)
   current=[];continue
  if current and point['layer']!=current[-1]['layer']:
   if len(current)>=2:groups.append(current)
   current=[]
  current.append(point)
 if len(current)>=2:groups.append(current)
 if len(groups)==1 and len(groups[0])==len(e['route']):output.append(e);continue
 for i,route in enumerate(groups):
  id=e['pcb_trace_id']+'_layer_section_'+str(i)
  while id in used:id+='_next'
  used.add(id);ports=[p[tag] for p in route for tag in ['start_pcb_port_id','end_pcb_port_id'] if tag in p]
  output.append({**e,'pcb_trace_id':id,'route':route,'pcb_port_ids':sorted(set(ports))})
 count+=1
g.path.write_text(json.dumps(output,indent=2)+'\n');print('Split',count,'multilayer trace records; copper paths and actual plated vias retained')
