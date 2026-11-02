"""Independent generated-geometry audit; does not establish routed-board readiness."""
import json,math,hashlib
from pathlib import Path
from shapely.geometry import Polygon,Point,box
from shapely.affinity import rotate,translate
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'artifacts/v2/source.circuit.json';data=json.loads(path.read_text())
sources={e['source_component_id']:e for e in data if e['type']=='source_component'}
pcs={e['pcb_component_id']:e for e in data if e['type']=='pcb_component'}
names={i:sources[e['source_component_id']]['name'] for i,e in pcs.items()}
board=next(e for e in data if e['type']=='pcb_board');boundary=box(-board['width']/2,-board['height']/2,board['width']/2,board['height']/2)
polys={names[e['pcb_component_id']]:Polygon([(p['x'],p['y']) for p in e['outline']]) for e in data if e['type']=='pcb_courtyard_outline' and e['layer']=='top'}
errors=[];gaps=[];copper_edge_gaps=[]
# Check the actual pad envelopes separately from placement courtyards. A
# courtyard may approach the edge more closely than the 0.25 mm copper rule.
# Rectangular envelopes conservatively cover pill-shaped pads as well.
for e in data:
    if e['type'] not in ['pcb_smtpad','pcb_plated_hole']:continue
    if e['shape']=='circle':
        radius=e['outer_diameter']/2 if e['type']=='pcb_plated_hole' else e['radius']
        envelope=Point(e['x'],e['y']).buffer(radius)
    else:
        w=e.get('outer_width',e.get('width'));h=e.get('outer_height',e.get('height'))
        if w is None or h is None:raise ValueError('Unsupported pad envelope: '+str(e))
        envelope=translate(rotate(box(-w/2,-h/2,w/2,h/2),e.get('ccw_rotation',0),origin=(0,0)),xoff=e['x'],yoff=e['y'])
    gap=envelope.distance(boundary.boundary) if boundary.covers(envelope) else -envelope.difference(boundary).area
    copper_edge_gaps.append(gap)
    if gap<.25-1e-6:errors.append({'type':'copper_to_board_edge','component':names.get(e.get('pcb_component_id')),'distance_mm':gap})
for i,(n,poly) in enumerate(polys.items()):
    if not boundary.buffer(1e-6).covers(poly):errors.append({'type':'courtyard_outside_board','component':n})
    for m,other in list(polys.items())[:i]:
        d=poly.distance(other);gaps.append(d)
        if poly.intersection(other).area>1e-7:errors.append({'type':'courtyard_overlap','components':[n,m]})
    for x in [-13,13]:
        for y in [-13,13]:
            d=poly.distance(Point(x,y))
            if d<3.2-1e-6:errors.append({'type':'screw_head_envelope','component':n,'mount':[x,y],'distance_mm':d})
for cid,c in pcs.items():
    if not c.get('do_not_place') and sources[c['source_component_id']]['ftype']!='simple_test_point' and c['layer']!='top':errors.append({'type':'fitted_component_not_top','component':names[cid]})
    if c['layer']=='top' and names[cid] not in polys:errors.append({'type':'missing_courtyard','component':names[cid]})
# Bare probe pads have no placement/assembly operation on the bottom side.
bottom={names[e['pcb_component_id']]:Polygon([(p['x'],p['y']) for p in e['outline']]) for e in data if e['type']=='pcb_courtyard_outline' and e['layer']=='bottom'}
for i,(n,poly) in enumerate(bottom.items()):
    if not boundary.buffer(1e-6).covers(poly):errors.append({'type':'bottom_courtyard_outside_board','component':n})
    for m,other in list(bottom.items())[:i]:
        if poly.intersection(other).area>1e-7:errors.append({'type':'bottom_courtyard_overlap','components':[n,m]})
    if not n.startswith('TP_'):continue
    for e in data:
        if e['type']=='pcb_plated_hole':
            # Larger copper-side envelope, not just the drill.
            if e.get('shape')=='circle':through=Point(e['x'],e['y']).buffer(e['outer_diameter']/2+.15)
            else:continue  # USB stakes are checked below by their component envelope.
            if poly.intersects(through):errors.append({'type':'bottom_testpad_at_through_pad','component':n})
    for cid,c in pcs.items():
        if names[cid] not in ['J_PD','J_DATA']:continue
        if poly.intersects(polys[names[cid]]):errors.append({'type':'bottom_testpad_at_usb_drills','component':n})
name='J_MOTOR';cid=next(i for i,n in names.items() if n==name)
motor=next(e for e in data if e['type']=='pcb_component' and e['pcb_component_id']==cid)
holes=[e for e in data if e['type']=='pcb_plated_hole' and e.get('pcb_component_id')==cid]
if len(holes)!=4:errors.append({'type':'terminal_drill_count','actual':len(holes)})
# Preserve the exact imported 3.5 mm-pitch staggered land pattern, transformed
# with the actual generated component placement. These are supplier nominal
# dimensions, not a manufacturing approval of the latest drill tolerances.
local_holes=[(-5.250053,2.499995),(-1.749933,-2.499995),(1.749933,2.499995),(5.250053,-2.499995)]
theta=math.radians(motor['rotation']);expected=[(motor['center']['x']+x*math.cos(theta)-y*math.sin(theta),motor['center']['y']+x*math.sin(theta)+y*math.cos(theta)) for x,y in local_holes]
for x,y in expected:
    matches=[h for h in holes if math.hypot(h['x']-x,h['y']-y)<1e-5]
    if len(matches)!=1 or not (math.isclose(matches[0]['hole_diameter'],.999998,abs_tol=1e-5) and math.isclose(matches[0]['outer_diameter'],1.7999964,abs_tol=1e-5)):
        errors.append({'type':'terminal_supplier_drill_or_pad','expected_xy_mm':[x,y]})
# Re-evaluate every solver proximity rule using generated component/port data,
# so a valid packing cannot hide detached decoupling or changed crystal pins.
plan=json.loads((ROOT/'artifacts/v2/placement-screen.json').read_text())
pcs_byname={names[cid]:c for cid,c in pcs.items()}
source_ports={e['source_port_id']:e for e in data if e['type']=='source_port'}
physical_ports={(names[e['pcb_component_id']],source_ports[e['source_port_id']]['pin_number']):e for e in data if e['type']=='pcb_port'}
proximity_results=[]
for rule in plan.get('proximity_checks',[]):
    child=physical_ports[(rule['child'],rule['child_pin'])] if 'child_pin' in rule else pcs_byname[rule['child']]['center']
    if rule['type']=='point':target={'x':rule['x'],'y':rule['y']}
    elif rule['type']=='pin':target=physical_ports[(rule['parent'],rule['pin'])]
    else:target=pcs_byname[rule['parent']]['center']
    distance=abs(child['x']-target['x'])+abs(child['y']-target['y'])
    passed=distance<=rule['limit_mm']+.011
    proximity_results.append({**rule,'actual_distance_mm':distance,'passed':passed})
    if not passed:errors.append({'type':'critical_proximity','rule':rule,'actual_distance_mm':distance})
if not proximity_results:errors.append({'type':'missing_proximity_checks'})
native=[e for e in data if e['type'].endswith('_error') and not e['type'].startswith('schematic_')]
receipt={'passed':not errors and not native,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'board_mm':[board['width'],board['height']],'top_courtyards_checked':len(polys),'bottom_courtyards_checked':len(bottom),'bottom_probe_pads':[n for n in bottom if n.startswith('TP_')],'minimum_courtyard_gap_mm':min(gaps),'minimum_copper_to_board_edge_mm':min(copper_edge_gaps),'screw_head_envelope_diameter_mm':6.4,'critical_proximity_check_count':len(proximity_results),'critical_proximity_checks':proximity_results,'native_pcb_error_count':len(native),'independent_error_count':len(errors),'errors':errors,'scope':'Generated 2D placement, pad-to-board-edge clearance, board bounds, screw-head envelopes and terminal drills. Not routing, wire/tool access, detailed 3D, electrical performance or manufacturing release.'}
(ROOT/'artifacts/v2/placement-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
if not receipt['passed']:raise SystemExit(1)
