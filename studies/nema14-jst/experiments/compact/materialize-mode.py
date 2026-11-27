"""Diagnostic translation preserving all existing geometry except a reported native mode rewrite."""
from pathlib import Path
import json,copy
base=json.load(open('artifacts/iteration-4/normal-attempt.circuit.json'));pp={e['pcb_port_id']:e for e in base if e['type']=='pcb_port'};sid=pp['pcb_port_217']['source_port_id'];source=next(e for e in base if e['type']=='source_trace' and sid in e['connected_source_port_ids']);net=next(e for e in base if e['type']=='source_net' and e['name']=='V3V3');key=source['subcircuit_connectivity_map_key'];raw=json.load(open('artifacts/iteration-5/mode-probes/via-to-vdd.output.json'));out=copy.deepcopy(base);changed=[];new=[];vias=[e for e in out if e['type']=='pcb_via']
for t in raw['traces']:
 if t['pcb_trace_id']=='pcb_trace_14':
  old=next(e for e in out if e.get('pcb_trace_id')=='pcb_trace_14');changed.append({'id':'pcb_trace_14','source_trace_id':old['source_trace_id'],'before_route_nodes':len(old['route']),'after_route_nodes':len(t['route'])});old['route']=t['route'];records=[old]
 elif t['connection_name']=='source_net_2':
  tr={'type':'pcb_trace','pcb_trace_id':'mode_probe_trace_'+str(len(new)),'source_trace_id':source['source_trace_id'],'source_net_id':net['source_net_id'],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':t.get('connectsTo',[]),'route':t['route']};out.append(tr);new.append(tr);records=[tr]
 else:continue
 for tr in records:
  assert all(n['route_type'] in ['wire','via'] for n in tr['route'])
  for n in tr['route']:
   if n['route_type']!='via':continue
   if any(abs(v['x']-n['x'])+abs(v['y']-n['y'])<1e-8 for v in vias):continue
   v={'type':'pcb_via','pcb_via_id':'mode_probe_via_'+str(len(vias)),'pcb_trace_id':tr['pcb_trace_id'],'source_trace_id':tr['source_trace_id'],'subcircuit_id':'subcircuit_source_group_0','subcircuit_connectivity_map_key':key,'source_net_id':net['source_net_id'],'x':n['x'],'y':n['y'],'hole_diameter':n.get('via_hole_diameter',.3),'outer_diameter':n.get('via_diameter',.45),'from_layer':n['from_layer'],'to_layer':n['to_layer'],'layers':['top','inner1','inner2','bottom']};vias.append(v);out.append(v)
Path('artifacts/iteration-5/mode-probes/materialized-vdd.circuit.json').write_text(json.dumps(out,indent=2)+'\n');Path('artifacts/iteration-5/mode-probes/materialization.json').write_text(json.dumps({'diagnostic_only':True,'changed_mode_copper':changed,'new_traces':len(new),'original_eight_paths_changed':False,'layer_span':'ordinary through-vias only; no blind/buried interpretation'},indent=2)+'\n');print(changed)
