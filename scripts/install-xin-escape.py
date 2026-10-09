"""Ordinary plated A4988 sense escapes; verify exact supplier pad clearances."""
import json
from shapely.geometry import Point,LineString
import verify_supplier_connectivity as g
plans=[('XIN',[(2.8,-4.15)])];add=[];rows=[]
for name,end in plans:
 key=next(k for k,n in g.nets.items()if n==name);p=next(p for p in g.ports.values()if g.src[g.comp[p['pcb_component_id']]['source_component_id']]=='U_MCU'and g.sp[p['source_port_id']]['name']==name);pts=[(p['x'],p['y'])]+end;wire=LineString(pts).buffer(.08);via=Point(*pts[-1]).buffer(.25);minimum=100
 for e in g.j:
  if e['type']not in ['pcb_smtpad','pcb_plated_hole']:continue
  q=g.geometry(e)
  if g.key(e)!=key:
   d=min(wire.distance(q),via.distance(q));assert d>=.1498,(name,e.get('pcb_smtpad_id'),d);minimum=min(minimum,d)
  if e['type']=='pcb_smtpad':assert via.intersection(q).area<1e-8,(name,e.get('pcb_smtpad_id'))
 net=next(e for e in g.j if e['type']=='source_net'and e['subcircuit_connectivity_map_key']==key);st=next(e for e in g.j if e['type']=='source_trace'and e['subcircuit_connectivity_map_key']==key and p['source_port_id']in e['connected_source_port_ids']);common={'subcircuit_connectivity_map_key':key,'source_net_id':net['source_net_id'],'source_trace_id':st['source_trace_id'],'subcircuit_id':'subcircuit_source_group_0'};tid='inside_mcu_escape_'+name
 add += [{'type':'pcb_trace','pcb_trace_id':tid,'pcb_port_ids':[p['pcb_port_id']],'route':[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top'}for x,y in pts],**common},{'type':'pcb_via','pcb_via_id':tid+'_via','pcb_trace_id':tid,'x':pts[-1][0],'y':pts[-1][1],'hole_diameter':.25,'outer_diameter':.5,'layers':['top','inner1','inner2','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common}];rows.append({'net':name,'points_mm':pts,'minimum_native_pad_clearance_mm':minimum})
ids={e[e['type']+'_id']for e in add};g.path.write_text(json.dumps([e for e in g.j if e.get(e['type']+'_id')not in ids]+add,indent=2)+'\n');(g.ROOT/'artifacts/validation/service-xin-escape.json').write_text(json.dumps({'escapes':rows,'status':'ALL_COPPER_DRC_CAM_REQUIRED'},indent=2)+'\n');print(rows)
