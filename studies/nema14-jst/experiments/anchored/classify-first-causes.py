"""Classify the saved rejected artifacts; never infer a routed pass from placement."""
from pathlib import Path
import json,gzip,sys,math,hashlib,importlib.util,collections
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets
from native_sources import source_owner_names
spec=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
p=Path('artifacts/iteration-5');out=Path('artifacts/iteration-6');out.mkdir(exist_ok=True)
def read(path):return json.loads(path.read_bytes() if path.exists() else gzip.decompress(Path(str(path)+'.gz').read_bytes()))
full=resolve_copper_nets(read(p/'full-unpacked.circuit.json'));scope=resolve_copper_nets(read(p/'cluster-authored.circuit.json'));routed=resolve_copper_nets(read(p/'core-driver/native.circuit.json'));cu=read(p/'full-unpacked-copper.json');rc=read(p/'core-driver/copper.json');srj=read(p/'core-driver/native-input.srj.json');moved=set(read(Path('experiments/compact/candidate-poses.json')))
def indexes(b):
 names=source_owner_names(b);sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};pad={e[e['type']+'_id']:e for e in b if e['type']=='pcb_smtpad'};st={e['source_trace_id']:e for e in b if e['type']=='source_trace'};return names,sp,pp,pad,st
names,sp,pp,pads,st=indexes(scope)
fullrows=[]
for v in cu['clearance_violations']:
 assert v['a_ref'] and v['b_ref'] and v['a'].startswith('pcb_smtpad_') and v['b'].startswith('pcb_smtpad_')
 a,z=v['a_ref'].split('.')[0],v['b_ref'].split('.')[0];assert (a in moved)!=(z in moved),(a,z)
 fullrows.append({**v,'first_cause':'moved_component_pad_against_unplaced_original_component_pad','moved_component':a if a in moved else z,'unplaced_component':z if a in moved else a,'stale_trace_coordinates_involved':False,'short':v in cu['shorts']})
def traces_by_name(b):
 ids={e['source_trace_id']:e.get('name') for e in b if e['type']=='source_trace'};out=collections.defaultdict(list)
 for e in b:
  if e['type']=='pcb_trace':out[ids[e['source_trace_id']]].append([{k:n[k] for k in ['route_type','x','y','width','layer','from_layer','to_layer'] if k in n} for n in e['route']])
 return dict(out)
f=traces_by_name(full);s=traces_by_name(scope);assert f==s,'Full vs scope authored world copper mismatch'
# Verify all native connection anchors against the actual moved source's ports.
anchors=[]
for connection in srj['connections']:
 for point in connection['pointsToConnect']:
  pid=point.get('pcb_port_id')
  if pid not in pp:continue
  expected=pp[pid];delta=math.hypot(point['x']-expected['x'],point['y']-expected['y']);assert delta<1e-10,(pid,delta);anchors.append({'port':pid,'source':names[sp[expected['source_port_id']]['source_component_id']]+'.'+sp[expected['source_port_id']]['name'],'delta_mm':delta})
# Check generated pad-obstacle centers and bounds; rotated-pill approximations use bounds.
obstacles=[]
for o in srj['obstacles']:
 pid=o.get('circuitJsonMetadata',{}).get('pcb_smtpad_id')
 if not pid:continue
 e=pads[pid];bounds=g.pad_shape(e).bounds;center=[(bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2];delta=math.dist(center,[o['center']['x'],o['center']['y']]);dims=[bounds[2]-bounds[0],bounds[3]-bounds[1]];angle=math.radians(o.get('ccwRotationDegrees',0));ow=abs(math.cos(angle))*o['width']+abs(math.sin(angle))*o['height'];oh=abs(math.sin(angle))*o['width']+abs(math.cos(angle))*o['height']
 assert delta<1e-8 and abs(dims[0]-ow)<1e-8 and abs(dims[1]-oh)<1e-8,(pid,delta,dims,o['width'],o['height'])
 obstacles.append({'pad':pid,'center_delta_mm':delta,'bounds_match':True})
board=next(e for e in routed if e['type']=='pcb_board');edge=[];unique={r['id'] for r in rc['board_edge_violations']}
for t in [e for e in routed if e['type']=='pcb_trace' and e['pcb_trace_id'] in unique]:
 for i,(a,z) in enumerate(zip(t['route'],t['route'][1:])):
  if a['route_type']!=z['route_type'] or a['route_type']!='wire' or a['layer']!=z['layer']:continue
  width=max(a['width'],z['width']);xmin=min(a['x'],z['x'])-width/2;xmax=max(a['x'],z['x'])+width/2;ymin=min(a['y'],z['y'])-width/2;ymax=max(a['y'],z['y'])+width/2;gap=min(xmin+17.5,17.5-xmax,ymin+17.5,17.5-ymax)
  if gap>=board['min_board_edge_clearance']-1e-6:continue
  edge.append({'trace':t['pcb_trace_id'],'segment':i,'layer':a['layer'],'width_mm':width,'true_copper_edge_gap_mm':gap,'required_mm':.25,'first_cause':'new_automatic_route_not_contained_in_board_edge_safe_region','original_fixed_trace':t['pcb_trace_id'].startswith('pcb_trace_')})
assert len(edge)==len(rc['board_edge_violations'])
mut=read(p/'core-driver/verification.json')['fixed_authored_wire_changes']
for x in mut:x['first_cause']='pcbPaths_not_collected_by_pinned_Core_manual_pcbPath_fixed_trace_guard';x['stale_pose_evidence']=False
report={'saved_head':'1f2e1736f2f8c2bf955dc5de0bced796c5cc69a7','full_33_shorts_and_39_spacing':{'shorts':len(cu['shorts']),'spacing_including_shorts':len(fullrows),'all_pad_to_pad':True,'cause_counts':dict(collections.Counter(e['first_cause'] for e in fullrows)),'by_moved_component':dict(collections.Counter(e['moved_component'] for e in fullrows)),'findings':fullrows},'authored_full_and_scope_geometry_equal':True,'all_saved_SRJ_connection_anchors_match_actual_moved_ports':{'count':len(anchors),'maximum_delta_mm':max(e['delta_mm'] for e in anchors)},'all_saved_pad_obstacles_match_actual_moved_pads':{'count':len(obstacles),'maximum_center_delta_mm':max(e['center_delta_mm'] for e in obstacles)},'stale_authored_world_copper_or_stale_pad_obstacles_proven':False,'native_15_board_edge_findings':edge,'six_mutated_authored_shapes':mut,'code_evidence':{'core_version':'0.0.2110','file':'@tscircuit/core/dist/index.js','manual_trace_detection_lines':[120146,120151],'recognizes':'Boolean(child._parsedProps.pcbPath?.length)','misses':'pcbPaths','edge_checker_version':'0.0.283','edge_checker_omits':'pcb_trace is absent from checkCopperToBoardEdgeClearance elementTypes; pad/via/pour checks do not cover trace segments','effect':'Multisegment authored fragments remain editable preloaded SRJ traces instead of fixed obstacles.'},'scope_limits':['No full candidate routing attempted','Native zero edge-check findings did not catch actual copper outside the safe board region','A native SRJ rectangle can conservatively approximate pad geometry; dimensions were checked against transformed actual pad bounds']}
(out/'first-causes.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['full_33_shorts_and_39_spacing','native_15_board_edge_findings','six_mutated_authored_shapes','code_evidence','scope_limits']});print('pad collisions by mover',report['full_33_shorts_and_39_spacing']['by_moved_component']);print('edge counts',len(edge),len(unique),'min copper gap',min(e['true_copper_edge_gap_mm'] for e in edge))
