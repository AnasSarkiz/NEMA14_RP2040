"""Explicit reviewed local edits after official FreeRouting; no grid router."""
import json,pathlib,math
r=pathlib.Path(__file__).resolve().parents[1];p=r/'artifacts/board.circuit.json';j=json.loads(p.read_text());nets={e['name']:e for e in j if e['type']=='source_net'}
# Original exact routes supersede duplicate SES serialization on wholly fixed phases/sense.
protected={nets[n]['subcircuit_connectivity_map_key'] for n in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2']}
j=[e for e in j if not(e.get('pcb_trace_id','').startswith('independent_freerouted_')and e.get('subcircuit_connectivity_map_key')in protected) and e.get('pcb_via_id')!='outer_native_escape_R_REF_L_pin2_via' and e.get('pcb_trace_id')!='supplier_repair_island_net1_5']
# Move B+ outer transition away from the nearby new sense connection.
for e in j:
 if e.get('pcb_via_id')=='inside_phase_via_B_PLUS':e['x']=-1.13
 if e['type']=='pcb_trace':
  for q in e['route']:
   if abs(q.get('x',100)+1.200507)<.0001 and abs(q.get('y',100)+5.648)<.0001:q['x']=-1.13
# Replace CP1 with one short, direct top route, creating room for CP2's escape.
j=[e for e in j if not(e['type']=='pcb_trace'and e.get('subcircuit_connectivity_map_key')==nets['CP1']['subcircuit_connectivity_map_key'])]
def trace(id,name,layer,width,pts):
 n=nets[name];st=next(e for e in j if e['type']=='source_trace'and e.get('subcircuit_connectivity_map_key')==n['subcircuit_connectivity_map_key']);j.append({'type':'pcb_trace','pcb_trace_id':id,'route':[{'route_type':'wire','x':x,'y':y,'width':width,'layer':layer}for x,y in pts],'subcircuit_connectivity_map_key':n['subcircuit_connectivity_map_key'],'source_net_id':n['source_net_id'],'source_trace_id':st['source_trace_id'],'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[]})
def via(id,name,x,y):
 n=nets[name];j.append({'type':'pcb_via','pcb_via_id':id,'x':x,'y':y,'hole_diameter':.2,'outer_diameter':.4,'layers':['top','inner1','inner2','bottom'],'from_layer':'top','to_layer':'bottom','subcircuit_connectivity_map_key':n['subcircuit_connectivity_map_key'],'source_net_id':n['source_net_id'],'subcircuit_id':'subcircuit_source_group_0','tented_on_top':True,'tented_on_bottom':True})
trace('independent_CP1','CP1','top',.16,[(-3.199995,-8.849873),(-4,-8.849873),(-4.65,-9.199976)])
trace('independent_CP2_driver','CP2','top',.16,[(-3.199995,-9.350253),(-3.84,-9.350253)])
via('independent_CP2_driver_via','CP2',-3.84,-9.350253)
trace('independent_CP2_cap','CP2','top',.16,[(-4.65,-10.600024),(-5.4,-10.600024)])
via('independent_CP2_cap_via','CP2',-5.4,-10.600024)
trace('independent_CP2_bottom','CP2','bottom',.16,[(-3.84,-9.350253),(-5.4,-10.600024)])
trace('independent_PD_CVM_return','PD_VBUS','bottom',.45,[(-4.65,-8.3),(-6,-8.3),(-6,-4.7),(-2.8,-4.7)])
# Reuse no stale ground barrels now covered by moved passives.
j=[e for e in j if e.get('pcb_via_id')not in ['supplier_repair_island_net0_26xxx_via0','outer_native_escape_R_SB_pin2_via','inside_native_escape_C_ADC_pin2_via','independent_freerouted_via_78']]
for e in j:
 if e.get('pcb_via_id')=='independent_freerouted_via_54':e['x']=5.4;e['pcb_via_id']='independent_mcu_ep_ground'
 if e.get('pcb_via_id')=='inside_power_escape_C_VM_pin1_via':e['y']=-8.3
 if e['type']=='pcb_trace' and e.get('pcb_trace_id')=='inside_power_escape_C_VM_pin1':e['route'][0]['y']=-7.650024;e['route'][-1]['y']=-8.3
# Reroute one quiet V3V3 branch around the full mounting keepout, not only its drill.
for e in j:
 if e.get('pcb_trace_id')=='independent_freerouted_trace_216':e['route']=[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'inner2'}for x,y in [(9.1618,-14.3627),(9.1618,-16.05),(16,-16.05),(16,-8.5),(13.7366,-8.5)]]
# Change the local ENABLE bridge to inner2 to clear the relocated capacitor power via.
e=next(e for e in j if e.get('pcb_trace_id')=='independent_freerouted_trace_412');old=e['route'];end=old[-1];e['route']=old[:6]+[{'route_type':'wire','x':-5.3328,'y':-6.95,'width':.16,'layer':'top'}]
via('independent_enable_left','ENABLE_N',-5.3328,-6.95)
via('independent_enable_right','ENABLE_N',-4.01,-8.37)
trace('independent_enable_inner2','ENABLE_N','inner2',.16,[(-5.3328,-6.95),(-5.3328,-8.8),(-4.01,-8.8),(-4.01,-8.37)])
trace('independent_enable_right_top','ENABLE_N','top',.16,[(-4.01,-8.37),(-3.8817,-8.0735),(end['x'],end['y'])])
j=[e for e in j if e.get('pcb_via_id')not in ['supplier_repair_island_net0_22_via0','supplier_repair_island_net0_26x_via0']]
# Ground escape moved off C_ADC's native land; motor-decoupling GND uses explicit TypeVII.
via('independent_ADC_ground_via','GND',9.75,5.720014)
trace('independent_ADC_ground_escape','GND','top',.16,[(8.9,5.720014),(9.75,5.720014)])
via('independent_filled_C_VM_ground','GND',-4.65,-6.249976)
v=next(e for e in j if e.get('pcb_via_id')=='independent_filled_C_VM_ground');v['hole_diameter']=.25;v['outer_diameter']=.5
p.write_text(json.dumps(j,indent=2)+'\n');print('Explicit CP1/CP2, CVM power, B+ via and STEP clearance repairs applied')
