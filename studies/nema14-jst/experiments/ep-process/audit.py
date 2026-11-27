"""Digital geometry only. No accepted-source edits, new routing or process acceptance."""
import sys,json,math,hashlib,csv
from pathlib import Path
sys.path.insert(0,'experiments/external-star')
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union,nearest_points
r=Path('artifacts/iteration-13');j=read(r/'candidate.circuit.json');cam=read(r/'candidate-cam-review.circuit.json');_,cc,_,ss,_,ps,_=index(j);pads=[e for e in j if e['type']=='pcb_smtpad'];ep=next(e for e in pads if e['width']==3.15);vs=[e for e in j if e['type']=='pcb_via'];epport=next(e for e in j if e['type']=='pcb_port' and e['pcb_port_id']==ep['pcb_port_id']);net=ss[epport['source_port_id']]['subcircuit_connectivity_map_key'];assert len(vs)==4 and all(v['subcircuit_connectivity_map_key']==net for v in vs)
assert len([e for e in j if e['type']=='pcb_trace'])==0
paste=[e for e in cam if e['type']=='pcb_solder_paste' and e['pcb_smtpad_id']==ep['pcb_smtpad_id']];assert len(paste)==4
pastecu=unary_union([box(p['x']-p['width']/2,p['y']-p['height']/2,p['x']+p['width']/2,p['y']+p['height']/2) for p in paste]);coverage=pastecu.area/g.pad_shape(ep).area;assert g.pad_shape(ep).contains(pastecu)
foreign=[p for p in pads if p['port_hints'] not in [['pin3'],['pin18'],['pin29']]]
min_foreign=min(g.pad_shape(v).distance(g.pad_shape(p)) for v in vs for p in foreign)
min_hole_foreign=min(g.pad_shape(v,True).distance(g.pad_shape(p)) for v in vs for p in foreign)
# Map only the proposed vias into the real unchanged comparison geometry, no extra copper.
bb=resolve_copper_nets(b);_,_,pc,sp,pp,ports,_=index(bb);owner={p['pcb_port_id']:n+'.'+pin for (n,pin),p in ports.items()};bn=sp[ports['U_DRV','EP']['source_port_id']]['subcircuit_connectivity_map_key'];centre=ports['U_DRV','EP'];objects=[]
for e in bb:
 t=e['type'];key=e.get('subcircuit_connectivity_map_key');label=e.get('pcb_trace_id',e.get('pcb_via_id',''))
 if t=='pcb_smtpad':
  p=pp[e['pcb_port_id']];key=sp[p['source_port_id']].get('subcircuit_connectivity_map_key');objects.append((owner[e['pcb_port_id']],g.pad_shape(e),[e['layer']],key))
 elif t=='pcb_via':objects.append((label,g.pad_shape(e),e['layers'],key))
 elif t=='pcb_trace':
  for i,(a,z) in enumerate(zip(e['route'],e['route'][1:])):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:objects.append((label+':segment'+str(i),LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])*1.2/2,quad_segs=128),[a['layer']],key))
rows=[]
for i,v in enumerate(vs):
 x=v['x']+centre['x'];y=v['y']+centre['y'];outer=Point(x,y).buffer(.375,quad_segs=128);hole=Point(x,y).buffer(.15,quad_segs=128);layerrows=[]
 for layer in ['top','inner1','inner2','bottom']:
  obs=[o for o in objects if layer in o[2] and o[3]!=bn];o=min(obs,key=lambda o:hole.distance(o[1]));hgap=hole.distance(o[1]);ann=min(obs,key=lambda o:outer.distance(o[1]));agap=outer.distance(ann[1]);layerrows.append({'layer':layer,'nearest_drill_object':o[0],'nominal_drill_edge_clearance_mm':hgap,'conditional_drill_margin_after_0_115_and_0_20_rule_mm':hgap-.115-.20,'nearest_annulus_object':ann[0],'annulus_foreign_copper_gap_mm':agap})
 rows.append({'id':'EP_TV'+str(i+1),'fixture_x_mm':v['x'],'fixture_y_mm':v['y'],'board_x_mm':x,'board_y_mm':y,'CAD_drill_mm':.30,'land_mm':.75,'selective_fill':True,'ground_net':bn,'layers':layerrows})
screws=[e for e in bb if e['type']=='pcb_keepout' and e.get('shape')=='circle' and e.get('radius')==3.2]
for row in rows:
 point=Point(row['board_x_mm'],row['board_y_mm']).buffer(.375,quad_segs=128);row['minimum_circle_screw_gap_mm']=min(point.distance(Point(e['center']['x'],e['center']['y']).buffer(3.2,quad_segs=128)) for e in screws);row['minimum_square_screw_gap_mm']=min(point.distance(box(e['center']['x']-3.2,e['center']['y']-3.2,e['center']['x']+3.2,e['center']['y']+3.2)) for e in screws)
with (r/'selective-fill-xy.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['id','fixture_x_mm','fixture_y_mm','board_x_mm','board_y_mm','CAD_drill_mm','land_mm','selective_fill','ground_net']);w.writeheader();w.writerows([{k:v for k,v in row.items() if k in w.fieldnames} for row in rows])
# Diagnose the real VREG loop without authoring a route. A direct shortest-pad bridge is a diagnostic, not a suggested route.
padsb={e['pcb_port_id']:e for e in bb if e['type']=='pcb_smtpad'};start=g.pad_shape(padsb[ports['C_VREG','pin2']['pcb_port_id']]);end=g.pad_shape(padsb[ports['U_DRV','EP']['pcb_port_id']]);a,z=nearest_points(start,end);line=LineString([a,z]);stroke=line.buffer(.096,quad_segs=128);blockers=[]
for label,poly,layers,key in objects:
 if 'top' not in layers or key==bn:continue
 gap=stroke.distance(poly)
 if gap<.15-1e-9:blockers.append({'object':label,'gap_to_0_192_mm_diagnostic_stroke_mm':gap,'intersects':stroke.intersects(poly)})
cu=g.inspect('artifacts/iteration-11/final.circuit.json');gn=next(e for e in cu['disconnected_nets'] if e['net']=='GND');islands={n:next(i for i,x in enumerate(gn['islands']) if n in x) for n in ['C_VREG.pin2','U_DRV.EP']};assert islands['C_VREG.pin2']!=islands['U_DRV.EP']
endpoint=[]
for phase,x,y,newx in [('A',5.84,7.449873,6.01),('B',9.36,6.949493,9.19)]:
 epold=g.pad_shape(padsb[ports['U_DRV','EP']['pcb_port_id']]);dist=Point(x,y).distance(epold);endpoint.append({'phase':phase,'outside_centre_mm':[x,y],'centre_to_EP_mm':dist,'wire_radius_mm':.30,'endcap_contact_area_mm2':Point(x,y).buffer(.3,quad_segs=128).intersection(epold).area,'inside_control_x_mm':newx,'inside_control_move_mm':abs(newx-x)})
report={'status':'review only; not fabrication qualified','baseline_native_sha256':hashlib.sha256(json.dumps(b,sort_keys=True).encode()).hexdigest(),'coupon_sha256':hashlib.sha256((r/'candidate.circuit.json').read_bytes()).hexdigest(),'native_own_ground_net_verified':True,'native_new_traces':0,'reference_EP_mm':3.15,'via_count':4,'via_hole_land_mm':[.30,.75],'pitch_mm':1.0,'nominal_annulus_mm':.225,'conditional_annulus_after_unchanged_0_115_screen_mm':.11,'actual_via_tolerance_confirmed':False,'minimum_reference_foreign_pad_to_annulus_mm':min_foreign,'minimum_reference_foreign_pad_to_hole_mm':min_hole_foreign,'reference_drill_margin_after_0_115_and_0_20_mm':min_hole_foreign-.315,'paste_area_mm2':pastecu.area,'paste_coverage':coverage,'paste_outer_edge_margin_mm':g.pad_shape(ep).boundary.distance(pastecu),'paste_web_mm':.2,'foil_proposed_mm':.12,'aperture_area_ratio':1.25/(4*.12),'CAM_adapter_is_separate_from_native_circuit':True,'CAM_plated_drill_tools':{'T10':{'diameter_mm':.30,'holes':4}},'selective_fill_only_XY_ids':[x['id'] for x in rows],'existing_same_diameter_vias_not_selected':22,'board_overlay_new_via_only':rows,'full_VREG_loop':{'islands':islands,'closed':False,'complete_loop_length_mm':None,'complete_loop_area_mm2':None,'nearest_edge_bridge_mm':line.length,'diagnostic_line_mm':[list(a.coords)[0],list(z.coords)[0]],'direct_bridge_blockers':blockers,'new_process_required_to_diagnose':False,'new_process_required_for_every_possible_ground_route':False,'reason':'No ground return copper is authored. Direct bridge encounters listed existing foreign copper; an EP via alone would not connect the capacitor. A legal ground route/plane remains separate work; no process approval assumed.'},'endpoint_semantics':{'pinned_checker':'0.0.283,routePointTouchesPad calls isPointInPad; pad contact tests centre, not wire radius','measurements':endpoint,'outside_control_native':read(r/'endpoint-outside-native.json')['by_type'],'inside_control_native':read(r/'endpoint-inside-native.json')['by_type'],'isolated_only_no_full_board_correction_adopted':True},'native_candidate_routing_checks':read(r/'candidate-native.json')['by_type'],'native_source_generated_errors':[e for e in j if 'error' in e['type']],'full_board_opens_unchanged':59,'accepted_source_unchanged':True,'routing_run':False}
assert report['endpoint_semantics']['outside_control_native']=={'pcb_trace_error':2} and report['endpoint_semantics']['inside_control_native']=={}
(r/'digital-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('coverage',coverage,'annulus conditional',.11,'min foreign',min_foreign,'board min drill margin',min(x['conditional_drill_margin_after_0_115_and_0_20_rule_mm'] for v in rows for x in v['layers']),'VREG blockers',blockers)
