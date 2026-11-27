"""Fail closed on changed accepted geometry, lost Kelvin copper, or missing actual returns.
A passing experiment is not full-board connectivity or locality acceptance.
"""
from pathlib import Path
import sys,json,math,hashlib,importlib.util,subprocess
from routing_geometry import resolve_copper_nets,pad_cut_topology,layer_copper,shared_outside_pad
from shapely.geometry import Point,LineString
spec=importlib.util.spec_from_file_location('cu',Path(__file__).with_name('inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
spec=importlib.util.spec_from_file_location('old',Path(__file__).with_name('verify-integrated-kelvin.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def verify(control_path,before_path,after_path,native_path,out):
 control,before,after=[json.loads(Path(x).read_bytes()) for x in [control_path,before_path,after_path]]
 for typ in ['source_component','source_net','pcb_board','pcb_smtpad','pcb_plated_hole','pcb_hole','pcb_keepout']:
  assert [e for e in control if e['type']==typ]==[e for e in after if e['type']==typ],typ
 norm=lambda b:[{k:v for k,v in e.items() if k not in {'model_obj_url','model_step_url'}} for e in b if e['type']=='cad_component']
 assert norm(control)==norm(after),'CAD pose/model geometry changed'
 for typ in ['source_port','pcb_port','pcb_component','source_trace']:
  key=typ+'_id';indexed={e[key]:e for e in after if e['type']==typ}
  for e in control:
   if e['type']==typ:assert indexed.get(e[key])==e,(typ,e[key])
 routes=old.geometry(after);assert len(routes)==15
 for name,route in old.geometry(control).items():assert routes[name]==route,name
 assert old.geometry(before)==routes,'Native routing changed authored copper'
 expected_widths={n:(.16 if n.startswith('KELVIN') or n in ['DRIVER_MODE_RESET','MODE_ESCAPE'] else .45 if n.startswith('POWER') else .6) for n in routes}
 for name,r in routes.items():assert {n['width'] for n in r if n['route_type']=='wire'}=={expected_widths[name]},name
 b=resolve_copper_nets(after);sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};ports={(sc.get(sp[e['source_port_id']]['source_component_id'],sp[e['source_port_id']]['source_component_id']),sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'};pads={e['pcb_port_id']:e for e in b if e['type']=='pcb_smtpad'};st={e['source_trace_id']:e.get('name') for e in b if e['type']=='source_trace'};traces={st[e['source_trace_id']]:e for e in b if e['type']=='pcb_trace'};pickups=[]
 for phase in 'AB':
  for suffix,pin,inp,power in [('POS','pin1','IN_POS',('U_DRV','OUT1A' if phase=='A' else 'OUT2A')),('NEG','pin2','IN_NEG',('J_MOTOR',phase+'_PLUS'))]:
   name=f'KELVIN_{phase}_{suffix}';s=ports['R_SHUNT_'+phase,pin];a=ports['U_I'+phase,inp];load=ports[power];pad=g.pad_shape(pads[s['pcb_port_id']]);net=sp[s['source_port_id']]['subcircuit_connectivity_map_key'];cut=pad_cut_topology(b,net,s['pcb_port_id'],a['pcb_port_id'],load['pcb_port_id'],pad,'top',g.pad_shape);assert cut['actual_shunt_pad_is_required_pickup'] and cut['all_three_terminals_connected_before_cut'],name
   shared=shared_outside_pad(layer_copper([traces[name]],b,g.pad_shape),layer_copper([traces[f"POWER_{phase}_{'DRV' if suffix=='POS' else 'COIL'}"]],b,g.pad_shape),pad,'top');assert shared<=1e-8
   pickups.append({'name':name,'pad_cut':cut,'shared_copper_outside_shunt_mm2':shared})
 vias=[e for e in b if e['type']=='pcb_via'];assert len(vias)==14
 for v in vias:assert set(v['layers'])=={'top','inner1','inner2','bottom'} and v['outer_diameter']==.45 and v['hole_diameter']==.3
 manual=[e for e in b if e['type']=='source_manually_placed_via'];assert len(manual)==4
 expected_centers=[(10.975,3.700127),(7.237,-.4684992),(5.53,15.5955202),(8.449303,1.7006)]
 for center in expected_centers:
  matching=[v for v in vias if math.hypot(v['x']-center[0],v['y']-center[1])<1e-8];assert len(matching)==1 and len(matching[0].get('pcb_port_ids',[]))==4
 counts=json.loads(Path(native_path).read_bytes());assert len(counts)==12
 for k,v in counts.items():assert v.get('count')==0 and 'exception' not in v,(k,v)
 cu=g.inspect(after_path);assert cu['geometric_clearance_pass'];assert not cu['full_board_connectivity_pass'] and len(cu['disconnected_nets'])==66
 critical_out=out+'.critical.json'
 subprocess.run([sys.executable,str(Path(__file__).with_name('check-critical-paths.py')),after_path,critical_out,'--routed'],stdout=subprocess.DEVNULL,check=False)
 critical=json.loads(Path(critical_out).read_bytes());assert critical['routed_return_width_and_continuity_verified'] and critical['routed_kelvin_full_continuity_verified']
 lengths={p:sum(sum(math.hypot(a['x']-z['x'],a['y']-z['y']) for a,z in zip(routes[n],routes[n][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']) for n in ['RETURN_'+p+'_TOP','RETURN_'+p+'_INNER1']) for p in 'AB'}
 assert all(x>5 for x in lengths.values()),'Do not silently change the 5 mm target'
 report={'authored_sha256':hashlib.sha256(Path(before_path).read_bytes()).hexdigest(),'normal_sha256':hashlib.sha256(Path(after_path).read_bytes()).hexdigest(),'original_components_ports_nets_pads_mounts_board_unchanged':True,'original_eight_paths_identical':True,'all_fifteen_paths_preserved':True,'traces':15,'vias':14,'actual_widths_mm':expected_widths,'kelvin_pickups':pickups,'ground_source_to_star_wire_mm':lengths,'ground_return_target_mm':5,'ground_return_length_pass':False,'via_barrel_lengths_included':False,'native_selected_checks':{k:v['count'] for k,v in counts.items()},'shorts':len(cu['shorts']),'clearance_findings':len(cu['clearance_violations']),'open_nets':66,'full_board_routed_pass':False,'manufacturing_qualified':False}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['kelvin_pickups','actual_widths_mm','native_selected_checks']});return report
if __name__=='__main__':verify(*sys.argv[1:])
