"""Restore the MCU STEP fanout to its existing ordinary via, with pad/Cu guard."""
import json
from shapely.geometry import Point,LineString
import verify_supplier_connectivity as g
p=next(p for p in g.ports.values()if g.src[g.comp[p['pcb_component_id']]['source_component_id']]=='U_MCU'and g.sp[p['source_port_id']]['name']=='GPIO6');key=g.sp[p['source_port_id']]['subcircuit_connectivity_map_key'];v=next(e for e in g.j if e.get('pcb_via_id')=='freerouted_via_67');assert g.key(v)==key and v['hole_diameter']==.25 and v['outer_diameter']==.5;pts=[(p['x'],p['y']),(v['x'],v['y'])];w=LineString(pts).buffer(.08);ds=[]
for e in g.j:
 if g.key(e)==key:continue
 t=e['type'];qs=[]
 if t in ['pcb_smtpad','pcb_plated_hole']:qs=[g.geometry(e)]
 if t=='pcb_via':qs=[Point(e['x'],e['y']).buffer(e['outer_diameter']/2)]
 if t=='pcb_trace':qs=[LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)for a,b in zip(e['route'],e['route'][1:])if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']=='top']
 for q in qs:d=w.distance(q);assert d>=.1498,(e,d);ds.append(d)
st=next(e for e in g.j if e['type']=='source_trace'and p['source_port_id']in e['connected_source_port_ids']);tid='inside_mcu_escape_STEP';add={'type':'pcb_trace','pcb_trace_id':tid,'pcb_port_ids':[p['pcb_port_id']],'source_trace_id':st['source_trace_id'],'source_net_id':st['connected_source_net_ids'][0],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0','route':[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top'}for x,y in pts]};g.path.write_text(json.dumps([e for e in g.j if e.get('pcb_trace_id')!=tid]+[add],indent=2)+'\n');(g.ROOT/'artifacts/validation/service-mcu-step-escape.json').write_text(json.dumps({'points_mm':pts,'existing_via_reused':v['pcb_via_id'],'minimum_native_and_existing_foreign_top_copper_clearance_mm':min(ds),'status':'FINAL_ALL_LAYER_DRC_AND_CAM_REQUIRED'},indent=2)+'\n');print(pts,min(ds))
