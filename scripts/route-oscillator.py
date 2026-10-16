"""Short, top-only RP2040 oscillator connections on real imported terminal centres."""
import json
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
import verify_supplier_connectivity as g
j=g.j;nets={e['name']:e for e in j if e['type']=='source_net'};clock={nets[n]['subcircuit_connectivity_map_key'] for n in ['XIN','XOUT','XTAL_OUT']}
def port(ref,role):return next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role)
def xy(p):return p['x'],p['y']
def attrs(net,p):
 n=nets[net];s=next(e for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==n['subcircuit_connectivity_map_key'] and p['source_port_id'] in e.get('connected_source_port_ids',[]));return {'source_trace_id':s['source_trace_id'],'source_net_id':n['source_net_id'],'subcircuit_connectivity_map_key':n['subcircuit_connectivity_map_key'],'subcircuit_id':'subcircuit_source_group_0'}
j[:]=[e for e in j if not(e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour'] and (e['type']=='pcb_copper_pour' or g.key(e) in clock or e.get(e['type']+'_id','').startswith('oscillator_')))]
rows=[]
def trace(name,net,a,b,intermediate=[]):
 p,q=port(*a),port(*b);pts=[xy(p)]+intermediate+[xy(q)];route=[dict(route_type='wire',x=x,y=y,layer='top',width=.16) for x,y in pts];route[0]['start_pcb_port_id']=p['pcb_port_id'];route[-1]['end_pcb_port_id']=q['pcb_port_id'];uid='oscillator_'+name;j.append(dict(type='pcb_trace',pcb_trace_id=uid,route=route,pcb_port_ids=[p['pcb_port_id'],q['pcb_port_id']],**attrs(net,p)));rows.append(dict(trace=uid,net=net,points=pts,length_mm=LineString(pts).length))
assert port('R_XOUT','pin1')['y']>port('R_XOUT','pin2')['y'],'XOUT damping input must be nearest the MCU'
trace('XIN','XIN',('U_MCU','XIN'),('Y_MCU','pin1'),[(1.500052,-3.95)])
trace('load_XIN','XIN',('C_XIN','pin1'),('Y_MCU','pin1'))
trace('XOUT','XOUT',('U_MCU','XOUT'),('R_XOUT','pin1'),[(1.899848,-4.175),(3.15,-4.175),(3.15,-6.687184)])
trace('XTAL_OUT','XTAL_OUT',('R_XOUT','pin2'),('Y_MCU','pin3'))
trace('load_XOUT','XTAL_OUT',('C_XOUT','pin1'),('R_XOUT','pin2'))
for ref,role,v in [('Y_MCU','pin2',(.249989,-6.3)),('Y_MCU','pin4',(1.950011,-6.12)),('C_XIN','pin2',(-2.75,-4.85)),('C_XOUT','pin2',(6.05,-7.32))]:
 p=port(ref,role);uid='oscillator_ground_'+ref+'_'+role;route=[dict(route_type='wire',x=x,y=y,layer='top',width=.16) for x,y in [xy(p),v]];route[0]['start_pcb_port_id']=p['pcb_port_id'];j.append(dict(type='pcb_trace',pcb_trace_id=uid,route=route,pcb_port_ids=[p['pcb_port_id']],**attrs('GND',p)));j.append(dict(type='pcb_via',pcb_via_id=uid+'_via',x=v[0],y=v[1],hole_diameter=.3,outer_diameter=.45,layers=['top','inner1','inner2','bottom'],from_layer='top',to_layer='bottom',tented_on_top=True,tented_on_bottom=True,**attrs('GND',p)))
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/upright-revision/oscillator-plan.json').write_text(json.dumps({'construction_requires_full_verification':True,'routes':rows,'guard_buffer_mm':.25,'layers_reserved':['top','inner1'],'MCU_pin_local_exemption_radius_mm':.55},indent=2)+'\n');print('Constructed top-only oscillator',[(r['net'],round(r['length_mm'],3)) for r in rows])
