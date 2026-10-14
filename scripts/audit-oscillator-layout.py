"""Separate oscillator geometry checks; generic DRC does not qualify oscillator design."""
import json,hashlib,math
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import verify_supplier_connectivity as g
j=g.j;src={e['name']:e for e in j if e['type']=='source_component'};errors=[];rows=[]
if 'Y_MCU' in src:
 nets={n:k for k,n in g.nets.items()};limits={'XIN':5,'XOUT':6,'XTAL_OUT':5}
 for name,limit in limits.items():
  ts=[t for t in j if t['type']=='pcb_trace' and g.key(t)==nets[name]];vs=[v for v in j if v['type']=='pcb_via' and g.key(v)==nets[name]];length=0;ls=set()
  for t in ts:
   for a,b in zip(t['route'],t['route'][1:]):
    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:length+=math.dist((a['x'],a['y']),(b['x'],b['y']));ls.add(a['layer'])
  es,rs=g.groups(nets[name]);roots={r for e,r in zip(es,rs) if e.get('pcb_port_id')}
  if not ts or vs or ls!={'top'} or length>limit or len(roots)!=1:errors.append({'net':name,'reason':'Top-only no-via short connected oscillator policy failed','layers':sorted(ls),'total_copper_length_mm':length,'signal_vias':len(vs),'physical_pad_islands':len(roots),'length_budget_mm':limit})
  rows.append({'net':name,'total_copper_length_mm':length,'layers':sorted(ls),'signal_vias':len(vs),'physical_pad_islands':len(roots)})
 # Enforce the construction reservation outside the unavoidable MCU pin fanout.
 plan=json.loads((g.ROOT/'artifacts/upright-revision/oscillator-plan.json').read_text())
 region=unary_union([LineString(r['points']).buffer(plan['guard_buffer_mm']) for r in plan['routes']])
 exemptions=unary_union([Point(r['points'][0]).buffer(plan['MCU_pin_local_exemption_radius_mm']) for r in plan['routes'] if r['trace'] in ['oscillator_XIN','oscillator_XOUT']])
 region=region.difference(exemptions)
 for e in j:
  if g.nets.get(g.key(e)) in ['GND','XIN','XOUT','XTAL_OUT']:continue
  hit=False
  if e['type']=='pcb_via':hit=Point(e['x'],e['y']).buffer(e['outer_diameter']/2).intersects(region)
  elif e['type'] in ['pcb_smtpad','pcb_plated_hole'] and 'top' in e.get('layers',[e.get('layer','top')]):hit=g.geometry(e).intersects(region)
  elif e['type']=='pcb_trace':
   hit=any(a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'] and a['layer'] in plan['layers_reserved'] and LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2).intersects(region) for a,b in zip(e['route'],e['route'][1:]))
  if hit:errors.append({'element':e.get(e['type']+'_id'),'reason':'Unrelated copper enters reserved oscillator/reference region'})
 # Every crystal/load-cap ground has a short, ordinary return to adjacent ground copper.
 ground=nets['GND'];planes=unary_union([__import__('shapely.geometry',fromlist=['Polygon']).Polygon([(v['x'],v['y']) for v in e['brep_shape']['outer_ring']['vertices']], [[(v['x'],v['y']) for v in r['vertices']] for r in e['brep_shape'].get('inner_rings',[])]) for e in j if e['type']=='pcb_copper_pour' and e['layer']=='inner1' and g.key(e)==ground])
 for ref,role in [('Y_MCU','pin2'),('Y_MCU','pin4'),('C_XIN','pin2'),('C_XOUT','pin2')]:
  p=next(p for p in g.ports.values() if g.src[g.sp[p['source_port_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==role)
  returns=[v for v in j if v['type']=='pcb_via' and g.key(v)==ground and math.dist((v['x'],v['y']),(p['x'],p['y']))<=1.2 and planes.buffer(.00001).intersects(Point(v['x'],v['y']).buffer(v['outer_diameter']/2))]
  if not returns:errors.append({'reference':ref+'.'+role,'reason':'No short via return to adjacent inner1 ground'})
 if src['Y_MCU'].get('frequency')!=12e6 or src['R_XOUT'].get('resistance')!=1000:errors.append('Oscillator frequency or damping resistor changed')
report={'passed':not errors,'board_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'external_crystal_present':'Y_MCU' in src,'routes':rows,'errors':errors,'startup_drive_level_load_and_frequency_bench_verified':False,'qualification_scope':'Geometry, connectivity, no signal vias and short ground returns; oscillator electrical operation needs bench validation.'}
(g.ROOT/'artifacts/upright-revision/oscillator-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Oscillator layout','PASS' if report['passed'] else 'FAIL',rows,errors);raise SystemExit(bool(errors))
