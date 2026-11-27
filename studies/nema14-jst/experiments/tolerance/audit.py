"""Native CLI physical replay and supplemental combined width/drill audit; no gate replacement."""
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
import hashlib
r=Path('artifacts/iteration-9');j=resolve_copper_nets(read(r/'final.circuit.json'));cli=resolve_copper_nets(read(r/'native-cli.circuit.json'));st={e['source_trace_id']:e.get('name','') for e in j if e['type']=='source_trace'}
for typ in ['source_port','source_net','source_trace','pcb_component','pcb_smtpad','pcb_plated_hole','pcb_via','pcb_board','pcb_hole','pcb_keepout']:
 assert [e for e in j if e['type']==typ]==[e for e in cli if e['type']==typ],('CLI source/physical mismatch',typ)
a={e['pcb_trace_id']:e for e in j if e['type']=='pcb_trace'};z={e['pcb_trace_id']:e for e in cli if e['type']=='pcb_trace'};fields=['route_type','x','y','width','layer'];metadata=[]
for k,t in a.items():
 assert t['subcircuit_connectivity_map_key']==z[k]['subcircuit_connectivity_map_key'];assert [{f:q.get(f) for f in fields} for q in t['route']]==[{f:q.get(f) for f in fields} for q in z[k]['route']]
 for n,(q,w) in enumerate(zip(t['route'],z[k]['route'])):
  for f in ['start_pcb_port_id','end_pcb_port_id']:
   if q.get(f)!=w.get(f):assert f=='end_pcb_port_id' and f not in w;metadata.append({'trace':st[t['source_trace_id']],'node':n,'API_annotation':q[f],'CLI_missing_field':f})
assert len(metadata)==3
vias=[e for e in j if e['type']=='pcb_via'];specs=read('experiments/placement/generated.json')['vias']+read('experiments/reconnect/vias.json');via_names={e['pcb_via_id']:next(q['name'] for q in specs if math.dist([e['x'],e['y']],[q['x'],q['y']])<1e-9) for e in vias};rows=[];worst=[]
for t in a.values():
 polys={}
 for v,w in zip(t['route'],t['route'][1:]):
  if v['route_type']==w['route_type']=='wire' and v['layer']==w['layer']:polys.setdefault(v['layer'],[]).append(LineString([(v['x'],v['y']),(w['x'],w['y'])]).buffer(max(v['width'],w['width'])*.6,quad_segs=128))
 for layer,shapes in polys.items():
  wire=unary_union(shapes)
  for via in vias:
   if layer not in via['layers'] or via['subcircuit_connectivity_map_key']==t['subcircuit_connectivity_map_key']:continue
   gap=g.pad_shape(via,True).distance(wire);row={'path':st[t['source_trace_id']],'via':via['pcb_via_id'],'via_name':via_names[via['pcb_via_id']],'layer':layer,'drill_edge_to_stressed_foreign_trace_mm':gap,'radial_budget_mm':.115,'unchanged_published_rule_mm':.2,'adjusted_margin_mm':gap-.115-.2}
   rows.append(row)
   if row['adjusted_margin_mm']<-1e-6:worst.append(row)
assert not any(x['path'] in ['AUTHORED_CP1_CORRIDOR','AUTHORED_CP2_CORRIDOR'] for x in worst)
# Report the newly visible native VREG limit and geometric lower bounds without overriding it.
_,_,_,ss,ppp,ports,_=index(j);pads={e['pcb_port_id']:e for e in j if e['type']=='pcb_smtpad'};vreg=[ports['U_DRV','VREG'],ports['C_VREG','pin1']];centre=math.dist([vreg[0]['x'],vreg[0]['y']],[vreg[1]['x'],vreg[1]['y']]);edges=g.pad_shape(pads[vreg[0]['pcb_port_id']]).distance(g.pad_shape(pads[vreg[1]['pcb_port_id']]))
report={'API_input_sha256':hashlib.sha256((r/'final.circuit.json').read_bytes()).hexdigest(),'CLI_input_sha256':hashlib.sha256((r/'native-cli.circuit.json').read_bytes()).hexdigest(),'CLI_physical_copper_net_and_widths_exactly_match':True,'CLI_source_contract_and_mechanics_exactly_match':True,'only_missing_nonphysical_endpoint_annotations':metadata,'supplemental_combined_width_and_drill_screen':{'replaces_existing_gate':False,'width_multiplier':1.2,'radial_drill_budget_mm':.115,'hole_to_foreign_track_rule_mm':.2,'checked_via_trace_layer_pairs':len(rows),'failed_pairs':worst,'failure_count':len(worst),'CP_failed_pairs':0,'minimum_CP_margin_mm':min(e['adjusted_margin_mm'] for e in rows if e['path'] in ['AUTHORED_CP1_CORRIDOR','AUTHORED_CP2_CORRIDOR']),'supplier_acceptance':False},'VREG_length_gate':{'new_source_owner':'AUTHORED_VREG_BASELINE','former_source_owner':'source_trace_188, one physical port plus net.VREG, no max_length field','new_native_max_length_mm':1,'unchanged_actual_wire_mm':2.60585631220988,'current_port_centre_lower_bound_mm':centre,'physical_pad_edge_lower_bound_mm':edges,'centre_translation_lower_bound_for_1mm_centreline_mm':centre-1,'native_error_retained':True,'no_length_limit_override':True},'native_routing_attempted':False,'manufacturing_qualified':False}
(r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print('CLI matches physical data; combined screen',len(worst),'inherited failed pairs, CP0; VREG lower bounds',centre,edges)
