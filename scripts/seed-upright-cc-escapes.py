"""Reserve ordinary, tented CC fanouts inside the upright USB footprint rows.

No signal via sits in a solder pad. Full DRC/CAM/connectivity checks are mandatory.
"""
import json
import verify_supplier_connectivity as g
j=g.j;nets={e['name']:e for e in j if e['type']=='source_net'}
def port(ref,role):return next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role)
j[:]=[e for e in j if not e.get(e['type']+'_id','').startswith('usb_cc_escape_')]
for ref in ['J_PD','J_DATA']:
 c=next(c for c in g.comp.values() if g.src[c['source_component_id']]==ref)['center'];xc,yc=c['x'],c['y']
 for role in ['CC1','CC2']:
  p=port(ref,role);net=('PD_' if ref=='J_PD' else 'DATA_')+role;n=nets[net];key=n['subcircuit_connectivity_map_key'];st=next(e for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==key and p['source_port_id'] in e.get('connected_source_port_ids',[]));attrs=dict(source_net_id=n['source_net_id'],source_trace_id=st['source_trace_id'],subcircuit_connectivity_map_key=key,subcircuit_id='subcircuit_source_group_0')
  if ref=='J_PD':vx,vy=p['x'],yc;pts=[(p['x'],p['y']),(vx,vy)]
  elif role=='CC1':vx,vy=xc-1.0,yc+.15;pts=[(p['x'],p['y']),(p['x'],yc+.7),(vx,vy)]
  else:vx,vy=xc+.9,yc-.25;pts=[(p['x'],p['y']),(p['x'],yc-.75),(vx,vy)]
  uid='usb_cc_escape_'+ref+'_'+role;rr=[dict(route_type='wire',x=x,y=y,width=.16,layer='top') for x,y in pts];rr[0]['start_pcb_port_id']=p['pcb_port_id'];j.append(dict(type='pcb_trace',pcb_trace_id=uid,route=rr,pcb_port_ids=[p['pcb_port_id']],**attrs));j.append(dict(type='pcb_via',pcb_via_id=uid+'_via',x=vx,y=vy,hole_diameter=.3,outer_diameter=.45,layers=['top','inner1','inner2','bottom'],from_layer='top',to_layer='bottom',tented_on_top=True,tented_on_bottom=True,**attrs))
g.path.write_text(json.dumps(j,indent=2)+'\n');print('Reserved all four upright USB CC ordinary fanouts')
