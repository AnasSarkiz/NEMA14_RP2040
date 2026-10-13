"""Connect paired trunk ends through the real ESD and series-resistor pins."""
import json
import verify_supplier_connectivity as g
j=g.j;ROOT=g.ROOT;nets={e['name']:e for e in j if e['type']=='source_net'};usb={nets[n]['subcircuit_connectivity_map_key'] for n in ['USB_DP','USB_DM','MCU_DP','MCU_DM']}
j[:]=[e for e in j if not(e['type'] in ['pcb_trace','pcb_via'] and g.key(e) in usb and not e.get('pcb_trace_id','').startswith('usb_coupled_'))]
plan=json.loads((ROOT/'artifacts/engineering-fixes/usb-routing-plan.json').read_text());cores={c['name']:c for c in plan['cores']}
def port(ref,role):return next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role)
def attrs(net,p):
 key=nets[net]['subcircuit_connectivity_map_key'];source=next(e['source_trace_id'] for e in j if e['type']=='source_trace' and e.get('subcircuit_connectivity_map_key')==key and p['source_port_id'] in e.get('connected_source_port_ids',[]));return {'source_net_id':nets[net]['source_net_id'],'source_trace_id':source,'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0'}
def trace(uid,net,p,points,layer,tag=False):
 route=[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':layer} for x,y in points]
 if tag:route[0]['start_pcb_port_id']=p['pcb_port_id']
 j.append({'type':'pcb_trace','pcb_trace_id':uid,'route':route,'pcb_port_ids':[p['pcb_port_id']] if tag else [],**attrs(net,p)})
def via(uid,net,p,x,y):j.append({'type':'pcb_via','pcb_via_id':uid,'x':x,'y':y,'outer_diameter':.4,'hole_diameter':.2,'layers':['top','inner1','inner2','bottom'],'from_layer':'top','to_layer':'bottom','tented_on_top':True,'tented_on_bottom':True,**attrs(net,p)})
def endpoint(core,net,index):return next(t for t in cores[core]['tracks'] if t['net']==net)['points'][index]
for net,role,x in [('USB_DP','DP2',5.4),('USB_DM','DM1',6.0)]:
 p=port('J_DATA',role);trace('usb_fan_J_DATA_'+net,net,p,[(p['x'],p['y']),(p['x'],9.15),(x,8.95)],'top',True);via('usb_fan_J_DATA_'+net+'_via',net,p,x,8.95);trace('usb_fan_J_DATA_'+net+'_bottom',net,p,[(x,8.95),endpoint('connector_to_ESD',net,0)],'bottom')
for net,inrole,outrole in [('USB_DP','DP2','DP1'),('USB_DM','DM2','DM1')]:
 p=port('U_ESD',inrole);x=p['x'];trace('usb_fan_ESD_input_'+net+'_bottom',net,p,[(x,7.0),endpoint('connector_to_ESD',net,-1)],'bottom')
 q=port('U_ESD',outrole);trace('usb_fan_ESD_IO_link_'+net,net,q,[(q['x'],q['y']),(p['x'],p['y'])],'top',True);via('usb_fan_ESD_output_'+net+'_via',net,q,q['x'],7.0);start=endpoint('ESD_to_series',net,0);trace('usb_fan_ESD_output_'+net+'_bottom',net,q,[(q['x'],7.0),(start[0],6.5),start],'bottom')
for net,ref,x in [('USB_DP','R_DP',4.6),('USB_DM','R_DM',5.3)]:
 p=port(ref,'pin2');trace('usb_fan_series_input_'+net,net,p,[(p['x'],p['y']),(p['x'],6.15),(x,6.35)],'top',True);via('usb_fan_series_input_'+net+'_via',net,p,x,6.35);trace('usb_fan_series_input_'+net+'_bottom',net,p,[(x,6.35),endpoint('ESD_to_series',net,-1)],'bottom')
for net,ref,role in [('MCU_DP','R_DP','USB_DP'),('MCU_DM','R_DM','USB_DM')]:
 p=port(ref,'pin1');trace('usb_fan_series_output_'+net,net,p,[(p['x'],p['y']),endpoint('series_to_MCU',net,0)],'top',True);q=port('U_MCU',role);trace('usb_fan_MCU_'+net,net,q,[(q['x'],q['y']),endpoint('series_to_MCU',net,-1)],'top',True)
# VREG_OUT leaves the inner edge of its QFN land. This ordinary, tented via
# lies outside the exposed pad and beneath the package, away from USB returns.
j[:]=[e for e in j if e.get('pcb_trace_id')!='usb_escape_VREG_OUT' and e.get('pcb_via_id')!='usb_escape_VREG_OUT_via']
p=port('U_MCU','VREG_OUT');trace('usb_escape_VREG_OUT','V1V1',p,[(p['x'],p['y']),(p['x'],2.6)],'top',True);via('usb_escape_VREG_OUT_via','V1V1',p,p['x'],2.6)
g.path.write_text(json.dumps(j,indent=2)+'\n');print('Seeded ordered USB/ESD/resistor connections and an internal VREG_OUT escape')
