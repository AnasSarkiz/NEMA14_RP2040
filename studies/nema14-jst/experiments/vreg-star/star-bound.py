"""Driver-local necessary access test, including nominal and stressed wire end-cap reach.
This deliberately omits all extra traces and every other layer to make the bound permissive.
"""
from model import *
from shapely.ops import unary_union
r=Path('artifacts/iteration-11');pads=[e for e in b if e['type']=='pcb_smtpad' and e['layer']=='top' and e['pcb_component_id']==co['U_DRV']['pcb_component_id']];ground=sp[ports['U_DRV','EP']['source_port_id']]['subcircuit_connectivity_map_key'];key=lambda e:sp[pp[e['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key');bb=box(3,3,12.5,12);ep=ports['U_DRV','EP'];reports=[]
for resolution in [128,256]:
 foreign=unary_union([g.pad_shape(e).buffer(.51,quad_segs=resolution) for e in pads if key(e)!=ground]);free=bb.difference(foreign);region=next(p for p in free.geoms if p.covers(Point(ep['x'],ep['y'])));assert not region.boundary.intersects(bb.boundary)
 for wire_radius in [0,.30,.36]:
  access=region.buffer(.275+wire_radius+.001,quad_segs=resolution)
  def possible(budget):
   blocked=unary_union([g.pad_shape(e).buffer(.15+budget if key(e)==ground else max(.425,.15+budget),quad_segs=resolution) for e in pads]);return bb.difference(blocked).intersection(access)
  allowed=possible(.115);assert allowed.is_empty
  lo,hi=0,.115
  for _ in range(25):
   mid=(lo+hi)/2
   if possible(mid).is_empty:hi=mid
   else:lo=mid
  last=possible(lo);reports.append({'curve_quadrants':resolution,'wire_endcap_radius_mm':wire_radius,'outer_annulus_radius_mm':.275,'extra_optimistic_reach_allowance_mm':.001,'original_hole_mm':.30,'necessary_reachable_via_centre_area_at_0_115_mm2':allowed.area,'closed_EP_wire_centre_component_bounds_mm':region.bounds,'optimistic_max_radial_budget_interval_mm':[lo,hi],'last_reachable_regions_bounds_mm':[p.bounds for p in (list(last.geoms) if hasattr(last,'geoms') else [last]) if not p.is_empty]})
# Quantified footprint changes are counterfactual decisions, not modified source or supplier approvals.
pm={e['pcb_port_id']:e for e in pads};ep_shape=g.pad_shape(pm[ep['pcb_port_id']]);ep_width=ep_shape.bounds[2]-ep_shape.bounds[0];gapA=ep_shape.distance(g.pad_shape(pm[ports['U_DRV','GND18']['pcb_port_id']]));gapB=ep_shape.distance(g.pad_shape(pm[ports['U_DRV','GND']['pcb_port_id']]));decisions=[]
for radial_margin in [0,.005,.010]:
 required=.30+2*(.115+radial_margin);moves=[required-gapA,required-gapB];symmetric=max(moves);decisions.append({'positive_margin_per_side_mm':radial_margin,'required_pad_gap_mm':required,'outward_GND18_pad_translation_mm':moves[0],'outward_GND_pad_translation_mm':moves[1],'symmetric_EP_edge_retraction_mm':symmetric,'resulting_EP_x_dimension_mm':ep_width-2*symmetric,'total_EP_x_reduction_mm':2*symmetric,'requires_supplier_land_pattern_change':True,'adopted':False})
ref_gapA=gapA+(ep_width-3.15)/2;ref_gapB=gapB+(ep_width-3.15)/2
out={'baseline_head':'4600e6b5d1f7237af2204eefa6457145fd68fcee','only_driver_SMT_pads_used':len(pads),'necessary_access_cases':reports,'rules_unchanged':{'hole_mm':.30,'land_mm':.55,'nominal_return_mm':.60,'stressed_return_mm':.72,'foreign_clearance_mm':.15,'all_SMT_radial_drill_budget_mm':.115},'scope':'Driver-pads-only necessary access, now allows wire cap/annulus contact outside via axis. No extra copper, other layers or mechanical obstacles; real obstacles can only reduce access. Empty domains rule out this retained padstack/stressed-width class under rigid driver placement. Not a proof over other land patterns or processes.','placement_translation_or_rotation_changes_intrinsic_gap':False,'counterfactual_land_pattern_options':decisions,'reference_3_15mm_EP_only_resulting_gaps_mm':[ref_gapA,ref_gapB],'reference_3_15_EP_alone_meets_0_530':False,'not_adopted':['smaller holes','land edits','via-in-pad flag','lower width/clearance/drill budgets'],'manufacturing_qualified':False};(r/'star-access-bound.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
