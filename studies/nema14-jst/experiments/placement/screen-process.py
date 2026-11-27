"""Named process tolerance screen, with explicit assumptions and no supplier acceptance claim."""
from pathlib import Path
import json,sys,math,hashlib,importlib.util,copy,tempfile
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets
from shapely.geometry import LineString
s=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
p=Path(sys.argv[1]);b=resolve_copper_nets(json.loads(p.read_bytes()));profile=json.load(open('experiments/anchored/process-profile.json'));allowance=profile['published_hole_position_tolerance_mm']+profile['assumed_max_via_hole_diameter_growth_mm']/2+profile['assumed_additional_relative_copper_registration_mm'];sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};spec=json.load(open('experiments/placement/generated.json'));records=[]
for e in b:
 typ=e['type'];key=sp.get(pp.get(e.get('pcb_port_id'),{}).get('source_port_id'),{}).get('subcircuit_connectivity_map_key',e.get('subcircuit_connectivity_map_key'))
 if typ in ['pcb_smtpad','pcb_plated_hole','pcb_via']:records.append({'shape':g.pad_shape(e),'layers':e.get('layers',[e.get('layer','top')]),'net':key,'type':typ,'id':e.get(typ+'_id')})
 elif typ=='pcb_trace':
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:records.append({'shape':LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128),'layers':[a['layer']],'net':key,'type':typ,'id':e['pcb_trace_id']})
 elif typ=='pcb_copper_pour':raise ValueError('Pour not supported by this screen')
rows=[]
for v in [e for e in b if e['type']=='pcb_via']:
 name=next((q['name'] for q in spec['vias'] if math.hypot(q['x']-v['x'],q['y']-v['y'])<1e-9),'automatic:'+v['pcb_via_id']);hole=g.pad_shape(v,True);annulus=g.pad_shape(v).difference(hole);gap=min(hole.distance(e['shape']) for e in records if e['type']=='pcb_smtpad');rad=(v['outer_diameter']-v['hole_diameter'])/2;layers={}
 for layer in v['layers']:
  foreign=[e for e in records if layer in e['layers'] and e['net']!=v['subcircuit_connectivity_map_key']];hd=min((hole.distance(e['shape']) for e in foreign),default=None);ad=min((annulus.distance(e['shape']) for e in foreign),default=None);inner=layer in ['inner1','inner2'];layers[layer]={'nominal_drill_edge_to_foreign_copper_mm':hd,'nominal_annulus_to_foreign_copper_mm':ad,'position_only_drill_clearance_mm':None if hd is None else hd-.075,'assumption_adjusted_drill_clearance_mm':None if hd is None else hd-allowance,'inner_via_rule_mm':.2 if inner else None,'nominal_inner_rule_pass':None if not inner or hd is None else hd>=.2-1e-6,'assumption_adjusted_inner_rule_pass':None if not inner or hd is None else hd-allowance>=.2-1e-6}
 rows.append({'name':name,'pcb_via_id':v['pcb_via_id'],'center_mm':[v['x'],v['y']],'hole_pad_mm':[v['hole_diameter'],v['outer_diameter']],'nominal_hole_edge_to_SMT_copper_mm':gap,'position_only_hole_SMT_clearance_mm':gap-.075,'assumption_adjusted_hole_SMT_clearance_mm':gap-allowance,'nominal_annular_radial_width_mm':rad,'assumption_adjusted_annular_margin_mm':rad-allowance,'layers':layers})
pths=[]
for h in [e for e in b if e['type']=='pcb_plated_hole']:
 key=sp.get(pp.get(h.get('pcb_port_id'),{}).get('source_port_id'),{}).get('subcircuit_connectivity_map_key');hole=g.pad_shape(h,True);ls={}
 for layer in ['inner1','inner2']:
  gap=min((hole.distance(e['shape']) for e in records if layer in e['layers'] and e['net']!=key),default=None);ls[layer]={'nominal_drill_edge_to_foreign_copper_mm':gap,'inner_component_PTH_rule_mm':.3,'assumption_adjusted_gap_mm':None if gap is None else gap-allowance,'assumption_adjusted_rule_pass':None if gap is None else gap-allowance>=.3-1e-6}
 pths.append({'id':h['pcb_plated_hole_id'],'layers':ls})
stress=copy.deepcopy(b)
for e in stress:
 if e['type']=='pcb_trace':
  for n in e['route']:
   if n['route_type']=='wire':n['width']*=1.2
with tempfile.TemporaryDirectory() as td:
 f=Path(td)/'stress.json';f.write_text(json.dumps(stress));c=g.inspect(str(f))
report={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'profile':profile,'radial_hole_clearance_budget_mm':allowance,'finished_table_stack_sum_mm':sum(profile['finished_layers_top_to_bottom_mm']),'conducted_top_to_inner1_barrel_mm':.035/2+.1164+.0152/2,'hole_size_and_registration_budgets_require_procurement_confirmation':True,'vias':rows,'component_PTH_inner_rule_checks':pths,'summary':{'vias':len(rows),'negative_position_only_SMT_margins':sum(v['position_only_hole_SMT_clearance_mm']<0 for v in rows),'negative_assumption_adjusted_SMT_margins':sum(v['assumption_adjusted_hole_SMT_clearance_mm']<0 for v in rows),'negative_assumption_adjusted_annular_margins':sum(v['assumption_adjusted_annular_margin_mm']<0 for v in rows),'assumption_adjusted_inner_via_rule_failures':sum(any(l['assumption_adjusted_inner_rule_pass'] is False for l in v['layers'].values()) for v in rows),'minimum_assumption_adjusted_SMT_margin_mm':min(v['assumption_adjusted_hole_SMT_clearance_mm'] for v in rows),'minimum_assumption_adjusted_annular_margin_mm':min(v['assumption_adjusted_annular_margin_mm'] for v in rows),'width_plus_20_percent_shorts':len(c['shorts']),'width_plus_20_percent_spacing_findings':len(c['clearance_violations'])},'width_plus_20_percent_spacing':c['clearance_violations'],'supplier_acceptance_verified':False,'manufacturing_qualified':False}
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
