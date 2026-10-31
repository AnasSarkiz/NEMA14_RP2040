"""Audit and draw a connector placement proposal without rewriting board source."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path

from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, box

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'artifacts/v2/connector-study'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--plan', type=Path, default=DEFAULT / 'avx9296-plan.json')
parser.add_argument('--output', type=Path, default=DEFAULT)
args = parser.parse_args()
study = json.loads(args.plan.read_text())
placements, parts = study['placements'], study['parts']
width, height = study['board_mm']
boundary = box(-width / 2, -height / 2, width / 2, height / 2)
errors, polygons = [], {}
base = ROOT / 'artifacts/v2/source.circuit.json'
if hashlib.sha256(base.read_bytes()).hexdigest() != study['base_source_sha256']:
    errors.append({'type': 'base_source_changed'})

for name, part in parts.items():
    p = placements[name]
    local = Polygon([(v['x'], v['y']) for v in part['courtyard']])
    poly = translate(rotate(local, p['pcbRotation'], origin=(0, 0)),
                     xoff=p['pcbX'], yoff=p['pcbY'])
    polygons[name] = poly
    if not boundary.buffer(1e-6).covers(poly):
        errors.append({'type': 'board_bounds', 'component': name})
    if not part['do_not_place'] and not name.startswith('TP_') and part['layer'] != 'top':
        errors.append({'type': 'fitted_part_not_top', 'component': name})
    for x in [-13, 13]:
        for y in [-13, 13]:
            if poly.distance(Point(x, y)) < 3.2 - 1e-6:
                errors.append({'type': 'screw_head_clearance', 'component': name})

gaps = []
for i, (name, poly) in enumerate(polygons.items()):
    for other, second in list(polygons.items())[:i]:
        if parts[name]['layer'] != parts[other]['layer']:
            continue
        gaps.append(poly.distance(second))
        if poly.intersection(second).area > 1e-7:
            errors.append({'type': 'courtyard_overlap', 'components': [name, other]})

checks = []
for rule in study['proximity_checks']:
    child = placements[rule['child']]
    if rule['type'] == 'point':
        x, y = rule['x'], rule['y']
    else:
        parent = placements[rule['parent']]
        x, y = parent['pcbX'], parent['pcbY']
        if rule['type'] == 'pin':
            theta = math.radians(parent['pcbRotation'])
            u, v = rule['local_x'], rule['local_y']
            x += u * math.cos(theta) - v * math.sin(theta)
            y += u * math.sin(theta) + v * math.cos(theta)
    distance = abs(child['pcbX'] - x) + abs(child['pcbY'] - y)
    # Search offsets were rounded to 0.01 mm; evaluate physical offsets here.
    passed = distance <= rule['limit_mm'] + .011
    checks.append({**rule, 'distance_mm': distance, 'passed': passed})
    if not passed:
        errors.append({'type': 'proximity', 'rule': rule, 'distance_mm': distance})

for name, part in parts.items():
    if name.startswith('TP_') and part['layer'] == 'bottom':
        for usb in ['J_PD', 'J_DATA']:
            if polygons[name].intersects(polygons[usb]):
                errors.append({'type': 'probe_at_usb_drills', 'component': name})

# Proposed four wire centers at the outward-facing left edge. These are
# insulation envelopes, not a bend-radius, retention or release-cycle test.
for y in [-1, 2, 5, 8]:
    entry = box(-width / 2, y - .8, -16.9, y + .8)
    for name, poly in polygons.items():
        if name != 'J_MOTOR_A' and parts[name]['layer'] == 'top' and poly.intersection(entry).area > 1e-7:
            errors.append({'type': 'wire_entry_obstruction', 'component': name})

receipt = {
    'passed': not errors, 'base_source_sha256': study['base_source_sha256'],
    'plan_sha256': hashlib.sha256(args.plan.read_bytes()).hexdigest(),
    'board_mm': study['board_mm'], 'top_courtyards': sum(v['layer'] == 'top' for v in parts.values()),
    'bottom_courtyards': sum(v['layer'] == 'bottom' for v in parts.values()),
    'proximity_checks': len(checks), 'proximity_rounding_tolerance_mm': .011,
    'minimum_courtyard_gap_mm': min(gaps), 'errors': errors, 'scope': study['scope'],
}
args.output.mkdir(parents=True, exist_ok=True)
(args.output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
if errors:
    raise SystemExit(1)

svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-22 -22 44 46" width="1320" height="1380">',
       '<rect x="-22" y="-22" width="44" height="46" fill="#f6f8fa"/>',
       '<g font-family="sans-serif" text-anchor="middle" fill="#173b37">',
       '<text x="0" y="-20.2" font-size=".9">NEMA14 V2 · compact four-wire spring connector</text>',
       '<text x="0" y="-18.8" font-size=".6">34.5 × 34.5 mm · PLACEMENT PROPOSAL · UNROUTED</text></g>',
       '<g transform="scale(1,-1)"><rect x="-17.25" y="-17.25" width="34.5" height="34.5" fill="#edf5ef" stroke="#28523d" stroke-width=".12"/>']
colors = {'J_': '#94d8ce', 'U_': '#cbd4e0', 'C_': '#f2d894', 'R_': '#e5c9b6',
          'Q_': '#c4b8d9', 'D_': '#e6b7cc', 'TP_': '#b4dba8', 'L_': '#d9b57f', 'Y_': '#afd6e4', 'BZ': '#b3cfd1'}
for name, poly in polygons.items():
    if parts[name]['layer'] != 'top':
        continue
    label = 'J_MOTOR (4 wires)' if name == 'J_MOTOR_A' else name
    a, b, c, d = poly.bounds
    w, h = c - a, d - b
    angle = 90 if h > w * 1.5 else 0
    size = min(.5, (max(w, h) - .15) / (len(label) * .62), min(w, h) * .6)
    color = next((v for prefix, v in colors.items() if name.startswith(prefix)), '#ddd')
    points = ' '.join(f'{x},{y}' for x, y in poly.exterior.coords)
    svg.append(f'<g><title>{html.escape(label + ": " + parts[name]["mpn"])}</title><polygon points="{points}" fill="{color}" stroke="#53615c" stroke-width=".045"/>')
    svg.append(f'<g transform="translate({(a+c)/2},{(b+d)/2}) rotate({angle}) scale(1,-1)"><text text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="{size}">{html.escape(label)}</text></g></g>')
for x in [-13, 13]:
    for y in [-13, 13]:
        svg.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="none" stroke="#aa7659" stroke-dasharray=".25,.15" stroke-width=".08"/><circle cx="{x}" cy="{y}" r="1.6" fill="#f6f8fa" stroke="#68796e" stroke-width=".08"/>')
for y, label in zip([8, 5, 2, -1], ['A+', 'A−', 'B+', 'B−']):
    svg.append(f'<path d="M -20.5 {y} H -16.9" stroke="#277a66" stroke-width=".15"/><g transform="translate(-20.8,{y}) scale(1,-1)"><text text-anchor="end" dominant-baseline="central" font-family="sans-serif" font-size=".5">{label}</text></g>')
svg.extend(['</g><g font-family="sans-serif" text-anchor="middle" fill="#23463c">',
            '<text x="0" y="19.0" font-size=".62">AVX 009296004202906 · JLCPCB C21619069 · body 12 × 7 × 2.5 mm</text>',
            '<text x="0" y="20.2" font-size=".57">Full courtyards shown · encoder capacitors on top · bare debug pads underneath</text>',
            '<text x="0" y="21.4" font-size=".57">Wire gauge / insulation and procurement still need confirmation</text>',
            '<text x="0" y="22.6" font-size=".57">No candidate pads, electrical netlist or routed copper generated</text></g></svg>'])
(args.output / 'placement.svg').write_text('\n'.join(svg) + '\n')
