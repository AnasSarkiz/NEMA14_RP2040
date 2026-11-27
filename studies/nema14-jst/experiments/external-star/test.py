"""Replay both rejected external controls, preserving source, real current flow and VREG-loop truth."""
from pathlib import Path
import json,copy,subprocess,sys,math
sys.path.insert(0,'experiments/external-star')
from model import read
from audit import audit
r=Path('artifacts/iteration-12');tmp=Path('.config/external-star-test');tmp.mkdir(parents=True,exist_ok=True)
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def records(data,typ):
 out=copy.deepcopy([e for e in data if e['type']==typ])
 if typ=='pcb_trace':
  for e in out:
   actual=sum(math.dist([a['x'],a['y']],[z['x'],z['y']]) for a,z in zip(e['route'],e['route'][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']);assert abs(e.pop('trace_length')-actual)<1e-12
 return out
for mode in ['external','direct']:
 p=tmp/(mode+'.json');run(['bun','experiments/external-star/render.ts',str(p)]+(['--top-direct'] if mode=='direct' else []));old,new=read(r/(mode+'.circuit.json')),read(p)
 for typ in ['source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_via','pcb_trace','pcb_board','pcb_hole','pcb_keepout','pcb_courtyard_outline']:assert records(old,typ)==records(new,typ),('Native replay drift',mode,typ)
 q=audit(p);assert q['preserved_nonreturn_route_arrays']==38 and q['preserved_other_via_whole_records']==18;assert q['independent']['disconnected_nets']==59 and not q['full_VREG_loop']['closed_copper_loop_exists'];assert all(not e['actual_0_60_width_pass'] and e['intermediate_land_required_after_actual_pad_cut'] and .28<e['middle_cross_section_copper_upper_bound_mm']<.281 for e in q['returns']);assert not q['candidate_promoted'] and not q['native_routing_attempted'];native=read(r/(mode+'-native.json'));assert all(e['count']==0 for e in native.values());allnative=read(r/(mode+'-native.json.all-routing.json'));assert allnative['by_type']=={'pcb_port_not_connected_error':298,'pcb_trace_style_warning':4,'pcb_trace_error':2};process=read(r/(mode+'-process.json'));assert all(process['summary'][k]==0 for k in ['negative_position_only_SMT_margins','negative_assumption_adjusted_SMT_margins','negative_assumption_adjusted_annular_margins','assumption_adjusted_inner_via_rule_failures','width_plus_20_percent_shorts','width_plus_20_percent_spacing_findings'])
 if mode=='external':assert q['returns'][0]['individual_barrel_links_required']==[True,True] and q['returns'][0]['authored_serial_path_mm']>5 and q['returns'][1]['individual_barrel_links_required']==[False,False]
 else:assert len(q['unused_via_port_metadata_deltas'])==6 and all(e['hole_avoiding_path_fits_5mm'] and e['does_not_qualify_return'] and not e['path_is_0_60mm_wide'] for e in q['returns'])
# Physical restrictions cannot be hidden by pad/net/width/cache mutations.
for kind in ['EP_land','real_pin_net','fixed_CP','return_width','VREG_cache','VREG_limit','board_clearance']:
 bad=copy.deepcopy(read(r/'direct.circuit.json'));st={e['source_trace_id']:e.get('name','') for e in bad if e['type']=='source_trace'}
 if kind=='EP_land':driver=next(e['source_component_id'] for e in bad if e['type']=='source_component' and e.get('name')=='U_DRV');pc=next(e['pcb_component_id'] for e in bad if e['type']=='pcb_component' and e['source_component_id']==driver);p=next(e for e in bad if e['type']=='pcb_smtpad' and e['pcb_component_id']==pc and e.get('port_hints')==['pin29']);p['width']=math.nextafter(p['width'],math.inf)
 elif kind=='real_pin_net':p=next(e for e in bad if e['type']=='source_port' and e.get('name')=='VREG');p['subcircuit_connectivity_map_key']='wrong-net'
 elif kind=='VREG_limit':next(e for e in bad if e['type']=='source_trace' and e.get('name')=='AUTHORED_VREG_BASELINE')['max_length']=3
 elif kind=='board_clearance':next(e for e in bad if e['type']=='pcb_board')['min_trace_to_pad_edge_clearance']=.14
 else:
  name={'fixed_CP':'AUTHORED_CP1_CORRIDOR','return_width':'RETURN_A_EP','VREG_cache':'AUTHORED_VREG_BASELINE'}[kind];t=next(e for e in bad if e['type']=='pcb_trace' and st[e['source_trace_id']]==name)
  if kind=='fixed_CP':t['route'][1]['x']=math.nextafter(t['route'][1]['x'],math.inf)
  elif kind=='return_width':t['route'][0]['width']=.3
  else:t['trace_length']=.5
 p=tmp/(kind+'.json');p.write_text(json.dumps(bad))
 try:audit(p)
 except (AssertionError,ValueError,KeyError):pass
 else:raise AssertionError('Mutation not rejected '+kind)
run(['bun','experiments/external-star/render-reference.ts',str(tmp/'reference.json')]);assert records(read(r/'reference.circuit.json'),'pcb_smtpad')==records(read(tmp/'reference.json'),'pcb_smtpad');assert all(not e['failed_pairs'] and e['minimum_margin_mm']>0 for e in read(r/'combined-drill-width.json'));assert all(e['hole_subtracted_continuity'] for entry in read(r/'local-branches.json') for e in entry['branches']);refnative=read(r/'reference-native.json');assert all(e['count']==0 for e in refnative.values());ref=read(r/'manufacturer-comparison.json');assert ref['fitted_native_MPN']=='A4988SETTR-T' and all(abs(g-.25)<1e-12 for g in ref['manufacturer_reference_summary']['EP_ground_pad_gaps_mm'].values());assert not ref['manufacturer_reference_summary']['ordinary_0_30_hole_fits_between_EP_and_ground_land_even_before_tolerances'];assert ref['production_land_pattern_unchanged'];assert all(e['source_and_physical_copper_exact'] for e in read(r/'cli-replay.json')['runs'])
print('PASS: two bounded external native controls;38 fixed paths/18 exact other vias;0 drill/stress findings but compulsory0.280010mm ground-land neck rejects0.60mm return. Actual barrel bypasses identified; full VREG ground loop open;59 nets remain; no promotion/routing/footprint change.')
