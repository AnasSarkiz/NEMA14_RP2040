"""Screen a single Phoenix release-actuated terminal against the active V2 draft.

This writes research artifacts only, not board source, pads or connectivity.
"""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, box

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'artifacts/v2/source.circuit.json'
definition = ROOT / 'imports/supplier/A_1770979/A_1770979.tsx'
data = json.loads(source.read_text())
sources = {e['source_component_id']: e for e in data if e['type'] == 'source_component'}
components = {e['pcb_component_id']: e for e in data if e['type'] == 'pcb_component'}
names = {key: sources[value['source_component_id']]['name'] for key, value in components.items()}
courts = [(names[e['pcb_component_id']], e['layer'], Polygon([(p['x'], p['y']) for p in e['outline']]))
          for e in data if e['type'] == 'pcb_courtyard_outline']
assert {n for n, layer, poly in courts if n.startswith('J_MOTOR_')} == {'J_MOTOR_A', 'J_MOTOR_B'}
text = definition.read_text()
outline = json.loads(re.search(r'<courtyardoutline outline=\{(\[.*?\])\}', text, re.S)[1])
anchor = {'pcbX': -13.7, 'pcbY': 3.8, 'pcbRotation': 90}
def transform(poly):
    return translate(rotate(poly, anchor['pcbRotation'], origin=(0, 0)),
                     xoff=anchor['pcbX'], yoff=anchor['pcbY'])
candidate = transform(Polygon([(p['x'], p['y']) for p in outline]))
board = next(e for e in data if e['type'] == 'pcb_board')
boundary = box(-board['width']/2, -board['height']/2, board['width']/2, board['height']/2)
errors = []
if not boundary.covers(candidate):
    errors.append({'type': 'board_bounds'})
for name, layer, poly in courts:
    if layer == 'top' and not name.startswith('J_MOTOR_') and candidate.intersection(poly).area > 1e-7:
        errors.append({'type': 'courtyard_overlap', 'component': name})
head_gap = min(candidate.distance(Point(x, y)) for x in [-13, 13] for y in [-13, 13])
if head_gap < 3.2:
    errors.append({'type': 'screw_head_clearance'})
pads = []
for tag in re.findall(r'<platedhole\b[^>]+>', text):
    x = float(re.search(r'pcbX="([\d.eE+-]+)mm"', tag)[1])
    y = float(re.search(r'pcbY="([\d.eE+-]+)mm"', tag)[1])
    point = transform(Point(x, y))
    copper = point.buffer(.9)
    if not boundary.covers(copper):
        errors.append({'type': 'pad_outside_board'})
    for name, layer, poly in courts:
        if layer == 'bottom' and poly.intersects(copper.buffer(.15)):
            errors.append({'type': 'through_pad_at_bottom_reserve', 'component': name})
    pads.append({'x': point.x, 'y': point.y, 'hole_diameter_mm': 1.1999976,
                 'copper_diameter_mm': 1.7999964})
assert len(pads) == 8
report = {'passed': not errors, 'mpn': '1770979', 'jlcpcb': 'C3818616',
          'base_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'definition_sha256': hashlib.sha256(definition.read_bytes()).hexdigest(),
          'anchor': anchor, 'body_mm': [10.5, 5, 10],
          'courtyard_mm': [candidate.bounds[2]-candidate.bounds[0], candidate.bounds[3]-candidate.bounds[1]],
          'bounds_mm': list(candidate.bounds), 'minimum_courtyard_distance_to_mount_center_mm': head_gap,
          'head_envelope_diameter_mm': 6.4, 'plated_pads': pads, 'errors': errors,
          'scope': '2D replacement-envelope and through-pad fit only. No electrical netlist, routing, 3D/tool access, wire retention or procurement qualification.'}
out = ROOT / 'artifacts/v2/connector-study'
out.mkdir(parents=True, exist_ok=True)
(out/'phoenix1770979-verification.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
if errors:
    raise SystemExit(1)

namespace = 'http://www.w3.org/2000/svg'
ET.register_namespace('', namespace)
svg = ET.parse(ROOT/'artifacts/v2/placement.svg')
root = svg.getroot()
top = next(g for g in root.findall(f'{{{namespace}}}g') if g.get('transform') == 'scale(1,-1)')
for group in list(top):
    title = group.find(f'{{{namespace}}}title')
    if title is not None and title.text.startswith(('J_MOTOR_A ', 'J_MOTOR_B ')):
        top.remove(group)
group = ET.SubElement(top, f'{{{namespace}}}g')
ET.SubElement(group, f'{{{namespace}}}title').text = 'J_MOTOR proposal: Phoenix 1770979, four poles, release mechanism'
ET.SubElement(group, f'{{{namespace}}}polygon', {'points': ' '.join(f'{x},{y}' for x,y in candidate.exterior.coords),
                 'fill': '#96d5cc', 'stroke': '#45535d', 'stroke-width': '.055'})
a,b,c,d = candidate.bounds
label = ET.SubElement(group, f'{{{namespace}}}g', {'transform': f'translate({(a+c)/2},{(b+d)/2}) rotate(90) scale(1,-1)'})
ET.SubElement(label, f'{{{namespace}}}text', {'text-anchor': 'middle', 'dominant-baseline': 'central',
                 'font-family': 'sans-serif', 'font-size': '.5'}).text = 'J_MOTOR · 4P · 1770979'
for node in root.findall(f'{{{namespace}}}text'):
    if node.text and 'PLACEMENT ONLY' in node.text:
        node.text = 'PROPOSAL · RELEASE-ACTUATED TERMINAL · UNROUTED'
    elif node.text and 'Encoder capacitors' in node.text:
        node.text = '1770979: 10.5 × 5 mm body, 10 mm installed height; top wire entry'
    elif node.text and 'Five bare debug' in node.text:
        node.text = 'Procurement and factory lead gauge unconfirmed; active board source unchanged'
svg.write(out/'phoenix1770979-placement.svg', encoding='unicode')
