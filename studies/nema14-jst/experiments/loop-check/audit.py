"""Independent full-loop/preservation/margin checks. Known native and fab failures remain failures."""
import sys,json,math,copy,hashlib
from pathlib import Path
sys.path.insert(0,'experiments/external-star')
from model import *
from routing_geometry import resolve_copper_nets,pad_cut_topology
from shapely.ops import unary_union
r=Path(sys.argv[1] if len(sys.argv)>1 else 'artifacts/iteration-14');path=r/'candidate.circuit.json';j=resolve_copper_nets(read(path));old=resolve_copper_nets(b);_,cs,pc,ss,pp,ps,courts=index(j)
def traces(data):
 st={e['source_trace_id']:e.get('name') for e in data if e['type']=='source_trace'};return {st[e['source_trace_id']]:e for e in data if e['type']=='pcb_trace'}
a,z=traces(old),traces(j);assert len(a)==44 and len(z)==45
def trace_record(t):
 q=copy.deepcopy(t);cache=q.pop('trace_length');actual=sum(math.dist((u['x'],u['y']),(v['x'],v['y'])) for u,v in zip(t['route'],t['route'][1:]) if u['route_type']==v['route_type']=='wire' and u['layer']==v['layer']);assert abs(cache-actual)<1e-12;return q
for n,t in a.items():assert trace_record(t)==trace_record(z[n]),('prior trace changed',n)
for typ in ['pcb_component','pcb_smtpad','pcb_plated_hole','pcb_via','pcb_board','pcb_hole','pcb_keepout','pcb_courtyard_outline','source_component']:
 assert [e for e in j if e['type']==typ]==[e for e in old if e['type']==typ],typ
cad=lambda data:[{k:v for k,v in e.items() if k not in ['model_obj_url','model_step_url']} for e in data if e['type']=='cad_component'];assert cad(j)==cad(old),'CAD transform changed'
old_sources={e['source_trace_id']:e for e in old if e['type']=='source_trace'}
for e in j:
 if e['type']=='source_trace' and e['source_trace_id'] in old_sources:assert e==old_sources[e['source_trace_id']]
pads={e['pcb_port_id']:e for e in j if e['type']=='pcb_smtpad'};vs=[e for e in j if e['type']=='pcb_via'];holes=unary_union([g.pad_shape(e,True) for e in j if e['type'] in ['pcb_via','pcb_hole','pcb_plated_hole']]);t=z['VREG_GROUND_LOOP'];net=t['subcircuit_connectivity_map_key'];points=[(q['x'],q['y']) for q in t['route']];line=LineString(points);assert abs(t['trace_length']-line.length)<1e-12;newsource=next(e for e in j if e['type']=='source_trace' and e.get('name')=='VREG_GROUND_LOOP');assert newsource['max_length']==1 and set(newsource['connected_source_port_ids'])=={ps['C_VREG','pin2']['source_port_id'],ps['U_DRV','EP']['source_port_id']};wire=line.buffer(.08,quad_segs=128);stressed=line.buffer(.096,quad_segs=128);assert all(q['width']==.16 and q['layer']=='top' for q in t['route']);assert wire.intersection(holes).area<1e-10
# Native logical endpoints must coincide with real copper, and the complete physical ground must reach EP.
for selector,node,field in [(('C_VREG','pin2'),t['route'][0],'start_pcb_port_id'),(('U_DRV','EP'),t['route'][-1],'end_pcb_port_id')]:
 p=ps[selector];assert node[field]==p['pcb_port_id'] and Point(node['x'],node['y']).within(g.pad_shape(pads[p['pcb_port_id']]))
cu=g.inspect(str(path));(r/'baseline.circuit.json').write_text(json.dumps(old,indent=2)+'\n');orig=g.inspect(str(r/'baseline.circuit.json'));stress=copy.deepcopy(j)
for e in stress:
 if e['type']=='pcb_trace':
  for q in e['route']:
   if q['route_type']=='wire':q['width']*=1.2
(r/'stressed.circuit.json').write_text(json.dumps(stress,indent=2)+'\n');stresscu=g.inspect(str(r/'stressed.circuit.json'))
checks=['shorts','clearance_violations','drill_spacing_violations','hole_trace_violations','board_edge_violations','screw_keepout_violations'];assert all(not cu[k] and not stresscu[k] for k in checks)
G=next(e for e in cu['disconnected_nets'] if e['net']=='GND');oldG=next(e for e in orig['disconnected_nets'] if e['net']=='GND');island=lambda rows,p:next(i for i,x in enumerate(rows) if p in x);assert island(G['islands'],'C_VREG.pin2')==island(G['islands'],'U_DRV.EP');assert island(oldG['islands'],'C_VREG.pin2')!=island(oldG['islands'],'U_DRV.EP');assert not any(e['net']=='VREG' for e in cu['disconnected_nets'])
foreign=[];same=[]
for e in j:
 typ=e['type'];key=e.get('subcircuit_connectivity_map_key');label=e.get('pcb_trace_id',e.get('pcb_via_id',''))
 if typ=='pcb_smtpad' and e['layer']=='top':
  p=pp[e['pcb_port_id']];key=ss[p['source_port_id']].get('subcircuit_connectivity_map_key');poly=g.pad_shape(e);label=pc[e['pcb_component_id']]+'.'+ss[p['source_port_id']]['name']
 elif typ=='pcb_via' and 'top' in e['layers']:poly=g.pad_shape(e)
 elif typ=='pcb_trace' and e['pcb_trace_id']!=t['pcb_trace_id']:
  for i,(u,v) in enumerate(zip(e['route'],e['route'][1:])):
   if u['route_type']==v['route_type']=='wire' and u['layer']==v['layer']=='top':
    poly=LineString([(u['x'],u['y']),(v['x'],v['y'])]).buffer(max(u['width'],v['width'])*.6,quad_segs=128)
    if key!=net:foreign.append((label+':'+str(i),poly))
    else:same.append(poly)
  continue
 else:continue
 if key!=net:foreign.append((label,poly))
rows=sorted([{'object':n,'nominal_gap_mm':wire.distance(poly),'simultaneous_stressed_gap_mm':stressed.distance(poly)} for n,poly in foreign],key=lambda q:q['simultaneous_stressed_gap_mm']);assert rows[0]['simultaneous_stressed_gap_mm']>=.15-1e-6
EP=g.pad_shape(pads[ps['U_DRV','EP']['pcb_port_id']]);shared=stressed.intersection(unary_union(same)).difference(EP).area;assert shared<1e-10
# Supplemental simultaneous stress/foreign drill check; old two all-SMT star failures are retained independently.
combined=[]
for name,tr in z.items():
 for i,(u,v) in enumerate(zip(tr['route'],tr['route'][1:])):
  if u['route_type']!=v['route_type'] or u['route_type']!='wire' or u['layer']!=v['layer']:continue
  poly=LineString([(u['x'],u['y']),(v['x'],v['y'])]).buffer(max(u['width'],v['width'])*.6,quad_segs=128)
  for via in vs:
   if u['layer'] in via['layers'] and tr['subcircuit_connectivity_map_key']!=via['subcircuit_connectivity_map_key']:combined.append({'path':name,'segment':i,'via':via['pcb_via_id'],'layer':u['layer'],'margin_mm':g.pad_shape(via,True).distance(poly)-.115-.2})
assert all(x['margin_mm']>=-1e-6 for x in combined)
smts=[]
for v in vs:
 d=min(g.pad_shape(v,True).distance(g.pad_shape(p)) for p in pads.values());
 if d-.115<0:smts.append({'via':v['pcb_via_id'],'nominal_hole_SMT_mm':d,'unchanged_adjusted_margin_mm':d-.115})
assert len(smts)==2
# Exact same inline-shunt net copper, plus real cut proofs; new GND cannot participate in those winding nets.
kelvin=[]
for phase in 'AB':
 for pole,pin,target in [('POS','pin1',('U_DRV','OUT1A' if phase=='A' else 'OUT2A')),('NEG','pin2',('J_MOTOR',phase+'_PLUS'))]:
  p=ps['R_SHUNT_'+phase,pin];key=ss[p['source_port_id']]['subcircuit_connectivity_map_key'];assert key!=net;pad=g.pad_shape(pads[p['pcb_port_id']]);result=pad_cut_topology(j,key,p['pcb_port_id'],ps['U_I'+phase,'IN_'+pole]['pcb_port_id'],ps[target]['pcb_port_id'],pad,'top',g.pad_shape);assert result['actual_shunt_pad_is_required_pickup'];kelvin.append({'phase':phase,'pole':pole,**result})
# Complete external copper travel includes both endpoints and pad access; internal device paths are unknown.
p=z['AUTHORED_VREG_BASELINE'];ppts=[(q['x'],q['y']) for q in p['route']];vreg=ps['U_DRV','VREG'];cp=ps['C_VREG','pin1'];cg=ps['C_VREG','pin2'];ep=ps['U_DRV','EP'];xy=lambda v:(v['x'],v['y']);positive=math.dist(xy(vreg),ppts[0])+LineString(ppts).length+math.dist(ppts[-1],xy(cp));ground=line.length;reference=[xy(vreg)]+ppts+[xy(cp),xy(cg)]+points+[xy(ep),xy(vreg)];poly=Polygon(reference);assert poly.is_valid
# Necessary bound for any orthogonal top-side pose of this cap with non-overlapping retained rectangular courtyards.
dcourt=courts['U_DRV'];ccourt=courts['C_VREG'];capground=g.pad_shape(pads[cg['pcb_port_id']]);eb=EP.bounds;db=dcourt.bounds;cb=ccourt.bounds;gb=capground.bounds;driverinsets=[eb[0]-db[0],eb[1]-db[1],db[2]-eb[2],db[3]-eb[3]];capinsets=[gb[0]-cb[0],gb[1]-cb[1],cb[2]-gb[2],cb[3]-gb[3]];lower=min(driverinsets)+min(capinsets)-.16;assert lower>1
native=read(r/'native.json.all-routing.json');long=[e for e in native['findings'] if e['type']=='pcb_trace_too_long_error'];assert len(long)==1 and long[0]['pcb_trace_id']==t['pcb_trace_id'] and long[0]['maximum_trace_length']==1
report={'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'baseline':'a01fd79,unchanged r11 all-top native geometry','new_paths':1,'preserved_whole_pcb_trace_records':44,'preserved_via_whole_records':22,'all_component_poses_pads_CAD_courtyards_mechanical_and_old_sources_exact':True,'positive_wire_mm':LineString(ppts).length,'ground_wire_mm':ground,'positive_full_pad_centre_travel_mm':positive,'ground_full_pad_centre_travel_mm':ground,'total_external_PCB_copper_travel_mm':positive+ground,'capacitor_terminal_centre_span_mm':math.dist(xy(cp),xy(cg)),'driver_EP_VREG_terminal_centre_chord_mm':math.dist(xy(ep),xy(vreg)),'terminal_closure_reference_polygon_area_mm2':poly.area,'terminal_closure_reference_perimeter_mm':LineString(reference).length,'area_is_actual_internal_current_loop':False,'internal_capacitor_and_silicon_current_paths_known':False,'complete_external_decoupling_connections_verified':True,'driver_GND3_external_tie_to_EP_present':island(G['islands'],'U_DRV.GND')==island(G['islands'],'U_DRV.EP'),'driver_GND18_external_tie_to_EP_present':island(G['islands'],'U_DRV.GND18')==island(G['islands'],'U_DRV.EP'),'VBB_ceramic_ground_to_EP_present':island(G['islands'],'C_VM.pin2')==island(G['islands'],'U_DRV.EP'),'ground_island_count_before_after':[len(oldG['islands']),len(G['islands'])],'full_board_disconnected_nets_before_after':[len(orig['disconnected_nets']),len(cu['disconnected_nets'])],'nominal_independent':{k:len(cu[k]) for k in checks},'simultaneous_plus20_percent_width':{k:len(stresscu[k]) for k in checks},'new_route_closest_foreign_objects':rows[:12],'new_route_shared_existing_GND_trace_area_outside_EP_mm2':shared,'new_route_crosses_any_real_drill':False,'supplemental_foreign_drill_failures':[],'supplemental_foreign_drill_minimum_margin_mm':min(x['margin_mm'] for x in combined),'supplemental_new_route_foreign_drill_minimum_margin_mm':min(x['margin_mm'] for x in combined if x['path']=='VREG_GROUND_LOOP'),'inherited_all_SMT_star_hole_failures':smts,'Kelvin_real_pad_cuts':kelvin,'sense_returns_mm_unchanged':[4.891753690204,4.752642038738],'native':{'by_type':native['by_type'],'new_ground_length_error':long[0],'limit_overridden':False},'placement_limit_bound':{'assumptions':['Retained rectangular top-side U_DRV and C_VREG courtyards do not overlap','Only orthogonal capacitor poses; no courtyard/footprint/side change','Physical pad edge gap minus both0.08mm trace end caps is an optimistic wire-length lower bound'],'driver_EP_to_courtyard_axis_insets_mm':driverinsets,'cap_ground_to_own_courtyard_axis_insets_mm':capinsets,'any_orthogonal_legal_pad_gap_lower_bound_mm':lower+.16,'any_orthogonal_legal_wire_length_lower_bound_mm':lower,'current_pad_edge_gap_mm':capground.distance(EP),'current_wire_length_lower_bound_mm':capground.distance(EP)-.16,'native_ground_max_mm':1,'necessary_aggregate_courtyard_inset_or_native_budget_change_mm':lower-1,'native_budget_for_this_actual_route_mm':ground,'proof_scope':'Axis separation of disjoint rectangles; no claim for different footprints, nonorthogonal rotations or another assembly side'},'no_new_process_or_vias':True,'controller_promoted':False,'fabrication_qualified':False,'autorouter_run':False}
(r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print('External copper travel',positive+ground,'groundwire',ground,'stress minimum',rows[0],'GND islands',report['ground_island_count_before_after'],'native length gate retained');print('Any orthogonal courtyard-legal wire lower bound',lower)
