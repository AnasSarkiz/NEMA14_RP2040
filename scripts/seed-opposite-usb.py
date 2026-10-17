"""Ordered native USB4145 inner/outer-row connections for lower-edge upright data socket.

Construction only; native DRC, physical connectivity and CAM qualification follow.
"""
import json
import verify_supplier_connectivity as g
j=g.j;nets={e['name']:e for e in j if e['type']=='source_net'};plan=json.loads((g.ROOT/'artifacts/engineering-fixes/usb-routing-plan.json').read_text());core=next(c for c in plan['cores'] if c['name']=='connector_to_ESD')
def p(role):return next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]=='J_DATA' and g.sp[p['source_port_id']]['name']==role)
def attrs(net,port):
 n=nets[net];sid=next(e['source_trace_id'] for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==n['subcircuit_connectivity_map_key'] and port['source_port_id'] in e.get('connected_source_port_ids',[]));return dict(source_net_id=n['source_net_id'],source_trace_id=sid,subcircuit_connectivity_map_key=n['subcircuit_connectivity_map_key'],subcircuit_id='subcircuit_source_group_0')
def trace(uid,net,port,pts,layer,tag=False,end=None):
 route=[dict(route_type='wire',x=x,y=y,width=.16,layer=layer) for x,y in pts]
 if tag:route[0]['start_pcb_port_id']=port['pcb_port_id']
 if end:route[-1]['end_pcb_port_id']=end['pcb_port_id']
 j.append(dict(type='pcb_trace',pcb_trace_id=uid,route=route,pcb_port_ids=([port['pcb_port_id']] if tag else [])+([end['pcb_port_id']] if end else []),**attrs(net,port)))
def via(uid,net,port,x,y):j.append(dict(type='pcb_via',pcb_via_id=uid,x=x,y=y,outer_diameter=.45,hole_diameter=.3,layers=['top','inner1','inner2','bottom'],from_layer='top',to_layer='bottom',tented_on_top=True,tented_on_bottom=True,**attrs(net,port)))
j[:]=[e for e in j if not e.get(e['type']+'_id','').startswith('usb_lower_') and not (e['type']=='pcb_trace' and e['pcb_trace_id'].startswith('usb_fan_ESD') and all(p.get('layer')=='bottom' for p in e['route']))]
xc=(p('DP1')['x']+p('DM1')['x'])/2;yc=p('DP1')['y']-1.479931
for net,role,offset in [('USB_DP','DP1',-.35),('USB_DM','DM1',.35)]:
 port=p(role);vx=xc+offset;vy=yc+.4;trace('usb_lower_'+role,net,port,[(port['x'],port['y']),(port['x'],yc+.7),(vx,vy)],'top',True);via('usb_lower_'+role+'_via',net,port,vx,vy);end=next(t for t in core['tracks'] if t['net']==net)['points'][0];trace('usb_lower_'+role+'_bottom',net,port,[(vx,vy),end],'bottom')
q=p('DM2');r=p('DM1');trace('usb_lower_mirrored_DM2','USB_DM',q,[(q['x'],q['y']),(q['x'],yc-.5),(r['x'],yc+.2),(r['x'],r['y'])],'top',True,r)
q=p('DP2');vx=xc+.25;vy=yc-.65;trace('usb_lower_mirrored_DP2','USB_DP',q,[(q['x'],q['y']),(q['x'],vy),(vx,vy)],'top',True);via('usb_lower_DP2_via','USB_DP',q,vx,vy);trace('usb_lower_DP2_bottom','USB_DP',q,[(vx,vy),(xc-.35,yc-.15),(xc-.35,yc+.4)],'bottom')
g.path.write_text(json.dumps(j,indent=2)+'\n');print('Constructed inner-row + paired trunk and mirrored outer-row links',xc,yc)
