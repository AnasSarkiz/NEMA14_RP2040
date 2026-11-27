"""Optimistic EP-return access bound using only real top pads; extra copper cannot open this set.
Polygonal curves converge at two resolutions. Radius sweep is bounded evidence, not a global process proof.
"""
from model import *
from shapely.ops import unary_union,nearest_points
r=Path('artifacts/iteration-10');j=read(r/'final.circuit.json');_,_,_,sp,_,ps,_=index(j);pads=[e for e in j if e['type']=='pcb_smtpad' and e['layer']=='top'];pm={e['pcb_port_id']:e for e in pads};ground=sp[ps['U_DRV','EP']['source_port_id']]['subcircuit_connectivity_map_key'];key=lambda e:sp[next(p for p in j if p['type']=='pcb_port' and p['pcb_port_id']==e['pcb_port_id'])['source_port_id']].get('subcircuit_connectivity_map_key');regionbox=box(3,3,12.5,12);ep=g.pad_shape(pm[ps['U_DRV','EP']['pcb_port_id']]);cases=[]
for resolution in [128,256]:
 free=regionbox.difference(unary_union([g.pad_shape(e).buffer(.36+.15,quad_segs=resolution) for e in pads if key(e)!=ground]));component=next(p for p in (list(free.geoms) if hasattr(free,'geoms') else [free]) if p.covers(Point(ps['U_DRV','EP']['x'],ps['U_DRV','EP']['y'])));closed=not component.boundary.intersects(regionbox.boundary)
 for radius in [.275,.30,.35,.40,.45,.5,.6,.75,1.0,1.5,2.0]:
  forbidden=unary_union([g.pad_shape(e).buffer(.15+.115 if key(e)==ground else radius+.15,quad_segs=resolution) for e in pads]);allowed=regionbox.difference(forbidden);reachable=allowed.intersection(component.buffer(radius,quad_segs=resolution));cases.append({'quad_segments':resolution,'pad_diameter_mm':radius*2,'hole_diameter_mm':.3,'reachable_centre_area_mm2':reachable.area,'EP_trace_component_closed_by_foreign_pad_buffers':closed,'component_bounds_mm':component.bounds})
gaps=[]
for terminal in ['GND18','GND']:
 pad=g.pad_shape(pm[ps['U_DRV',terminal]['pcb_port_id']]);gap=ep.distance(pad);gaps.append({'EP_to_terminal':terminal,'pad_edge_gap_mm':gap,'ideal_centred_original_hole_edge_gap_mm':(gap-.3)/2,'best_possible_margin_under_unchanged_radial_budget_mm':(gap-.3)/2-.115,'required_gap_for_0_30_hole_and_two_0_115_margins_mm':.53,'gap_shortfall_mm':.53-gap,'maximum_hole_for_this_gap_and_two_0_115_margins_mm':gap-.23})
assert all(e['reachable_centre_area_mm2']==0 and e['EP_trace_component_closed_by_foreign_pad_buffers'] for e in cases)
out={'assumptions':{'stressed_return_width_mm':.72,'foreign_copper_clearance_mm':.15,'original_hole_mm':.30,'radial_drill_budget_mm':.115,'original_pad_diameter_mm':.55,'only_SMT_obstacles_used':True,'annular_access_optimistically_allowed_up_to_full_outer_radius':True,'all_SMT_drill_budget_including_same_net_preserved':True,'actual_board_layers_and_other_copper_can_only_reduce_available_space':True},'bounded_via_radius_cases':cases,'local_GND_gap_bounds':gaps,'scope':'Bounded pad/radius screening and local analytic bounds; no alternate footprint or via-in-pad process qualification','smallest_process_decision':'Supplier-supported smaller finished via holes or qualified via-in-pad handling would change the retained rule/process assumptions; neither is adopted. Original-hole return margin remains blocked.','manufacturing_qualified':False};(r/'EP-domain.json').write_text(json.dumps(out,indent=2)+'\n');print(gaps)
# Actual copper plot; no invented board or copper.
colors={'EP':'#7bb1cf','GND18':'#7bb1cf','GND':'#7bb1cf'};svg=['<svg xmlns="http://www.w3.org/2000/svg" width="950" height="1000" viewBox="3.7 -11.8 7.8 8.2">','<rect x="3.7" y="-11.8" width="7.8" height="8.2" fill="white"/>','<text x="3.9" y="-11.4" font-size=".18">NEMA14 JST — original-hole return access (top copper, mm)</text>','<text x="3.9" y="-11.05" font-size=".14">Blue: ground pads; grey: other pads; orange: ±0.115 radial drill budget</text>']
for e in pads:
 shape=g.pad_shape(e)
 if shape.distance(ep)>1.1:continue
 n=next((k[1] for k,p in ps.items() if k[0]=='U_DRV' and p['pcb_port_id']==e['pcb_port_id']),None);pts=' '.join(f'{x},{-y}' for x,y in shape.exterior.coords);svg.append(f'<polygon points="{pts}" fill="{colors.get(n,"#c4c8ce")}" stroke="#444" stroke-width=".008"/>')
for v in [e for e in j if e['type']=='pcb_via' and 5.7<e['x']<9.5 and 6.8<e['y']<7.6]:
 x,y=v['x'],-v['y'];svg.append(f'<circle cx="{x}" cy="{y}" r=".275" fill="none" stroke="#126e5c" stroke-width=".025"/><circle cx="{x}" cy="{y}" r=".265" fill="none" stroke="#e27a18" stroke-width=".018" stroke-dasharray=".04 .03"/><circle cx="{x}" cy="{y}" r=".15" fill="white" stroke="#111" stroke-width=".01"/>')
svg+=['<text x="3.9" y="-4.15" font-size=".15">EP/peripheral GND gap ≈0.450 mm; required 0.530 mm for 0.30 + 2×0.115.</text>','<text x="3.9" y="-3.85" font-size=".15">The unchanged original-hole tolerance screen remains rejected.</text>','</svg>'];(r/'EP-domain.svg').write_text('\n'.join(svg))
