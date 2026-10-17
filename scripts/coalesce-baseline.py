"""Join consecutive retained baseline segments without changing conductor geometry."""
import json,re,collections
import verify_supplier_connectivity as g
original=g.j;out=[];groups=collections.defaultdict(list)
for e in original:
 m=re.match(r'legal_baseline_(.+)_segment_(\d+)$',e.get('pcb_trace_id',''))
 if m:groups[m[1]].append((int(m[2]),e))
 else:out.append(e)
for name,items in groups.items():
 items.sort();runs=[];current=[];prev=None
 for index,e in items:
  if current and (index!=prev+1 or any(current[-1]['route'][-1][k]!=e['route'][0][k] for k in ['x','y','layer','width'])):runs.append(current);current=[]
  current.append(e);prev=index
 if current:runs.append(current)
 for i,run in enumerate(runs):
  e=dict(run[0]);route=list(e['route'])
  for q in run[1:]:
   route[-1]={**route[-1],**q['route'][0]};route.extend(q['route'][1:])
  e['route']=route;e['pcb_trace_id']='review_baseline_'+name+'_run_'+str(i);e['pcb_port_ids']=sorted({p[tag] for p in route for tag in ['start_pcb_port_id','end_pcb_port_id'] if tag in p});out.append(e)
g.path.write_text(json.dumps(out,indent=2)+'\n');print('Coalesced baseline segments:',len(original),'->',len(out),'records; wire geometry unchanged')
