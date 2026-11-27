"""Independent external-return and full VREG-loop audit. No pad, width or clearance is repaired."""
from model import *
from routing_geometry import resolve_copper_nets,pad_cut_topology,shared_outside_pad
from shapely.ops import unary_union
import hashlib,copy
r=Path('artifacts/iteration-12')
def groups(data):
 st={e['source_trace_id']:e.get('name','') for e in data if e['type']=='source_trace'};return {st[e['source_trace_id']]:e for e in data if e['type']=='pcb_trace'}
def audit(path):
 j=resolve_copper_nets(read(path));names,cs,pc,ss,pp,ps,courts=index(j);tr=groups(j);old=groups(resolve_copper_nets(b));pads={e['pcb_port_id']:e for e in j if e['type']=='pcb_smtpad'};vias=[e for e in j if e['type']=='pcb_via'];spec=read('experiments/external-star/all-vias.json');vs={n:next(e for e in vias if math.dist([e['x'],e['y']],[v['x'],v['y']])<1e-8) for n,v in spec.items()};holes=unary_union([g.pad_shape(v,True) for v in vias])
 for n,t in old.items():
  if n.startswith('RETURN_'):continue
  assert t['route']==tr[n]['route'] and t['subcircuit_connectivity_map_key']==tr[n]['subcircuit_connectivity_map_key'],('Preserved copper changed',n)
 for n,c in co.items():assert all(cs[n][f]==c[f] for f in ['center','rotation','layer','width','height']),('Component moved',n)
 for typ in ['pcb_board','pcb_hole','pcb_keepout','pcb_smtpad','source_component','source_net']:
  assert [e for e in b if e['type']==typ]==[e for e in j if e['type']==typ],('Unintended source or geometry change',typ)
 fitted_ids={e['source_component_id'] for e in b if e['type']=='source_component'}
 assert [e for e in b if e['type']=='pcb_component' and e['source_component_id'] in fitted_ids]==[e for e in j if e['type']=='pcb_component' and e['source_component_id'] in fitted_ids],'Fitted component/DNP record changed'
 cad=lambda data:[{k:v for k,v in e.items() if k not in ['model_obj_url','model_step_url']} for e in data if e['type']=='cad_component' and e['source_component_id'] in fitted_ids];assert cad(b)==cad(j),'Supplier CAD transform changed'
 oldpc={e['pcb_component_id']:e for e in b if e['type']=='pcb_component'};via_component_deltas=[]
 for e in [e for e in j if e['type']=='pcb_component' and e['source_component_id'] not in fitted_ids]:
  before=oldpc[e['pcb_component_id']]
  if e!=before:
   assert e['source_component_id'] in ['source_manually_placed_via_'+str(i) for i in [14,15,16,17]] and {k:v for k,v in e.items() if k!='center'}=={k:v for k,v in before.items() if k!='center'};via_component_deltas.append({'via_component':e['pcb_component_id'],'before':before['center'],'after':e['center']})
 assert len(via_component_deltas)==4
 oldsp={e['source_port_id']:e for e in b if e['type']=='source_port'};newsp={e['source_port_id']:e for e in j if e['type']=='source_port'};port_deltas=[]
 for pid in oldsp:
  if oldsp[pid]==newsp[pid]:continue
  left,right=oldsp[pid],newsp[pid];assert left['source_component_id'] in ['source_manually_placed_via_'+str(i) for i in [14,15,16,17]] and 'subcircuit_connectivity_map_key' not in right and {k:v for k,v in left.items() if k!='subcircuit_connectivity_map_key'}==right;port_deltas.append({'unused_via_source_port':pid,'name':left['name'],'former_net':left['subcircuit_connectivity_map_key'],'physical_via_net_retained':True})
 assert len(port_deltas) in [0,6]
 assert len(vias)==22 and all(e['hole_diameter']==.3 and e['outer_diameter']==.55 for e in vias)
 unchanged=[e for e in vias if not any(math.dist([e['x'],e['y']],[spec[n]['x'],spec[n]['y']])<1e-8 for n in ['V_GA','V_STAR_A','V_GB','V_STAR_B'])];assert len(unchanged)==18 and all(e in b for e in unchanged)
 def wires(t):return [(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(a['width']/2,quad_segs=128).difference(holes),[a['layer']]) for a,z in zip(t['route'],t['route'][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']]
 returns=[]
 for phase,pin in [('A','GND18'),('B','GND')]:
  ts=[t for n,t in tr.items() if n.startswith('RETURN_'+phase+'_')];assert all(p['width']==.6 for t in ts for p in t['route']);endpoints=[ps['R_S'+phase,'pin2']['pcb_port_id'],ps['U_DRV','EP']['pcb_port_id']];land=pads[ps['U_DRV',pin]['pcb_port_id']]
  def connected(cut=False,missing=None):
   rec=[]
   def add(poly,ls,pid=None):
    for q in list(poly.geoms) if hasattr(poly,'geoms') else [poly]:
     if q.area>1e-10:rec.append((q,ls,pid))
   for t in ts:
    for poly,ls in wires(t):add(poly,ls)
   for pid in endpoints+([] if cut else [land['pcb_port_id']]):add(g.pad_shape(pads[pid]).difference(holes),['top'],pid)
   for i,n in enumerate(['V_G'+phase,'V_STAR_'+phase]):
    v=vs[n];ring=g.pad_shape(v).difference(g.pad_shape(v,True))
    if missing==i:
     for layer in v['layers']:add(ring,[layer])
    else:add(ring,v['layers'])
   parent=list(range(len(rec)))
   def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
   for i,(poly,ls,_) in enumerate(rec):
    for k,(q,lq,_) in enumerate(rec[:i]):
     if set(ls)&set(lq) and poly.intersection(q).area>1e-10:parent[find(k)]=find(i)
   return bool(set.intersection(*[{find(i) for i,q in enumerate(rec) if q[2]==pid} for pid in endpoints]))
  assert connected() and not connected(cut=True)
  # Cross-section through the compulsory intermediate ground land, outside every trace-end cap.
  cy=land['y'];cx=land['x'];alltop=unary_union([p for t in ts for p,ls in wires(t) if 'top' in ls]+[g.pad_shape(land)]);cross=alltop.intersection(LineString([(cx,cy-1),(cx,cy+1)]));neck=cross.length;assert neck<.281 and neck<.6
  wire=sum(math.dist([a['x'],a['y']],[z['x'],z['y']]) for t in ts for a,z in zip(t['route'],t['route'][1:]) if a['layer']==z['layer']);outer=tr['RETURN_'+phase+'_EXTERNAL']['route'][-1];inside=tr['RETURN_'+phase+'_EP']['route'][0];padaccess=math.dist([outer['x'],outer['y']],[land['x'],land['y']])+math.dist([inside['x'],inside['y']],[land['x'],land['y']]);two_barrels='RETURN_'+phase+'_INNER' in tr;serial=wire+padaccess+(2*.1415 if two_barrels else 0)
  row={'phase':phase,'all_authored_return_wire_widths_mm':.6,'intermediate_land':'.U_DRV.'+pin,'intermediate_land_required_after_actual_pad_cut':True,'middle_cross_section_copper_upper_bound_mm':neck,'required_planar_width_mm':.6,'actual_0_60_width_pass':False,'nominal_width_loss_percent':100*(.6-neck)/.6,'individual_barrel_links_required':[not connected(missing=i) for i in [0,1]],'authored_wire_mm':wire,'explicit_intermediate_pad_access_mm':padaccess,'authored_serial_barrels':2 if two_barrels else 0,'authored_serial_path_mm':serial,'serial_path_describes_required_current_flow':two_barrels and all(not connected(missing=i) for i in [0,1])}
  if not two_barrels:
   # Construct a real hole-avoiding conductive path, NOT a .60mm-wide path. Via ring is a physical annulus.
   s=ps['R_S'+phase,'pin2'];v=vs['V_STAR_'+phase];a=math.atan2(s['y']-v['y'],s['x']-v['x']);z=math.atan2(land['y']-v['y'],land['x']-v['x']);delta=(z-a+math.pi)%(2*math.pi)-math.pi;radius=.225;arc=[[v['x']+radius*math.cos(a+delta*k/256),v['y']+radius*math.sin(a+delta*k/256)] for k in range(257)];route=[[s['x'],s['y']]]+arc+[[land['x'],land['y']],[inside['x'],inside['y']],[ps['U_DRV','EP']['x'],ps['U_DRV','EP']['y']]];plane=unary_union([p for t in ts for p,ls in wires(t) if 'top' in ls]+[g.pad_shape(pads[endpoints[0]]),g.pad_shape(pads[endpoints[1]]),g.pad_shape(land)]+[g.pad_shape(vs[n]).difference(g.pad_shape(vs[n],True)) for n in ['V_G'+phase,'V_STAR_'+phase]]).difference(holes);line=LineString(route);assert line.difference(plane.buffer(1e-8)).length<1e-6;row.update({'hole_avoiding_top_path_mm':line.length,'hole_avoiding_path_fits_5mm':line.length<=5,'zero_conducted_barrels':True,'path_points_mm':route,'path_is_0_60mm_wide':False,'does_not_qualify_return':True})
  returns.append(row)
 cu=g.inspect(str(path));ground=next(e for e in cu['disconnected_nets'] if e['net']=='GND');vregsrc=ps['C_VREG','pin2'];gnd_island=next(x for x in ground['islands'] if 'C_VREG.pin2' in x);driver_island=next(x for x in ground['islands'] if 'U_DRV.EP' in x);assert gnd_island!=driver_island
 vregsource=next(e for e in j if e['type']=='source_trace' and e.get('name')=='AUTHORED_VREG_BASELINE');assert vregsource['max_length']==1;assert set(vregsource['connected_source_port_ids'])=={ps['U_DRV','VREG']['source_port_id'],ps['C_VREG','pin1']['source_port_id']};vregtrace=tr['AUTHORED_VREG_BASELINE'];vregwire=sum(math.dist([a['x'],a['y']],[z['x'],z['y']]) for a,z in zip(vregtrace['route'],vregtrace['route'][1:]));assert abs(vregwire-.9907754874075481)<1e-12 and abs(vregtrace['trace_length']-vregwire)<1e-12
 # Trace actual copper islands for supply/ground closure; source-net labels alone never close a loop.
 def same_copper(net,a,z):
  found=next((e for e in cu['disconnected_nets'] if e['net']==net),None)
  if found is None:return True
  left=next((i for i,x in enumerate(found['islands']) if a in x),None);right=next((i for i,x in enumerate(found['islands']) if z in x),None);assert left is not None and right is not None,(net,a,z);return left==right
 loop_closures={'sense_A_to_EP':same_copper('GND','R_SA.pin2','U_DRV.EP'),'sense_B_to_EP':same_copper('GND','R_SB.pin2','U_DRV.EP'),'driver_GND3_to_EP':same_copper('GND','U_DRV.GND','U_DRV.EP'),'driver_GND18_to_EP':same_copper('GND','U_DRV.GND18','U_DRV.EP'),'EP_to_ceramic_VBB_bypass_ground':same_copper('GND','U_DRV.EP','C_VM.pin2'),'EP_to_bulk_ground':same_copper('GND','U_DRV.EP','C_BULK.pin2'),'VCP_reservoir_to_driver':same_copper('VCP','C_VCP.pin1','U_DRV.VCP'),'VCP_reservoir_supply_to_VBB1':same_copper('PD_VBUS','C_VCP.pin2','U_DRV.VBB1')}
 assert all(loop_closures[k] for k in ['sense_A_to_EP','sense_B_to_EP','driver_GND3_to_EP','driver_GND18_to_EP']);assert not loop_closures['EP_to_ceramic_VBB_bypass_ground'] and not loop_closures['VCP_reservoir_to_driver']
 # Re-run all four actual inline-shunt pickup cuts, with real geometry and no reliance on trace names for connectivity.
 pickups=[]
 def branch(n):return [t for name,t in tr.items() if name==n or name.startswith(n+'__')]
 def shapes(ts):
  by={}
  for t in ts:
   for poly,ls in wires(t):by.setdefault(ls[0],[]).append(poly)
  for via in vias:
   if via['subcircuit_connectivity_map_key'] not in {t['subcircuit_connectivity_map_key'] for t in ts}:continue
   ring=g.pad_shape(via).difference(g.pad_shape(via,True))
   if any(layer in by and any(p.intersection(ring).area>1e-10 for p in by[layer]) for layer in via['layers']):
    for layer in via['layers']:by.setdefault(layer,[]).append(ring)
  return {k:unary_union(p) for k,p in by.items()}
 for phase in 'AB':
  for pole,pin,target,power in [('POS','pin1',('U_DRV','OUT1A' if phase=='A' else 'OUT2A'),'DRV'),('NEG','pin2',('J_MOTOR',phase+'_PLUS'),'COIL')]:
   port=ps['R_SHUNT_'+phase,pin];pad=g.pad_shape(pads[port['pcb_port_id']]);key=ss[port['source_port_id']]['subcircuit_connectivity_map_key'];topo=pad_cut_topology(j,key,port['pcb_port_id'],ps['U_I'+phase,'IN_'+pole]['pcb_port_id'],ps[target]['pcb_port_id'],pad,'top',g.pad_shape);assert topo['actual_shunt_pad_is_required_pickup'];overlap=shared_outside_pad(shapes(branch('KELVIN_'+phase+'_'+pole)),shapes(branch('POWER_'+phase+'_'+power)),pad,'top');assert overlap<1e-8;pickups.append({'phase':phase,'pole':pole,'actual_pad_cut':topo,'shared_winding_Cu_outside_pad_mm2':overlap})
 return {'input_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'preserved_nonreturn_route_arrays':38,'preserved_other_via_whole_records':18,'all_fitted_component_poses_DNP_CAD_and_supplier_pads_exact':True,'manual_via_component_deltas':via_component_deltas,'unused_via_port_metadata_deltas':port_deltas,'all_via_holes_lands_mm':[.30,.55],'returns':returns,'Kelvin_actual_pickups':pickups,'actual_loop_closures':loop_closures,'full_VREG_loop':{'positive_leg_wire_mm':vregwire,'ground_pad_to_EP_pad_edge_lower_bound_mm':g.pad_shape(pads[vregsrc['pcb_port_id']]).distance(g.pad_shape(pads[ps['U_DRV','EP']['pcb_port_id']])),'capacitor_ground_island':gnd_island,'driver_ground_island':driver_island,'capacitor_ground_reaches_driver_ground':False,'closed_copper_loop_exists':False,'complete_loop_length_mm':None,'loop_area_mm2':None,'reason':'No real ground copper from C_VREG.pin2 to the driver GND/PAD island. Internal chip connections and source net identity are not substituted for copper.'},'independent':{k:len(cu[k]) for k in ['shorts','clearance_violations','drill_spacing_violations','hole_trace_violations','board_edge_violations','screw_keepout_violations','disconnected_nets']},'native_routing_attempted':False,'candidate_promoted':False,'manufacturing_qualified':False}
if __name__=='__main__':
 outputs={}
 for mode in ['external','direct']:
  outputs[mode]=audit(r/(mode+'.circuit.json'))
  Path(r/(mode+'-audit.json')).write_text(json.dumps(outputs[mode],indent=2)+'\n');print(mode,[{k:e[k] for k in ['phase','middle_cross_section_copper_upper_bound_mm','individual_barrel_links_required','authored_serial_path_mm']} for e in outputs[mode]['returns']]);print(mode,'VREG closedloop?',outputs[mode]['full_VREG_loop']['closed_copper_loop_exists'])
