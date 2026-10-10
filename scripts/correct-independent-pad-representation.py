"""C_USB native-checker spoke contained entirely in verified connected pad copper."""
import json
import verify_supplier_connectivity as g
from shapely.geometry import LineString
rep=json.loads((g.ROOT/'artifacts/physical-connectivity.json').read_text());assert not rep['disconnectedNets'],rep
p=next(p for p in g.ports.values()if g.src[g.comp[p['pcb_component_id']]['source_component_id']]=='C_USB' and g.sp[p['source_port_id']]['pin_number']==2)
id=p['pcb_port_id'];pad=next(e for e in g.j if e['type']=='pcb_smtpad' and e.get('pcb_port_id')==id);assert g.nets[g.key(pad)]=='GND';pts=[(p['x'],p['y']),(p['x']+.05,p['y'])];assert g.geometry(pad).covers(LineString(pts).buffer(.08));st=next(e for e in g.j if e['type']=='source_trace'and p['source_port_id']in e['connected_source_port_ids'])
tid='independent_native_C_USB_ground_spoke';g.j[:]=[e for e in g.j if e.get('pcb_trace_id')!=tid];g.j.append({'type':'pcb_trace','pcb_trace_id':tid,'pcb_port_ids':[id],'source_trace_id':st['source_trace_id'],'source_net_id':st['connected_source_net_ids'][0],'subcircuit_connectivity_map_key':g.key(pad),'subcircuit_id':'subcircuit_source_group_0','route':[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top'}for x,y in pts]});g.path.write_text(json.dumps(g.j,indent=2)+'\n');(g.ROOT/'artifacts/validation/independent-native-pad-spoke.json').write_text(json.dumps({'purpose':'Native checker pad-center representation; physical connectivity already passed','pad':id,'CuAddedOutsideActualPadMm2':0,'points':pts},indent=2)+'\n')
