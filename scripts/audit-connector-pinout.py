"""Audit numbered contacts, native pad orientation and reference connector roles.

This is a CAD connectivity check, not USB certification or a physical crimp test.
Run with an optional CircuitJSON path to check a fresh source build as well.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'artifacts/board.circuit.json'
records = json.loads(path.read_text())
reference_dir = ROOT / 'references/rishabh-connectors-1.0.42'
snapshot_path = reference_dir / 'connector-extract.json'
snapshot = json.loads(snapshot_path.read_text())
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


class Circuit:
    def __init__(self, rows):
        self.rows = rows
        self.components = {e['name']: e for e in rows if e['type'] == 'source_component'}
        self.nets = {e['name']: e.get('subcircuit_connectivity_map_key') for e in rows if e['type'] == 'source_net'}

    def port(self, name, pin):
        component = self.components[name]
        return next(e for e in self.rows if e['type'] == 'source_port' and
                    e['source_component_id'] == component['source_component_id'] and e['pin_number'] == pin)

    def key(self, name, pin):
        return self.port(name, pin).get('subcircuit_connectivity_map_key')

    def pcb(self, name):
        return next(e for e in self.rows if e['type'] == 'pcb_component' and
                    e['source_component_id'] == self.components[name]['source_component_id'])

    def pad(self, name, pin):
        port = self.port(name, pin)
        pcb_port = next(e for e in self.rows if e['type'] == 'pcb_port' and e['source_port_id'] == port['source_port_id'])
        pads = [e for e in self.rows if e['type'] in ['pcb_smtpad', 'pcb_plated_hole'] and e.get('pcb_port_id') == pcb_port['pcb_port_id']]
        require(len(pads) == 1, f'{name}.{pin}: expected one physical pad')
        return pads[0]

    def relative(self, name, pin, anchor):
        # Relative contact positions remove placement and footprint bounding-box offsets.
        p, a = self.pad(name, pin), self.pad(name, anchor)
        angle = math.radians(-self.pcb(name)['rotation'])
        px, py = center(p)
        ax, ay = center(a)
        x, y = px - ax, py - ay
        return x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle)


def center(pad):
    if pad.get('shape') == 'polygon':
        return tuple((min(v[k] for v in pad['points']) + max(v[k] for v in pad['points'])) / 2 for k in ['x', 'y'])
    return pad['x'], pad['y']


ours, ref = Circuit(records), Circuit(snapshot['records'])
for filename, expected in snapshot['provenance']['source_files_sha256'].items():
    require(hashlib.sha256((reference_dir / filename).read_bytes()).hexdigest() == expected,
            'Reference source hash mismatch: ' + filename)


def same(circuit, a, b):
    return bool(circuit.key(*a)) and circuit.key(*a) == circuit.key(*b)


def net(name, pin, expected):
    require(bool(ours.nets.get(expected)) and ours.key(name, pin) == ours.nets.get(expected),
            f'{name}.{pin} must connect to {expected}')


def nc(name, pin):
    p = ours.port(name, pin)
    require(p.get('do_not_connect') is True and not p.get('subcircuit_connectivity_map_key'),
            f'{name}.{pin} must be explicitly disconnected')


# C165948 supplier indices are not USB contact names. Reference wrappers remap them.
# Each tuple: supplier index, contact identity, reference power index, reference data index.
contacts = [
    (1, 'EH2', 2, 14), (2, 'EH1', 4, 16), (3, 'EH4', 3, 15), (4, 'EH3', 1, 13),
    (5, 'B8', 7, 19), (6, 'A5', 8, 20), (7, 'B7', 9, 21), (8, 'A6', 10, 22),
    (9, 'A7', 11, 23), (10, 'B6', 12, 24), (11, 'A8', 13, 25), (12, 'B5', 14, 26),
    (13, 'A1B12', 5, 17), (14, 'B1A12', 16, 28), (15, 'B4A9', 15, 27), (16, 'A4B9', 6, 18),
]
for name, reference_name, reference_column in [('J_PD', 'J_MOTOR_USB', 2), ('J_DATA', 'J_USB', 3)]:
    c = ours.components[name]
    require(c.get('manufacturer_part_number') == 'TYPE-C-31-M-12' and
            c.get('supplier_part_numbers', {}).get('jlcpcb') == ['C165948'], name + ': exact connector identity')
    for row in contacts:
        pin, contact = row[:2]
        # Shell EH aliases differ after legacy remapping; actual pad geometry is authoritative.
        if pin > 4:
            require(contact in ours.port(name, pin)['port_hints'], f'{name}.{pin}: wrong USB contact identity')
            require(contact in ref.port(reference_name, row[reference_column])['port_hints'], 'Reference USB contact changed: ' + contact)
        u, v = ours.relative(name, pin, 6), ref.relative(reference_name, row[reference_column], 8 if name == 'J_PD' else 20)
        require(math.dist(u, v) < .001, f'{name}.{pin}: pad position differs from mapped reference contact')
        p, q = ours.pad(name, pin), ref.pad(reference_name, row[reference_column])
        # Supplier revisions have different shell slot lengths. Electrical pad positions
        # and copper outlines match; preserve and disclose the distinct existing drills.
        for field in ['type', 'shape', 'width', 'height', 'hole_width', 'outer_width', 'outer_height']:
            require(p.get(field) == q.get(field), f'{name}.{pin}: native pad {field} differs from reference')
        if pin <= 4:
            expected = 1.499997 if pin in [1, 4] else 1.1999976
            require(abs(p['hole_height'] - expected) < 1e-6, f'{name}.{pin}: existing shell slot changed')
    for pin in [1, 2, 3, 4, 13, 14]:
        net(name, pin, 'GND')
    for pin in [15, 16]:
        net(name, pin, 'PD_VBUS' if name == 'J_PD' else 'DATA_VBUS')
    net(name, 6, 'PD_CC1' if name == 'J_PD' else 'DATA_CC1')
    net(name, 12, 'PD_CC2' if name == 'J_PD' else 'DATA_CC2')
    for pin in [5, 11]:
        nc(name, pin)

for pin, expected in [(7, 'USB_DM'), (8, 'USB_DP'), (9, 'USB_DM'), (10, 'USB_DP')]:
    net('J_DATA', pin, expected)
for pin in [7, 8, 9, 10]:
    nc('J_PD', pin)  # WCH CH224DS1 v1F section5.5, required PD-only behavior.
for name, expected in [('R_CC1', 'DATA_CC1'), ('R_CC2', 'DATA_CC2')]:
    require(ours.components[name].get('resistance') == 5100, name + ': separate5.1k sink termination')
    net(name, 1, expected)
    net(name, 2, 'GND')
require(ours.nets['DATA_CC1'] != ours.nets['DATA_CC2'], 'Data CC pins must not be tied together')
require(ours.nets['PD_CC1'] != ours.nets['PD_CC2'], 'PD CC pins must not be tied together')
require(ours.nets['DATA_VBUS'] != ours.nets['PD_VBUS'], 'Computer and15V VBUS must remain separate')
for pin, expected in {1:'PD_VDD', 2:'PD_VDD', 3:'PD_VDD', 4:'PD_LEGACY_DATA', 5:'PD_LEGACY_DATA',
                      6:'PD_CC2', 7:'PD_CC1', 9:'GND', 11:'GND'}.items():
    net('U_PD', pin, expected)
nc('U_PD', 8)
for name, expected in [('D_DATA', 'DATA_VBUS'), ('D_PD', 'PD_VBUS')]:
    # Native1N5819WS supplier pin1=K, pin2=A.
    net(name, 2, expected)
    net(name, 1, 'LOGIC_IN')
for pin, expected in {1:'USB_DP', 2:'GND', 3:'USB_DM', 4:'USB_DM', 5:'DATA_VBUS', 6:'USB_DP'}.items():
    net('U_ESD', pin, expected)
is_rp2040 = ours.components['U_MCU'].get('manufacturer_part_number') == 'RP2040'
if is_rp2040:
    for resistor, bus, mcu_net, pin in [('R_DM', 'USB_DM', 'MCU_DM', 46), ('R_DP', 'USB_DP', 'MCU_DP', 47)]:
        require(ours.components[resistor].get('resistance') == 27, resistor + ': RP2040 PHY series resistance')
        net(resistor, 1, mcu_net)
        net(resistor, 2, bus)
        net('U_MCU', pin, mcu_net)
else:
    net('U_MCU', 26, 'USB_DM')
    net('U_MCU', 27, 'USB_DP')

motor_rows = [(1, 'A_PLUS', 'Black', 24), (2, 'A_MINUS', 'Green', 21),
              (3, 'B_PLUS', 'Red', 26), (4, 'B_MINUS', 'Blue', 1)]
require(ours.components['J_MOTOR'].get('manufacturer_part_number') == 'B4B-PH-K-S(LF)(SN)', 'Exact JST PH header required')
for pin, expected, color, driver_pin in motor_rows:
    net('J_MOTOR', pin, expected)
    net('U_DRV', driver_pin, expected)
    require(expected in ref.port('J1', pin)['port_hints'], f'JST pin{pin} differs from reference phase identity')
    require(math.dist(ours.relative('J_MOTOR', pin, 1), ref.relative('J1', pin, 1)) < .001,
            f'JST pin{pin}: reference mounting-side order/pitch differs')
    require(abs(ours.pad('J_MOTOR', pin)['hole_diameter'] - .75) < 1e-6, 'JST finished drill requirement changed')
for circuit, name in [(ours, 'J_MOTOR'), (ref, 'J1')]:
    cad = next(e for e in circuit.rows if e['type'] == 'cad_component' and e['source_component_id'] == circuit.components[name]['source_component_id'])
    require('C131334' in cad.get('model_step_url', ''), name + ': exact supplier STEP required')
    # Native model terminal row x=0,2,4,6, y=0. Match each terminal to its PCB pad.
    a = math.radians(cad['rotation']['z'])
    for pin in range(1, 5):
        x, y = (pin - 1) * 2 - cad['model_origin_position']['x'], -cad['model_origin_position']['y']
        projected = (cad['position']['x'] + x*math.cos(a) - y*math.sin(a),
                     cad['position']['y'] + x*math.sin(a) + y*math.cos(a))
        pad = circuit.pad(name, pin)
        require(math.dist(projected, center(pad)) < .001, name + ': CAD terminal/pin orientation mismatch')

# Independently verify the reference relationships, rather than just its labels.
for a, b in [(('J_MOTOR_USB', 8), ('U_PD', 7)), (('J_MOTOR_USB', 14), ('U_PD', 6)),
             (('J_USB', 22), ('J_USB', 24)), (('J_USB', 21), ('J_USB', 23)),
             (('J_USB', 20), ('R_CC1', 1)), (('J_USB', 26), ('R_CC2', 1)),
             (('J_USB', 21), ('R_USB1', 1)), (('R_USB1', 2), ('U1', 46)),
             (('J_USB', 22), ('R_USB2', 1)), (('R_USB2', 2), ('U1', 47)),
             (('J1', 2), ('DRIVER', 7)), (('J1', 4), ('DRIVER', 8)),
             (('J1', 1), ('R_PHASE_A', 2)), (('R_PHASE_A', 1), ('DRIVER', 5)),
             (('J1', 3), ('R_PHASE_B', 2)), (('R_PHASE_B', 1), ('DRIVER', 10))]:
    require(same(ref, a, b), f'Reference endpoint mismatch: {a} -> {b}')
report = {
    'status': 'FAIL' if errors else 'PASS', 'input': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
    'circuit_json_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'reference': snapshot['provenance'], 'reference_extract_sha256': hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
    'checked_usb_supplier_contacts': 32, 'checked_motor_contacts': 4,
    'reference_geometry_comparison_tolerance_mm': .001,
    'motor_mapping': [{'pin': p, 'phase': n, 'wire': c, 'a4988_pin': d} for p,n,c,d in motor_rows],
    'intentional_differences': ['Fixed15V PD-only, no legacy DP/DM negotiation (WCH section5.5); reference supports legacy protocols and configurable5-20V.',
                              'A4988 direct phase outputs; reference DRV8825 positive phases pass through telemetry shunts.',
                              'CH32 uses its WCH PHY circuit; RP2040 retains27ohm series resistors as in reference.',
                              'Existing supplier shell slots0.8x1.2/1.5mm versus reference0.8x1.4/1.6mm. Contact centres and copper outlines match; insertion/wetting require supplier/sample acceptance.'],
    'qualification': 'CAD only. USB reversibility/enumeration/PD/backfeed and numbered housing/winding continuity require prototype tests. JST PH does not define a universal motor pinout.',
    'errors': errors,
}
suffix = '-source' if len(sys.argv) > 1 else ''
destination = ROOT / f'artifacts/validation/connector-pinout-audit{suffix}.json'
destination.parent.mkdir(exist_ok=True, parents=True)
destination.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'contacts': 36, 'errors': errors, 'report': str(destination)}, indent=2))
raise SystemExit(bool(errors))
