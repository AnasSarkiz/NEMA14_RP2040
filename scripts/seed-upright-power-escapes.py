"""Short 0.30 mm outer-layer VBUS pad escapes into two 0.50/0.30 mm through vias.

Full 0.75 A budget remains in the independent thermal audit; trunks retain their
wider policy. No terminal share or unverified parallel-current assumption is used.
"""
import json
import verify_supplier_connectivity as g
j=g.j;sn={e['name']:e for e in j if e['type']=='source_net'}
def port(ref,role):return next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role)
j[:]=[e for e in j if not e.get(e['type']+'_id','').startswith('usb_power_escape_')]
for ref in ['J_PD','J_DATA']:
 c=next(c for c in g.comp.values() if g.src[c['source_component_id']]==ref)['center'];xc,yc=c['x'],c['y'];net='PD_VBUS' if ref=='J_PD' else 'DATA_VBUS';n=sn[net];key=n['subcircuit_connectivity_map_key']
 for role in ['VBUS1','VBUS2','VBUS3','VBUS4']:
  p=port(ref,role);vx=xc+(-2 if p['x']<xc else 2);vy=yc+.05 if ref=='J_DATA' else yc;way_y=yc+(.75 if p['y']>yc else -.75)
  if ref=='J_DATA' and role=='VBUS4':way_y=yc-.7
  st=next(e for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==key and p['source_port_id'] in e.get('connected_source_port_ids',[]));attrs=dict(source_net_id=n['source_net_id'],source_trace_id=st['source_trace_id'],subcircuit_connectivity_map_key=key,subcircuit_id='subcircuit_source_group_0');uid='usb_power_escape_'+ref+'_'+role;pts=[(p['x'],p['y']),(p['x'],way_y),(vx,vy)];rr=[dict(route_type='wire',x=x,y=y,width=.30,layer='top') for x,y in pts];rr[0]['start_pcb_port_id']=p['pcb_port_id'];j.append(dict(type='pcb_trace',pcb_trace_id=uid,route=rr,pcb_port_ids=[p['pcb_port_id']],**attrs));vuid='usb_power_escape_'+ref+('_west_via' if vx<xc else '_east_via')
  if not any(e.get('pcb_via_id')==vuid for e in j):j.append(dict(type='pcb_via',pcb_via_id=vuid,x=vx,y=vy,hole_diameter=.3,outer_diameter=.5,layers=['top','inner1','inner2','bottom'],from_layer='top',to_layer='bottom',tented_on_top=True,tented_on_bottom=True,**attrs))
g.path.write_text(json.dumps(j,indent=2)+'\n');print('Reserved all eight VBUS pads with 0.30 mm outer escapes and four ordinary through vias')
