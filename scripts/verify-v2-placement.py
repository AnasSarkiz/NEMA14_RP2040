"""Independent generated-geometry audit; does not establish routed-board readiness."""
import json,math,hashlib
from pathlib import Path
from shapely.geometry import Polygon,Point,box
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'artifacts/v2/source.circuit.json';data=json.loads(path.read_text())
sources={e['source_component_id']:e for e in data if e['type']=='source_component'}
pcs={e['pcb_component_id']:e for e in data if e['type']=='pcb_component'}
names={i:sources[e['source_component_id']]['name'] for i,e in pcs.items()}
board=next(e for e in data if e['type']=='pcb_board');boundary=box(-board['width']/2,-board['height']/2,board['width']/2,board['height']/2)
polys={names[e['pcb_component_id']]:Polygon([(p['x'],p['y']) for p in e['outline']]) for e in data if e['type']=='pcb_courtyard_outline' and e['layer']=='top'}
errors=[];gaps=[]
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
for phase in ['A','B']:
    name='J_MOTOR_'+phase;cid=next(i for i,n in names.items() if n==name)
    holes=[e for e in data if e['type']=='pcb_plated_hole' and e.get('pcb_component_id')==cid]
    assert len(holes)==4,(name,len(holes))
    if not all(math.isclose(h['hole_diameter'],1.2,abs_tol=1e-7) and math.isclose(h['outer_diameter'],2,abs_tol=1e-7) for h in holes):errors.append({'type':'terminal_pad_or_drill','component':name})
    ds=sorted(round(math.hypot(a['x']-b['x'],a['y']-b['y']),5) for i,a in enumerate(holes) for b in holes[:i])
    expected=sorted([2.5,2.5,3.1,3.1,math.hypot(2.5,3.1),math.hypot(2.5,3.1)])
    if any(abs(a-b)>1e-4 for a,b in zip(ds,expected)):errors.append({'type':'terminal_drill_pitch','component':name,'distances':ds})
native=[e for e in data if e['type'].endswith('_error') and not e['type'].startswith('schematic_')]
receipt={'passed':not errors and not native,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'board_mm':[board['width'],board['height']],'top_courtyards_checked':len(polys),'bottom_courtyards_checked':len(bottom),'bottom_probe_pads':[n for n in bottom if n.startswith('TP_')],'minimum_courtyard_gap_mm':min(gaps),'screw_head_envelope_diameter_mm':6.4,'native_pcb_error_count':len(native),'independent_error_count':len(errors),'errors':errors,'scope':'Generated 2D placement, board bounds, screw-head envelopes and terminal drills. Not routing, wire/tool access, detailed 3D, electrical performance or manufacturing release.'}
(ROOT/'artifacts/v2/placement-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
if not receipt['passed']:raise SystemExit(1)
