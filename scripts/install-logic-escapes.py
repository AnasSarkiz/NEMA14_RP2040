"""Explicit standard motor-supply escapes; every native foreign pad checked."""
import json,math,hashlib
import verify_supplier_connectivity as g
from shapely.geometry import Point,LineString
rp=g.ROOT.name=='NEMA14_RP2040';j=g.j;key=next(k for k,n in g.nets.items()if n=='V3V3');ports=[]
plan=[('R_REF_H','pin1',[(-3.6,-5.45)])]
add=[];rows=[]
for ref,pin,points in plan:
 port=next(e for e in j if e['type']=='pcb_port'and g.src[g.comp[e['pcb_component_id']]['source_component_id']]==ref and g.sp[e['source_port_id']]['name']==pin);assert g.sp[port['source_port_id']]['subcircuit_connectivity_map_key']==key;points=[(port['x'],port['y'])]+points;wire=LineString(points).buffer(.15);via=Point(*points[-1]).buffer(.25);minimum=100
 for p in j:
  if p['type']not in ['pcb_smtpad','pcb_plated_hole']:continue
  q=g.geometry(p)
  if g.key(p)!=key:
   d=min(wire.distance(q)if'top'in p.get('layers',[p.get('layer')])else 100,via.distance(q));assert d>=.1498,(ref,pin,'foreign pad',p.get('pcb_smtpad_id'),d);minimum=min(d,minimum)
  if p['type']=='pcb_smtpad':assert via.intersection(q).area<1e-8,(ref,pin,'via land inside SMT',p.get('pcb_smtpad_id'))
 net=next(e for e in j if e['type']=='source_net'and e['subcircuit_connectivity_map_key']==key);st=next(e for e in j if e['type']=='source_trace'and e['subcircuit_connectivity_map_key']==key);common={'subcircuit_connectivity_map_key':key,'source_net_id':net['source_net_id'],'source_trace_id':st['source_trace_id'],'subcircuit_id':'subcircuit_source_group_0'};tid='inside_logic_escape_'+ref+'_'+pin;add += [{'type':'pcb_trace','pcb_trace_id':tid,'pcb_port_ids':[port['pcb_port_id']],'route':[{'route_type':'wire','x':x,'y':y,'width':.3,'layer':'top'}for x,y in points],**common},{'type':'pcb_via','pcb_via_id':tid+'_via','pcb_trace_id':tid,'x':points[-1][0],'y':points[-1][1],'hole_diameter':.25,'outer_diameter':.5,'layers':['top','inner1','inner2','bottom']if rp else['top','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common}];rows.append({'reference':ref,'pin':pin,'points_mm':points,'minimum_native_foreign_pad_clearance_mm':minimum})
ids={e.get(e['type']+'_id')for e in add};j=[e for e in j if e.get(e['type']+'_id')not in ids];g.path.write_text(json.dumps(j+add,indent=2)+'\n');(g.ROOT/'artifacts/validation/service-logic-escapes.json').write_text(json.dumps({'rows':rows,'status':'INDEPENDENT_TRACE_VIA_SPACING_AND_CAM_REQUIRED'},indent=2)+'\n');print(rows)
