"""Native full-copper qualification, exact preservation and unchanged stress rejection."""
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
import copy,hashlib
p=Path(sys.argv[1]);j=resolve_copper_nets(read(p));old=resolve_copper_nets(b);_,cs,_,sps,pps,ps,cts=index(j);pads={e['pcb_port_id']:e for e in j if e['type']=='pcb_smtpad'}
def groups(data):
 st={e['source_trace_id']:e for e in data if e['type']=='source_trace'};return {('AUTHORED_VREG_BASELINE' if e['pcb_trace_id']=='source_net_23_0' else st[e['source_trace_id']].get('name','')):e for e in data if e['type']=='pcb_trace'}
a,z=groups(old),groups(j);assert len(z)==44;assert sum(e['type']=='pcb_via' for e in j)==22
for n,c in co.items():
 if n!='C_CP':assert all(cs[n][k]==c[k] for k in ['center','rotation','layer','width','height']),('Unintended part move',n)
source_trace=next(e for e in j if e['type']=='source_trace' and e.get('name')=='AUTHORED_VREG_BASELINE');assert source_trace['max_length']==1,'Native VREG length gate changed'
for name,t in a.items():
 if name in ['AUTHORED_CP1_CORRIDOR','AUTHORED_CP2_CORRIDOR']:continue
 q=z[name];assert t['route']==q['route'],('fixed route changed',name);assert t['subcircuit_connectivity_map_key']==q['subcircuit_connectivity_map_key'],name
 if name!='AUTHORED_VREG_BASELINE':
  l,r=copy.deepcopy(t),copy.deepcopy(q)
  for e in [l,r]:
   length=sum(math.dist([v['x'],v['y']],[w['x'],w['y']]) for v,w in zip(e['route'],e['route'][1:]) if v['route_type']==w['route_type']=='wire' and v['layer']==w['layer']);assert abs(length-e.pop('trace_length'))<1e-12
  assert l==r,('fixed identity changed',name)
assert all(e in j for e in old if e['type']=='pcb_via')
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);v.spec=read('experiments/placement/generated.json');critical,cu=v.verify(p);assert critical['independent']['disconnected_nets']==59;assert not any(e['net'] in ['CP1','CP2','VREG'] for e in cu['disconnected_nets'])
rows=[];drills=[];ep=g.pad_shape(pads[ps['U_DRV','EP']['pcb_port_id']]);square=box(9.8,9.8,16.2,16.2);circle=Point(13,13).buffer(3.2,quad_segs=128)
for r in read('experiments/tolerance/paths.json'):
 t=z[r['name']];src,dst=[ps[tuple(ref[1:].split(' > .'))] for ref in [r['from'],r['to']]];actual=[[e['x'],e['y']] for e in t['route']];assert actual==r['world_points_mm'];assert all(e['width']==.16 and e['layer']=='top' for e in t['route']);assert t['route'][0]['start_pcb_port_id']==src['pcb_port_id'] and t['route'][-1]['end_pcb_port_id']==dst['pcb_port_id'];assert t['subcircuit_connectivity_map_key']==sps[src['source_port_id']]['subcircuit_connectivity_map_key']==sps[dst['source_port_id']]['subcircuit_connectivity_map_key'];assert actual[0]==[src['x'],src['y']] and actual[-1]==[dst['x'],dst['y']]
 nominal=unary_union([LineString([v,w]).buffer(.08,quad_segs=128) for v,w in zip(actual,actual[1:])]);stress=unary_union([LineString([v,w]).buffer(.096,quad_segs=128) for v,w in zip(actual,actual[1:])]);pad=g.pad_shape(pads[dst['pcb_port_id']]);assert nominal.intersection(pad).area>1e-10 and nominal.intersection(g.pad_shape(pads[src['pcb_port_id']])).area>1e-10
 row={'name':r['name'],'width_mm':.16,'stress_width_mm':.192,'wire_mm':sum(math.dist(v,w) for v,w in zip(actual,actual[1:])),'stress_EP_gap_mm':stress.distance(ep),'stress_square_gap_mm':stress.distance(square),'stress_circle_gap_mm':stress.distance(circle),'pad_square_gap_mm':pad.distance(square),'pad_circle_gap_mm':pad.distance(circle)};assert all(row[k]>=.15-1e-6 for k in ['stress_EP_gap_mm','stress_square_gap_mm','stress_circle_gap_mm','pad_square_gap_mm','pad_circle_gap_mm']);rows.append(row)
 for via in [e for e in j if e['type']=='pcb_via' and e['subcircuit_connectivity_map_key']!=t['subcircuit_connectivity_map_key']]:
  gap=g.pad_shape(via,True).distance(stress);drills.append({'trace':r['name'],'via':via['pcb_via_id'],'drill_to_stressed_track_mm':gap,'radial_budget_mm':.115,'rule_mm':.2,'adjusted_margin_mm':gap-.115-.2})
assert min(e['adjusted_margin_mm'] for e in drills)>=-1e-6
process=read('artifacts/iteration-9/final-process.json');assert process['summary']['width_plus_20_percent_shorts']==0 and process['summary']['width_plus_20_percent_spacing_findings']==11;assert all(e['a'] not in ['pcb_trace_32','pcb_trace_33'] and e['b'] not in ['pcb_trace_32','pcb_trace_33'] for e in process['width_plus_20_percent_spacing'])
o=read('artifacts/iteration-8/locality.json');n=read('artifacts/iteration-9/final-locality.json');key=lambda e:tuple(e[k] for k in ['a','pa','b','pb']);oldrows={key(e):e for e in o['rows']};lost=[e for e in n['rows'] if oldrows[key(e)]['pass'] and not e['pass']];assert not lost
report={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'baseline_head':'64bd573ccfacad4440be93230c9b65f722527e1f','pose':read('experiments/tolerance/poses.json'),'preserved_non_CP_routes':42,'preserved_non_CP_identities_except_explicit_VREG_enrollment':41,'VREG_exact_route_net_width_and_terminals':True,'VREG_maximum_unchanged_mm':1,'VREG_actual_wire_mm':2.60585631220988,'preserved_via_records':22,'CP_paths':rows,'CP_drill_checks':drills,'minimum_CP_adjusted_drill_margin_mm':min(e['adjusted_margin_mm'] for e in drills),'stress_before_after':[24,11],'introduced_stress_before_after':[13,0],'existing_findings_retained':11,'critical':critical,'locality':{'before':sum(e['pass'] for e in o['rows']),'after':sum(e['pass'] for e in n['rows']),'total':len(n['rows']),'lost':lost},'native_stage_allowed':False,'native_stage_blocker':'11 inherited width-stress failures, 3 inherited combined width/drill failures, VREG 2.605856mm versus native max1mm, and unapproved alternate drill process','manufacturing_qualified':False,'candidate_promoted':False};Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['CP_paths','minimum_CP_adjusted_drill_margin_mm','stress_before_after','locality','native_stage_allowed']},indent=2))
