"""Verify actual plated drills and JLCPCB drill/copper rules against delivered CAM."""
import json,hashlib,math
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
import importlib.util
spec=importlib.util.spec_from_file_location('via_cam',g.ROOT/'scripts/audit-manufacturing.py');cam=importlib.util.module_from_spec(spec);spec.loader.exec_module(cam)
j=g.j;root=g.ROOT;errors=[];tol=.00055;directory=root/'artifacts/manufacturing';drillpath=directory/'drill-L1-L4.drl'
_,drills,stats=cam.drill(drillpath);vias=[e for e in j if e['type']=='pcb_via'];holes=[];copper=[];keys=[];layers=[];matches=[]
for e in j:
 t=e['type']
 if t=='pcb_via':
  holes.append((e,Point(e['x'],e['y']).buffer(e['hole_diameter']/2,quad_segs=64)))
  for l in e['layers']:copper.append(Point(e['x'],e['y']).buffer(e['outer_diameter']/2));keys.append(g.key(e));layers.append(l)
 elif t in ['pcb_smtpad','pcb_plated_hole']:
  for l in e.get('layers',[e.get('layer','top')]):copper.append(g.geometry(e));keys.append(g.key(e));layers.append(l)
  if t=='pcb_plated_hole':
   q=dict(e);q['outer_width']=q.get('hole_width',q.get('hole_diameter'));q['outer_height']=q.get('hole_height',q.get('hole_diameter'));q['outer_diameter']=q.get('hole_diameter',q.get('hole_width'));holes.append((e,cam.shape(q)))
 elif t=='pcb_hole':holes.append((e,Point(e['x'],e['y']).buffer(e['hole_diameter']/2,quad_segs=64)))
 elif t=='pcb_trace':
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:copper.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2));keys.append(g.key(e));layers.append(a['layer'])
 elif t=='pcb_copper_pour':copper.append(__import__('shapely.geometry',fromlist=['Polygon']).Polygon([(v['x'],v['y']) for v in e['brep_shape']['outer_ring']['vertices']], [[(v['x'],v['y']) for v in r['vertices']] for r in e['brep_shape'].get('inner_rings',[])]));keys.append(g.key(e));layers.append(e['layer'])
tree=STRtree(copper);minimum=1e9;pair_minimum=1e9
for v in vias:
 if v['hole_diameter']<.3-1e-9 or v['outer_diameter']<.45-1e-9 or (v['outer_diameter']-v['hole_diameter'])/2<.075-1e-9:errors.append({'via':v['pcb_via_id'],'reason':'Requested drill/pad/nominal annulus minimum failed'})
 expected=Point(v['x'],v['y']).buffer(v['hole_diameter']/2,quad_segs=64)
 found=[h for h in drills if h.centroid.distance(Point(v['x'],v['y']))<=tol and abs(h.area-math.pi*(v['hole_diameter']/2)**2)<.0001]
 if len(found)!=1:errors.append({'via':v['pcb_via_id'],'reason':'Actual plated drill is missing, duplicated or has the wrong diameter','matches':len(found)});continue
 h=found[0];matches.append({'via':v['pcb_via_id'],'Circuit_JSON_xy_mm':[v['x'],v['y']],'actual_Excellon_xy_mm':list(h.centroid.coords)[0],'drill_mm':v['hole_diameter'],'pad_mm':v['outer_diameter'],'nominal_annular_ring_mm':(v['outer_diameter']-v['hole_diameter'])/2})
for i,(e,h) in enumerate(holes):
 typ=e['type'];key=g.key(e) if typ!='pcb_hole' else None
 for k in tree.query(h.buffer(.301)):
  if key is not None and keys[k]==key:continue
  limit=.3 if typ=='pcb_plated_hole' and layers[k].startswith('inner') else .28 if typ=='pcb_plated_hole' else .2
  d=h.distance(copper[k]);minimum=min(minimum,d)
  if d+tol<limit:errors.append({'hole':e.get(typ+'_id'),'layer':layers[k],'reason':'Foreign copper violates JLCPCB drill-edge clearance','actual_mm':d,'minimum_mm':limit})
 for q,s in holes[i+1:]:
  if typ=='pcb_hole' or q['type']=='pcb_hole':continue
  limit=.2 if 'pcb_via' in [typ,q['type']] else .45;d=h.distance(s);pair_minimum=min(pair_minimum,d)
  if d+tol<limit:errors.append({'holes':[e[typ+'_id'],q[q['type']+'_id']],'reason':'Plated drill-to-drill edge spacing','actual_mm':d,'minimum_mm':limit})
report={'passed':not errors,'board_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'actual_plated_drill_file_sha256':hashlib.sha256(drillpath.read_bytes()).hexdigest(),'capability_source':'https://jlcpcb.com/capabilities/pcb-capabilities','via_rule':'Diameter difference >=0.10 mm; 0.15 mm preferred. This revision requires >=0.30 mm drill and >=0.45 mm pad.','nominal_dimensions_not_fabricated_measurements':True,'source_vias':len(vias),'actual_drill_matches':len(matches),'minimum_actual_declared_drill_mm':min(v['hole_diameter'] for v in vias),'minimum_declared_pad_mm':min(v['outer_diameter'] for v in vias),'minimum_nominal_ring_mm':min((v['outer_diameter']-v['hole_diameter'])/2 for v in vias),'minimum_foreign_drill_to_copper_mm':minimum,'minimum_plated_drill_pair_edge_gap_mm':pair_minimum,'drill_parser_stats':stats,'via_coordinates':matches,'errors':errors}
(root/'artifacts/upright-revision/via-fabrication-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Actual via fabrication', 'PASS' if report['passed'] else 'FAIL',len(vias),'vias;',len(errors),'findings');raise SystemExit(bool(errors))
