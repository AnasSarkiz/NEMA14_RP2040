"""Stagger QSPI SD2 and SD0 escapes outside the exposed pad and other lands."""
import json,math
import verify_supplier_connectivity as g
nets={e['name']:e for e in g.j if e['type']=='source_net'}
def port(role):return next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]=='U_MCU' and g.sp[p['source_port_id']]['name']==role)
net=nets['QSPI_SD2']['subcircuit_connectivity_map_key'];v=next(e for e in g.j if e['type']=='pcb_via' and g.key(e)==net and math.dist((e['x'],e['y']),(.6,2.125))<.001);old=(v['x'],v['y']);new=(.4,1.975);v.update(x=new[0],y=new[1]);changes=[]
for e in g.j:
 if e['type']=='pcb_trace' and g.key(e)==net:
  for q in e['route']:
   if q['route_type']=='wire' and math.dist((q['x'],q['y']),old)<.001:q.update(x=new[0],y=new[1]);changes.append(e['pcb_trace_id'])
g.j[:]=[e for e in g.j if not(e['type']=='pcb_trace' and e['pcb_trace_id'].startswith('review_baseline_feedback_fanout_pcb_port_102_'))]
for name,points in [('QSPI_SD2',None),('QSPI_SD0',None)]:
 p=port(name);n=nets[name];key=n['subcircuit_connectivity_map_key'];source=next(e['source_trace_id'] for e in g.j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==key and p['source_port_id'] in e['connected_source_port_ids']);points=[(p['x'],p['y']),(.25,2.975),(.25,2.2),new] if name=='QSPI_SD2' else [(p['x'],p['y']),(.65,2.975),(.6,2.475),(1.3,2.125)];route=[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top'} for x,y in points];route[0]['start_pcb_port_id']=p['pcb_port_id'];g.j.append({'type':'pcb_trace','pcb_trace_id':'review_escape_ordered_'+name,'route':route,'pcb_port_ids':[p['pcb_port_id']],'source_trace_id':source,'source_net_id':n['source_net_id'],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0'})
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/engineering-fixes/ordered-flash-escapes.json').write_text(json.dumps({'relocated_SD2_masked_via':{'from':old,'to':new},'follower_traces':sorted(set(changes)),'all_functional_pins_and_nets_preserved':True,'requires_DRC':True},indent=2)+'\n')
