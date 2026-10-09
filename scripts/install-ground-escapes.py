import sys,json
from shapely.geometry import Point,LineString
sys.path.insert(0,'scripts');import verify_supplier_connectivity as g
key=next(k for k,n in g.nets.items()if n=='GND');plans=[('U_DRV','GND',[(-.7,-8.349493)]),('U_DRV','GND18',[(-.7,-8.849873)]),('U_DRV','ROSC',[(.300633,-10.6),(-.7,-8.85)]),('R_REF_L','pin2',[(.5,-4.8)])];add=[];rows=[]
for ref,pin,end in plans:
 p=next(p for p in g.ports.values()if g.src[g.comp[p['pcb_component_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==pin);assert g.sp[p['source_port_id']]['subcircuit_connectivity_map_key']==key;pts=[(p['x'],p['y'])]+end;wire=LineString(pts).buffer(.08);via=Point(*pts[-1]).buffer(.2)if ref=='R_REF_L'else None
 for e in g.j:
  if e['type']not in ['pcb_smtpad','pcb_plated_hole']:continue
  q=g.geometry(e)
  if g.key(e)!=key:assert min(wire.distance(q),via.distance(q)if via is not None else 100)>=.1498,(ref,pin,e)
  if via is not None and e['type']=='pcb_smtpad':assert via.intersection(q).area<1e-8,e
 net=next(e for e in g.j if e['type']=='source_net'and e['subcircuit_connectivity_map_key']==key);st=next(e for e in g.j if e['type']=='source_trace'and e['subcircuit_connectivity_map_key']==key and p['source_port_id']in e['connected_source_port_ids']);common={'subcircuit_connectivity_map_key':key,'source_net_id':net['source_net_id'],'source_trace_id':st['source_trace_id'],'subcircuit_id':'subcircuit_source_group_0'};tid='inside_ground_escape_'+ref+'_'+pin;add.append({'type':'pcb_trace','pcb_trace_id':tid,'pcb_port_ids':[p['pcb_port_id']],'route':[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top'}for x,y in pts],**common})
 if via is not None:add.append({'type':'pcb_via','pcb_via_id':tid+'_via','pcb_trace_id':tid,'x':pts[-1][0],'y':pts[-1][1],'hole_diameter':.2,'outer_diameter':.4,'layers':['top','inner1','inner2','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common})
 rows.append({'reference':ref,'pin':pin,'points_mm':pts})
ids={e[e['type']+'_id']for e in add};j=[e for e in g.j if e.get(e['type']+'_id')not in ids];g.path.write_text(json.dumps(j+add,indent=2)+'\n');(g.ROOT/'artifacts/validation/service-ground-escapes.json').write_text(json.dumps({'rows':rows,'status':'REFILL_DRC_CAM_REQUIRED'},indent=2)+'\n');print(rows)
