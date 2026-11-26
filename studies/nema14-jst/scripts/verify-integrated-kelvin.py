"""Verify experimental full-controller copper, without accepting the failed board."""
from pathlib import Path
import json,sys,hashlib,math,importlib.util
from routing_geometry import resolve_copper_nets,pad_cut_topology,layer_copper,shared_outside_pad
from shapely.geometry import Point,LineString
spec=importlib.util.spec_from_file_location('copper',Path(__file__).with_name('inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
ROUTE_KEYS={'route_type','x','y','width','layer','from_layer','to_layer'}
FIXED_TYPES={'source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_board','pcb_hole','pcb_keepout'}
def geometry(board):
 names={e['source_trace_id']:e.get('name') for e in board if e['type']=='source_trace'}
 return {names[e['source_trace_id']]:[{k:v for k,v in n.items() if k in ROUTE_KEYS} for n in e['route']] for e in board if e['type']=='pcb_trace'}
def assert_fixed(control,candidate):
 for typ in FIXED_TYPES:assert [e for e in control if e['type']==typ]==[e for e in candidate if e['type']==typ],f'Changed {typ}'
 # Evaluator-relative asset URLs may differ; no pose, transform or model geometry may differ.
 normalize=lambda b:[{k:v for k,v in e.items() if k not in {'model_obj_url','model_step_url'}} for e in b if e['type']=='cad_component']
 assert normalize(control)==normalize(candidate),'CAD transform changed'
def verify(control_path,before_path,after_path,native_before,native_after,out):
 paths=[Path(p) for p in [control_path,before_path,after_path]];control,before,after=[json.loads(p.read_bytes()) for p in paths]
 assert hashlib.sha256(paths[0].read_bytes()).hexdigest()=='fe986e028cb398ebf3ed7fcbd9fd5dd8133b64c80aeac673c0540aa5c98cf06b','Wrong all-top control'
 for b in [before,after]:assert_fixed(control,b)
 routes=geometry(after);assert geometry(before)==routes,'Native routing changed authored copper'
 expected={f'{kind}_{phase}_{suffix}' for kind,suffixes in [('POWER',['DRV','COIL']),('KELVIN',['POS','NEG'])] for phase in 'AB' for suffix in suffixes};assert set(routes)==expected
 lengths={};widths={}
 for name,route in routes.items():
  width=.16 if name.startswith('KELVIN') else .45;w={n['width'] for n in route if n['route_type']=='wire'};assert w=={width},(name,w);widths[name]=width
  lengths[name]=sum(math.hypot(a['x']-z['x'],a['y']-z['y']) for a,z in zip(route,route[1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer'])
 b=resolve_copper_nets(after);sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={(sc[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'};pads={e['pcb_port_id']:e for e in b if e['type']=='pcb_smtpad'};st={e['source_trace_id']:e.get('name') for e in b if e['type']=='source_trace'};traces={st[e['source_trace_id']]:e for e in b if e['type']=='pcb_trace'};pickups=[]
 authored={p['name']:p for p in json.loads((Path(__file__).resolve().parents[1]/'experiments/integrated/authored-paths.json').read_text())};components={sc[e['source_component_id']]:e for e in b if e['type']=='pcb_component'}
 for phase in 'AB':
  for suffix,pin,target,power in [('POS','pin1','IN_POS',('U_DRV','OUT1A' if phase=='A' else 'OUT2A')),('NEG','pin2','IN_NEG',('J_MOTOR',phase+'_PLUS'))]:
   name=f'KELVIN_{phase}_{suffix}';shunt=pp['R_SHUNT_'+phase,pin];amp=pp['U_I'+phase,target];load=pp[power];pad=g.pad_shape(pads[shunt['pcb_port_id']]);net=sp[shunt['source_port_id']]['subcircuit_connectivity_map_key'];topology=pad_cut_topology(b,net,shunt['pcb_port_id'],amp['pcb_port_id'],load['pcb_port_id'],pad,'top',g.pad_shape);assert topology['actual_shunt_pad_is_required_pickup'] and topology['all_three_terminals_connected_before_cut'],name
   powername=f"POWER_{phase}_{'DRV' if suffix=='POS' else 'COIL'}";shared=shared_outside_pad(layer_copper([traces[name]],b,g.pad_shape),layer_copper([traces[powername]],b,g.pad_shape),pad,'top');assert shared<=1e-8,(name,shared)
   edge=authored[name]['actual_pad_edge'];ep=Point(*edge);assert pad.boundary.distance(ep)<1e-5,(name,'edge off actual pad');center=components['R_SHUNT_'+phase]['center'];assert (edge[0]-shunt['x'])*(center['x']-shunt['x'])+(edge[1]-shunt['y'])*(center['y']-shunt['y'])>0,(name,'pickup not body-facing');segments=[LineString([(a['x'],a['y']),(z['x'],z['y'])]) for a,z in zip(traces[name]['route'],traces[name]['route'][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']=='top'];assert min(q.distance(ep) for q in segments)<1e-6
   pickups.append({'name':name,'actual_body_facing_pad_edge':edge,'pad_cut':topology,'shared_copper_outside_actual_pad_mm2':shared})
 vias=[e for e in b if e['type']=='pcb_via'];assert len(vias)==10
 for v in vias:assert set(v['layers'])=={'top','inner1','inner2','bottom'} and {v['from_layer'],v['to_layer']}=={'top','bottom'} and v['outer_diameter']==.45 and v['hole_diameter']==.3
 copper=g.inspect(paths[2]);assert copper['geometric_clearance_pass'];assert len(copper['disconnected_nets'])==66 and not copper['full_board_connectivity_pass']
 native={}
 for label,path in [('before',native_before),('after',native_after)]:
  checks=json.loads(Path(path).read_text());assert len(checks)==12
  for name,result in checks.items():
   assert 'exception' not in result,(name,result)
   if name=='checkSourceTracesMatchPcbTraceThickness':
    assert result['count']==4 and all(e.get('type')=='pcb_trace_warning' for e in result['findings']),result
   else:assert result['count']==0,(name,result)
  native[label]={n:r['count'] for n,r in checks.items()}
 report={'control_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'authored_sha256':hashlib.sha256(paths[1].read_bytes()).hexdigest(),'normal_attempt_sha256':hashlib.sha256(paths[2].read_bytes()).hexdigest(),'source_and_fixed_geometry_unchanged':True,'authored_geometry_preserved_by_normal_native_routing':True,'authored_paths':len(routes),'through_vias':len(vias),'actual_width_mm':widths,'wire_length_mm':lengths,'via_barrel_lengths_included':False,'kelvin_wire_length_mismatch_mm':{p:abs(lengths[f'KELVIN_{p}_POS']-lengths[f'KELVIN_{p}_NEG']) for p in 'AB'},'pickups':pickups,'native_selected_checks':native,'independent_shorts':len(copper['shorts']),'independent_clearance_findings':len(copper['clearance_violations']),'independent_open_nets':len(copper['disconnected_nets']),'candidate_passes_production_gates':False,'production_source_changed':False,'limits':['Eight paths only. Normal native routing failed; remaining nets are open.','Long Kelvin and winding detours are not qualified current loops.','Neither 0.60 mm ground return is verified. USB return-plane, impedance, thermal, CAM and physical assembly remain unverified.']}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['pickups','native_selected_checks','actual_width_mm','limits']},indent=2));return report
if __name__=='__main__':verify(*sys.argv[1:])
