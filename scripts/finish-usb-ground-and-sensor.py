"""Manual final repair: explicit pad-to-pour spokes and inner sensor detour.
Native DRC and actual CAM are required after these geometric edits.
"""
import verify_supplier_connectivity as g
import json
from shapely.geometry import LineString
j=g.j;net=next(e for e in j if e['type']=='source_net'and e['name']=='GND');nk=net['subcircuit_connectivity_map_key'];common={'source_trace_id':next(e['source_trace_id']for e in j if e['type']=='source_trace'and e.get('subcircuit_connectivity_map_key')==nk),'source_net_id':net['source_net_id'],'subcircuit_connectivity_map_key':nk,'subcircuit_id':'subcircuit_source_group_0'}
changes=[]
for name,x in [('C_USB',4.3),('C_VREG_OUT',5.4)]:
 y=7.820116;ex=x+(.35 if name=='C_USB' else -.35);line=LineString([(x,y),(ex,y)]).buffer(.08)
 for e in j:
  if g.key(e)==nk:continue
  if e['type']in['pcb_smtpad','pcb_plated_hole']and 'top'in e.get('layers',[e.get('layer')]):assert line.distance(g.geometry(e))>=.15,(name,e,line.distance(g.geometry(e)))
  elif e['type']=='pcb_trace':
   for a,b in zip(e['route'],e['route'][1:]):
    if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']=='top':assert line.distance(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))>=.15,(name,e['pcb_trace_id'])
 e={'type':'pcb_trace','pcb_trace_id':'service_ground_spoke_'+name,'pcb_port_ids':[],'route':[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top'},{'route_type':'wire','x':ex,'y':y,'width':.16,'layer':'top'}],**common};j.append(e);changes.append(e)
e=next(e for e in json.loads((g.ROOT/'artifacts/validation/usb-old-inner-stubs-removed.json').read_text())if e['pcb_trace_id']=='supplier_repair_island_net37_0_upperbay_0');a,b=e['route'];e['pcb_trace_id']='service_sensor_inner2_detour';e['route']=[a,{**a,'y':16.7},{**b,'y':16.7},b];j.append(e);changes.append(e)
g.path.write_text(json.dumps(j,indent=2)+'\n');(g.ROOT/'artifacts/validation/usb-manual-final-repairs.json').write_text(json.dumps(changes,indent=2)+'\n')
