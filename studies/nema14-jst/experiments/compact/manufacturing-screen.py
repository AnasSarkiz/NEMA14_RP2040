"""Separate nominal geometric clearances and conservative tolerance sensitivities.
A published capability table is not acceptance of this stack, process or board.
"""
from pathlib import Path
import json,sys,hashlib,importlib.util,math
sys.path.insert(0,'scripts');from routing_geometry import resolve_copper_nets
from shapely.geometry import LineString,Point
spec=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
p=Path(sys.argv[1]);b=resolve_copper_nets(json.loads(p.read_bytes()));board=next(e for e in b if e['type']=='pcb_board');sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};records=[]
for e in b:
 typ=e['type'];key=sp.get(pp.get(e.get('pcb_port_id'),{}).get('source_port_id'),{}).get('subcircuit_connectivity_map_key',e.get('subcircuit_connectivity_map_key'))
 if typ in ['pcb_smtpad','pcb_plated_hole','pcb_via']:records.append({'geometry':g.pad_shape(e),'layers':e.get('layers',[e.get('layer','top')]),'net':key,'type':typ,'id':e.get(typ+'_id')})
 elif typ=='pcb_trace':
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:records.append({'geometry':LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128),'layers':[a['layer']],'net':key,'type':typ,'id':e['pcb_trace_id']})
 elif typ=='pcb_copper_pour':raise ValueError('Pour geometry must be implemented before using this screen on a pour board')
rows=[]
for v in [e for e in b if e['type']=='pcb_via']:
 hole=g.pad_shape(v,True);annulus=g.pad_shape(v).difference(hole);same=[e for e in records if e['type']=='pcb_smtpad'];near=sorted([{'id':e['id'],'nominal_hole_edge_to_smt_copper_mm':hole.distance(e['geometry'])} for e in same],key=lambda e:e['nominal_hole_edge_to_smt_copper_mm']);foreign=[e for e in records if e['net']!=v.get('subcircuit_connectivity_map_key')];layers={}
 for layer in v['layers']:
  rs=[e for e in foreign if layer in e['layers']];nearest=min(rs,key=lambda e:hole.distance(e['geometry'])) if rs else None;hd=hole.distance(nearest['geometry']) if nearest else None;ad=min((annulus.distance(e['geometry']) for e in rs),default=None);inner=layer in ['inner1','inner2']
  track_gap=min((hole.distance(e['geometry']) for e in rs if e['type']=='pcb_trace'),default=None)
  layers[layer]={'nearest_foreign_id':nearest['id'] if nearest else None,'nominal_drill_edge_to_foreign_copper_mm':hd,'nominal_annulus_to_foreign_copper_mm':ad,'position_only_adjusted_drill_clearance_mm':hd-.075 if hd is not None else None,'published_inner_via_hole_rule_mm':.2 if inner else None,'nominal_inner_via_rule_pass':hd>=.2-1e-6 if inner and hd is not None else None,'position_adjusted_inner_via_rule_pass':hd-.075>=.2-1e-6 if inner and hd is not None else None,'published_via_hole_to_track_mm':.2,'nominal_hole_to_foreign_track_mm':track_gap,'position_adjusted_hole_to_foreign_track_mm':track_gap-.075 if track_gap is not None else None,'nominal_via_hole_to_track_rule_pass':track_gap>=.2-1e-6 if track_gap is not None else None,'position_adjusted_via_hole_to_track_rule_pass':track_gap-.075>=.2-1e-6 if track_gap is not None else None}
 gap=near[0]['nominal_hole_edge_to_smt_copper_mm'];radial=(v['outer_diameter']-v['hole_diameter'])/2
 rows.append({'pcb_via_id':v['pcb_via_id'],'center_mm':[v['x'],v['y']],'outer_hole_mm':[v['outer_diameter'],v['hole_diameter']],'nearest_smt':near[0],'nominal_smt_hole_gap_mm':gap,'position_only_smt_hole_gap_mm':gap-.075,'position_only_smt_nonoverlap':gap-.075>=0,'additional_size_sensitivity_mm':gap-.075-.13/2,'size_sensitivity_is_not_confirmed_via_process_tolerance':True,'nominal_radial_annulus_mm':radial,'conservative_position_only_radial_annulus_budget_mm':radial-.075,'specific_via_preferred_diameter_difference_mm':.15,'specific_via_diameter_difference_mm':v['outer_diameter']-v['hole_diameter'],'layers':layers,'fabrication_qualified':False})
pth=[]
for h in [e for e in b if e['type']=='pcb_plated_hole']:
 key=sp.get(pp.get(h.get('pcb_port_id'),{}).get('source_port_id'),{}).get('subcircuit_connectivity_map_key');hole=g.pad_shape(h,True);rows_inner={}
 for layer in ['inner1','inner2']:
  foreign=[e for e in records if layer in e['layers'] and e['net']!=key];gap=min((hole.distance(e['geometry']) for e in foreign),default=None);rows_inner[layer]={'published_component_pth_hole_to_copper_mm':.3,'nominal_gap_mm':gap,'position_adjusted_gap_mm':gap-.075 if gap is not None else None,'nominal_rule_pass':gap>=.3-1e-6 if gap is not None else None,'position_adjusted_rule_pass':gap-.075>=.3-1e-6 if gap is not None else None}
 pth.append({'pcb_plated_hole_id':h['pcb_plated_hole_id'],'inner_layers':rows_inner,'supplier_acceptance_verified':False})
r={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':'https://jlcpcb.com/capabilities/Capabilities','retrieved_utc':'2026-11-27','defined_board':{'layers':board['num_layers'],'thickness_mm':board['thickness']},'via_process_model':'Ordinary mechanically drilled plated through-via; no approved filled/capped via-in-pad or laser blind/buried process. Source hole is treated as nominal geometry, not a confirmed production drill-tool diameter.','unknown_process_fields':['dielectric stack','copper weights','drill-tool compensation and via hole-size tolerance','copper registration','mask opening/tenting and assembly review'],'position_tolerance_mm':.075,'published_inner_via_hole_to_foreign_copper_mm':.2,'published_inner_component_pth_hole_rule_mm':.3,'component_pth_rule_not_substituted_for_via_rule':True,'supplier_acceptance_verified':False,'component_pth_inner_rule_checks':pth,'vias':rows};Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n');print('vias',len(rows),'position-only SMT failures',sum(not e['position_only_smt_nonoverlap'] for e in rows),'position-only inner failures',sum(any(e['layers'][l]['position_adjusted_inner_via_rule_pass'] is False for l in ['inner1','inner2']) for e in rows))
