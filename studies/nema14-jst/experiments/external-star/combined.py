"""Unchanged supplemental simultaneous width/drill screen; separate from legacy manufacturing gates."""
from model import *
from routing_geometry import resolve_copper_nets
r=Path('artifacts/iteration-12');out=[]
for mode in ['external','direct']:
 j=resolve_copper_nets(read(r/(mode+'.circuit.json')));st={e['source_trace_id']:e.get('name','') for e in j if e['type']=='source_trace'};vias=[e for e in j if e['type']=='pcb_via'];rows=[]
 for t in [e for e in j if e['type']=='pcb_trace']:
  for k,(a,z) in enumerate(zip(t['route'],t['route'][1:])):
   if a['route_type']!=z['route_type'] or a['route_type']!='wire' or a['layer']!=z['layer']:continue
   wire=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])*.6,quad_segs=128)
   for v in vias:
    if a['layer'] not in v['layers'] or t['subcircuit_connectivity_map_key']==v['subcircuit_connectivity_map_key']:continue
    gap=g.pad_shape(v,True).distance(wire);rows.append({'path':st[t['source_trace_id']],'pcb_trace_id':t['pcb_trace_id'],'segment':k,'via':v['pcb_via_id'],'layer':a['layer'],'drill_to_stressed_trace_mm':gap,'adjusted_margin_mm':gap-.115-.2})
 failures=[e for e in rows if e['adjusted_margin_mm']<-1e-6];out.append({'mode':mode,'width_multiplier':1.2,'radial_budget_mm':.115,'hole_to_foreign_track_rule_mm':.2,'replaces_legacy_gate':False,'checked_pairs':len(rows),'failed_pairs':failures,'minimum_margin_mm':min(e['adjusted_margin_mm'] for e in rows),'closest_pairs':sorted(rows,key=lambda e:e['adjusted_margin_mm'])[:12]})
(r/'combined-drill-width.json').write_text(json.dumps(out,indent=2)+'\n');print([(e['mode'],len(e['failed_pairs']),e['minimum_margin_mm']) for e in out])
