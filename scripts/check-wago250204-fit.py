"""Screen WAGO 250-204 against the fixed V2 placement, without editing the board.

This is a 2D, axis-aligned housing/courtyard screen. It does not solve a new
placement or qualify routing, drill dimensions, 3D access or manufacturing.
"""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'artifacts/v2/source.circuit.json'
raw = ROOT / 'references/v2/wago-250-204/raw-easyeda.tsx.txt'
data = json.loads(source.read_text())
names = {e['source_component_id']: e['name'] for e in data if e['type'] == 'source_component'}
components = {e['pcb_component_id']: names[e['source_component_id']]
              for e in data if e['type'] == 'pcb_component'}
board = next(e for e in data if e['type'] == 'pcb_board')
courts = {components[e['pcb_component_id']]: Polygon([(p['x'], p['y']) for p in e['outline']])
          for e in data if e['type'] == 'pcb_courtyard_outline' and e['layer'] == 'top'}
old = {n: p for n, p in courts.items() if n in ['J_MOTOR_A', 'J_MOTOR_B']}
assert len(old) == 2
obstacles = {n: p for n, p in courts.items() if n not in old}
# Rectangular Minkowski sums are exact only for these rectangular courtyards.
assert all(abs(p.area - box(*p.bounds).area) < 1e-6 for p in obstacles.values())
outline = json.loads(re.search(r'<courtyardoutline outline=\{(\[.*?\])\}', raw.read_text(), re.S)[1])
local = Polygon([(p['x'], p['y']) for p in outline])
a, b, c, d = local.bounds
cw, ch = c - a, d - b
screens = []
for envelope, (w, h) in [('manufacturer_body', (15.5, 12)), ('supplier_courtyard', (cw, ch))]:
    for angle in [0, 90]:
        ww, hh = (w, h) if angle == 0 else (h, w)
        hx, hy = ww / 2, hh / 2
        possible_centers = box(-board['width']/2 + hx, -board['height']/2 + hy,
                               board['width']/2 - hx, board['height']/2 - hy)
        forbidden = []
        for poly in obstacles.values():
            x1, y1, x2, y2 = poly.bounds
            forbidden.append(box(x1-hx, y1-hy, x2+hx, y2+hy))
        free = possible_centers.difference(unary_union(forbidden))
        screens.append({'envelope': envelope, 'rotation_deg': angle,
                        'free_center_region_empty': free.is_empty,
                        'free_center_region_area_mm2': free.area})
assert all(s['free_center_region_empty'] for s in screens), 'Reassess if a free location appears'

# An illustrative placement over the existing connector region, kept inside
# the PCB and outside all four screw-head envelopes. This is deliberately NOT
# a proposed replacement layout: the red parts must be repositioned first.
center_x, center_y = -10.75, 1.5
illustration = box(center_x-ch/2, center_y-cw/2, center_x+ch/2, center_y+cw/2)
collisions = sorted(n for n, poly in obstacles.items() if illustration.intersection(poly).area > 1e-7)
head_distance = min(illustration.distance(Point(x, y)) for x in [-13, 13] for y in [-13, 13])
assert box(-board['width']/2, -board['height']/2, board['width']/2, board['height']/2).covers(illustration)
assert head_distance >= 3.2
report = {
    'checked_date': '2026-11-02', 'mpn': '250-204', 'jlcpcb': 'C2765063',
    'base_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'raw_import_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
    'board_mm': [board['width'], board['height']],
    'manufacturer_body_width_depth_installed_height_mm': [15.5, 12, 13.1],
    'supplier_courtyard_width_depth_mm': [cw, ch],
    'old_terminal_courtyard_area_mm2': sum(p.area for p in old.values()),
    'candidate_courtyard_area_mm2': local.area,
    'courtyard_area_ratio': local.area / sum(p.area for p in old.values()),
    'top_obstacle_count_after_removing_old_terminals': len(obstacles),
    'fixed_placement_screens': screens,
    'fits_existing_placement': False,
    'illustration_center_mm': [center_x, center_y],
    'illustration_rotation_deg': 90,
    'illustration_bounds_mm': list(illustration.bounds),
    'illustration_colliding_components': collisions,
    'illustration_minimum_distance_to_mount_center_mm': head_distance,
    'scope': 'No axis-aligned space in unchanged placement, even before adding screw-head, wire-access or assembly clearance. This does not prove a redesigned placement impossible. No copper or manufacturing signoff.'
}
out = ROOT / 'artifacts/v2/connector-study'
out.mkdir(parents=True, exist_ok=True)
(out/'wago250204-verification.json').write_text(json.dumps(report, indent=2)+'\n')

ns = 'http://www.w3.org/2000/svg'
ET.register_namespace('', ns)
svg = ET.parse(ROOT/'artifacts/v2/placement.svg')
root = svg.getroot()
top = next(g for g in root.findall(f'{{{ns}}}g') if g.get('transform') == 'scale(1,-1)')
for group in list(top):
    title = group.find(f'{{{ns}}}title')
    if title is None or not title.text:
        continue
    name = title.text.split(' · ')[0]
    if name in old:
        top.remove(group)
    elif name in collisions:
        group.find(f'{{{ns}}}polygon').set('fill', '#e9a3a3')
        group.find(f'{{{ns}}}polygon').set('stroke', '#a51d25')
x1, y1, x2, y2 = illustration.bounds
ET.SubElement(top, f'{{{ns}}}rect', {'x': str(x1), 'y': str(y1), 'width': str(x2-x1),
              'height': str(y2-y1), 'fill': '#f4a324', 'fill-opacity': '.22',
              'stroke': '#b36c00', 'stroke-width': '.18', 'stroke-dasharray': '.4,.2'})
label = ET.SubElement(top, f'{{{ns}}}g', {'transform': f'translate({center_x-1},{center_y}) rotate(90) scale(1,-1)'})
ET.SubElement(label, f'{{{ns}}}text', {'font-family': 'sans-serif', 'font-size': '.7',
              'text-anchor': 'middle', 'fill': '#8a4600'}).text = 'WAGO 250-204 · 16 × 12.5 mm courtyard'
for node in root.findall(f'{{{ns}}}text'):
    if node.text and 'PLACEMENT ONLY' in node.text:
        node.text = 'FIT SCREEN · COLLISIONS IN RED · NOT AN IMPLEMENTED LAYOUT'
    elif node.text and 'Encoder capacitors' in node.text:
        node.text = 'Housing: 15.5 × 12 × 13.1 mm; PCB stays 34.5 × 34.5 mm'
    elif node.text and 'Five bare debug' in node.text:
        node.text = 'No free position at 0°/90° in the current placement; redesign required'
svg.write(out/'wago250204-fit.svg', encoding='unicode')
print(json.dumps(report, indent=2))
