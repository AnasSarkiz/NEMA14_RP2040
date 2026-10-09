"""Reviewed A4988 phase escapes with standard 0.25/0.50 mm vias.
Validate actual foreign native-pad clearance before inserting any copper.
"""
import json,math,hashlib
import verify_supplier_connectivity as g
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
rp=g.ROOT.name=='NEMA14_RP2040';j=g.j
coords={'A_PLUS':([(-.199747,-6.350005),(-.199747,-5.648)],.30),'B_PLUS':([(-1.200507,-6.350005),(-1.200507,-5.648)],.30),'A_MINUS':([(1.799995,-7.348733),(2.3,-7.348733),(2.6,-7),(2.7,-6.8)],.20),'B_MINUS':([(-3.199995,-7.348733),(-3.6,-7.348733),(-3.75,-6.9),(-3.75,-6.4)],.30)}if rp else {'A_PLUS':([(.500353,-4.900005),(.4,-4.0)],.30),'B_PLUS':([(-.500407,-4.900005),(-.4,-4.0)],.30),'A_MINUS':([(2.500095,-5.898733),(3.55,-5.898733)],.30),'B_MINUS':([(-2.499895,-5.898733),(-3.55,-5.898733)],.30)}
keys={n:k for k,n in g.nets.items()if n in coords};remove={e['pcb_trace_id']for e in j if e['type']=='pcb_trace'and g.key(e)in keys.values()and e['pcb_trace_id'].startswith(('supplier_repair_island_','inside_phase_escape_'))};j=[e for e in j if not(e['type']=='pcb_trace'and e['pcb_trace_id']in remove or e['type']=='pcb_via'and(e.get('pcb_trace_id')in remove or e['pcb_via_id'].startswith('inside_phase_via_')))];add=[];rows=[]
for n,(points,width)in coords.items():
 key=keys[n];port=next(e for e in j if e['type']=='pcb_port'and g.src[g.comp[e['pcb_component_id']]['source_component_id']]=='U_DRV'and g.sp[e['source_port_id']].get('subcircuit_connectivity_map_key')==key);assert math.dist(points[0],[port['x'],port['y']])<.001,(n,points[0],port);points[0]=(port['x'],port['y']);wire=LineString(points).buffer(width/2);x,y=points[-1];via=Point(x,y).buffer(.25);clearances=[]
 for e in j:
  if e['type']not in ['pcb_smtpad','pcb_plated_hole']:continue
  p=g.geometry(e)
  if g.key(e)!=key:
   d=min(wire.distance(p)if'top'in e.get('layers',[e.get('layer')])else 100,via.distance(p));assert d>=.1498,(n,'foreign pad clearance',e.get('pcb_smtpad_id'),d);clearances.append(d)
  if e['type']=='pcb_smtpad':assert not via.intersection(p).area>1e-8,(n,'ordinary via annulus overlaps SMT pad',e.get('pcb_smtpad_id'))
 for e in j:
  if e['type']=='pcb_keepout':assert not unary_union([wire,via]).intersects(g.keepout_geometry(e)),(n,'fastener keepout')
 net=next(e for e in j if e['type']=='source_net'and e['subcircuit_connectivity_map_key']==key);st=next(e for e in j if e['type']=='source_trace'and e['subcircuit_connectivity_map_key']==key);common={'subcircuit_connectivity_map_key':key,'source_net_id':net['source_net_id'],'source_trace_id':st['source_trace_id'],'subcircuit_id':'subcircuit_source_group_0'};tid='inside_phase_escape_'+n;add += [{'type':'pcb_trace','pcb_trace_id':tid,'pcb_port_ids':[port['pcb_port_id']],'route':[{'route_type':'wire','x':a,'y':b,'width':width,'layer':'top'}for a,b in points],**common},{'type':'pcb_via','pcb_via_id':'inside_phase_via_'+n,'pcb_trace_id':tid,'x':x,'y':y,'hole_diameter':.25,'outer_diameter':.5,'layers':['top','inner1','inner2','bottom']if rp else['top','bottom'],'tented_on_top':True,'tented_on_bottom':True,**common}];rows.append({'net':n,'trace_id':tid,'via_id':'inside_phase_via_'+n,'points_mm':points,'width_mm':width,'length_mm':LineString(points).length,'minimum_foreign_native_pad_clearance_mm':min(clearances)})
# Explicit escapes have priority over newly attempted search paths. Never erase
# old copper or native pads merely to make an escape fit.
removed=[]
for e in j:
 if e['type']!='pcb_trace' or g.key(e)in keys.values():continue
 shapes=[LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)for a,b in zip(e['route'],e['route'][1:])if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']=='top'];top=unary_union(shapes)
 for row in rows:
  if g.key(e)==keys[row['net']]:continue
  phase=unary_union([LineString(row['points_mm']).buffer(row['width_mm']/2),Point(*row['points_mm'][-1]).buffer(.25)])
  if top.distance(phase)<.1498:
   assert e['pcb_trace_id'].startswith('supplier_repair_island_'),('Existing foreign copper collides with escape',row['net'],e['pcb_trace_id']);removed.append(e['pcb_trace_id']);break
j=[e for e in j if not(e['type']=='pcb_trace'and e['pcb_trace_id']in removed or e['type']=='pcb_via'and e.get('pcb_trace_id')in removed)];g.path.write_text(json.dumps(j+add,indent=2)+'\n');(g.ROOT/'artifacts/validation/service-phase-escapes.json').write_text(json.dumps({'rows':rows,'discarded_attempted_routes_requiring_repair':removed,'source_native_pad_clearance_minimum_mm':.15,'ordinary_vias_outside_all_SMT_annuli':True,'status':'ROUTING_AND_ACTUAL_CAM_CHECKS_REQUIRED'},indent=2)+'\n');print(rows,removed)
