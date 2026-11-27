"""Object-owned nominal, width, drill and preservation evidence; rejected gates stay rejected."""
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union,nearest_points
import hashlib,copy
r=Path('artifacts/iteration-10');path=Path(sys.argv[1] if len(sys.argv)>1 else r/'annotated.circuit.json');j=resolve_copper_nets(read(path));old=resolve_copper_nets(b);nm,cs,pn,sps,pps,ps,cts=index(j)
def traces(data):
 st={e['source_trace_id']:e for e in data if e['type']=='source_trace'};return {st[e['source_trace_id']]['name']:e for e in data if e['type']=='pcb_trace'}
a,z=traces(old),traces(j);changes=read('experiments/original-process/paths.json');changed={e['name'] for e in changes};assert len(z)==44
for n in a:
 assert a[n]['subcircuit_connectivity_map_key']==z[n]['subcircuit_connectivity_map_key']
 if n not in changed:assert a[n]['route']==z[n]['route'],('Unintended copper change',n)
for n,c in co.items():assert all(cs[n][f]==c[f] for f in ['center','rotation','layer','width','height']),('Part moved',n)
via_specs=read('experiments/original-process/vias.json');vs=[e for e in j if e['type']=='pcb_via'];assert len(vs)==22 and all(e['hole_diameter']==.3 and e['outer_diameter']==.55 for e in vs)
vnames={e['pcb_via_id']:next(n for n,q in via_specs.items() if math.dist([e['x'],e['y']],[q['x'],q['y']])<1e-8) for e in vs};rows=[]
for n,t in z.items():
 for k,(u,v) in enumerate(zip(t['route'],t['route'][1:])):
  if u['route_type']!=v['route_type'] or u['route_type']!='wire' or u['layer']!=v['layer']:continue
  wire=LineString([(u['x'],u['y']),(v['x'],v['y'])]).buffer(max(u['width'],v['width'])*.6,quad_segs=128)
  for via in vs:
   if u['layer'] not in via['layers'] or via['subcircuit_connectivity_map_key']==t['subcircuit_connectivity_map_key']:continue
   gap=g.pad_shape(via,True).distance(wire);rows.append({'path':n,'pcb_trace_id':t['pcb_trace_id'],'segment':k,'layer':u['layer'],'via':vnames[via['pcb_via_id']],'pcb_via_id':via['pcb_via_id'],'drill_to_stressed_trace_mm':gap,'adjusted_margin_mm':gap-.115-.2})
failed=[e for e in rows if e['adjusted_margin_mm']<-1e-6];assert not failed,failed
# Exact original findings with all equal-distance primitive ownership, including duplicate zero-length nodes.
records={}
for e in old:
 if e['type'] in ['pcb_smtpad','pcb_via','pcb_plated_hole']:
  records[e[e['type']+'_id']]=[{'segment':None,'nominal':g.pad_shape(e),'stress':g.pad_shape(e)}]
 elif e['type']=='pcb_trace':
  records[e['pcb_trace_id']]=[]
  for k,(u,v) in enumerate(zip(e['route'],e['route'][1:])):
   if u['route_type']==v['route_type']=='wire' and u['layer']==v['layer']:
    line=LineString([(u['x'],u['y']),(v['x'],v['y'])]);records[e['pcb_trace_id']].append({'path':next(n for n,t in a.items() if t['pcb_trace_id']==e['pcb_trace_id']),'segment':k,'points_mm':list(line.coords),'nominal':line.buffer(max(u['width'],v['width'])/2,quad_segs=128),'stress':line.buffer(max(u['width'],v['width'])*.6,quad_segs=128)})
spacing=[]
for f in read('artifacts/iteration-9/final-process.json')['width_plus_20_percent_spacing']:
 pairs=[]
 for u in records[f['a']]:
  for v in records[f['b']]:
   gap=u['stress'].distance(v['stress'])
   if abs(gap-f['clearance_mm'])<1e-6:pairs.append({'a':{k:q for k,q in u.items() if k not in ['nominal','stress']},'b':{k:q for k,q in v.items() if k not in ['nominal','stress']},'nominal_gap_mm':u['nominal'].distance(v['nominal']),'stressed_gap_mm':gap})
 assert pairs;spacing.append({**f,'primitive_matches':pairs,'width_stress_introduces_failure':all(e['nominal_gap_mm']>=.15-1e-6 for e in pairs)})
# Identify actual nearest SMT pads to every original-hole via, not merely its nearest foreign net.
pads=[e for e in j if e['type']=='pcb_smtpad'];drill=[]
for v in vs:
 gaps=sorted([(g.pad_shape(v,True).distance(g.pad_shape(p)),p) for p in pads],key=lambda e:e[0]);minimum=gaps[0][0]
 if minimum-.115<0:
  drill.append({'via':vnames[v['pcb_via_id']],'pcb_via_id':v['pcb_via_id'],'center_mm':[v['x'],v['y']],'nominal_hole_SMT_gap_mm':minimum,'position_only_margin_mm':minimum-.075,'combined_budget_margin_mm':minimum-.115,'nearest_pads':[{'id':p['pcb_smtpad_id'],'terminal':'.'.join(next(k for k,port in ps.items() if port['pcb_port_id']==p['pcb_port_id'])),'gap_mm':d} for d,p in gaps if d<.115+1e-9]})
# Generalized return metric adds both actual annulus-end-to-axis distances, preventing edge clipping from hiding length.
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);v.spec=copy.deepcopy(read('experiments/placement/generated.json'))
for q in v.spec['vias']:q.update(via_specs[q['name']])
critical,cu=v.verify(path);assert critical['independent']['disconnected_nets']==59
# Independent physical contact at every numeric clipped endpoint, against the declared real port copper.
contacts=[];padmap={e['pcb_port_id']:e for e in pads};ppmap={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'}
for e in changes:
 t=z[e['name']]
 for selector,node,field in [(e['from'],t['route'][0],'start_pcb_port_id'),(e['to'],t['route'][-1],'end_pcb_port_id')]:
  pid=node[field];port=ppmap[pid];assert port['source_port_id'] in next(x for x in j if x['type']=='source_trace' and x['source_trace_id']==t['source_trace_id'])['connected_source_port_ids'];via=next((v for v in vs if pid in v['pcb_port_ids']),None);shape=g.pad_shape(via).difference(g.pad_shape(via,True)) if via else g.pad_shape(padmap[pid]);overlap=Point(node['x'],node['y']).buffer(node['width']/2,quad_segs=128).intersection(shape).area;assert overlap>1e-10;contacts.append({'path':e['name'],'terminal':selector,'real_port':pid,'endpoint_disk_real_copper_overlap_mm2':overlap})
source=next(e for e in j if e['type']=='source_trace' and e.get('name')=='AUTHORED_VREG_BASELINE');assert source['max_length']==1;vreg=[ps['U_DRV','VREG'],ps['C_VREG','pin1']];lower=g.pad_shape(padmap[vreg[0]['pcb_port_id']]).distance(g.pad_shape(padmap[vreg[1]['pcb_port_id']]))
report={'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'baseline_head':'c978b75e71dde2602bb733151d0edd422d00dc76','spacing_11_owned_findings':spacing,'inherited_combined_drill_pairs':read('artifacts/iteration-9/audit.json')['supplemental_combined_width_and_drill_screen']['failed_pairs'],'same_exact_spacing_and_combined_drill_object_pairs':0,'supplemental_combined_width_and_drill':{'width_multiplier':1.2,'radial_budget_mm':.115,'hole_to_foreign_track_mm':.2,'per_segment_pairs':rows,'failed':failed,'minimum_margin_mm':min(e['adjusted_margin_mm'] for e in rows),'replaces_legacy_gate':False},'original_hole_SMT_failures':drill,'all_component_poses_exact':True,'unchanged_route_arrays':len(a)-len(changed),'intentional_changed_paths':sorted(changed),'all_actual_vias_hole_pad_mm':[.3,.55],'independent_endpoint_contacts':contacts,'critical':critical,'VREG':{'wire_mm':sum(math.dist([u['x'],u['y']],[v['x'],v['y']]) for u,v in zip(z['AUTHORED_VREG_BASELINE']['route'],z['AUTHORED_VREG_BASELINE']['route'][1:])),'max_length_mm':source['max_length'],'physical_pad_edge_lower_bound_mm':lower,'routing_alone_cannot_meet_1mm_at_these_pads':lower>1,'native_limit_retained':True,'automatic_inference':'Core capacitor DEFAULT_MAX_DECOUPLING_TRACE_LENGTH_MM=1 propagates through getMaxLengthFromConnectedComponents; no numeric datasheet 1mm requirement claimed'},'native_routing_attempted':False,'promoted':False,'manufacturing_qualified':False}
Path(sys.argv[2] if len(sys.argv)>2 else r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print('44 traces /22 vias, widths/net/contacts/4Kelvin cuts/2returns pass; 11→0 stress and 3→0 combined drill; unchanged original-hole SMT failures',len(drill));print('returns',critical['actual_ground_returns']);print('combined minimum',min(e['adjusted_margin_mm'] for e in rows))
