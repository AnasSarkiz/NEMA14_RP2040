#!/usr/bin/env python3
"""Check actual top stencil against physical via drills and native solder pads."""
import hashlib, importlib.util, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

def main():
    source = ROOT / 'artifacts/board.circuit.json'
    source_bytes = source.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    directory = ROOT / 'artifacts/manufacturing'
    audit = json.loads((directory / 'audit.json').read_text())
    archive_sha = hashlib.sha256((ROOT / 'artifacts/nema14-gerbers.zip').read_bytes()).hexdigest()
    paste_sha = hashlib.sha256((directory / 'F_Paste.gbr').read_bytes()).hexdigest()
    if audit['status'] != 'PASS' or audit['source_sha256'] != source_sha or audit['archive']['sha256'] != archive_sha or audit['files']['F_Paste.gbr']['sha256'] != paste_sha:
        raise ValueError('Via/stencil inspection requires a current passing source/archive-bound CAM audit')
    spec = importlib.util.spec_from_file_location('audit_geometry', ROOT / 'scripts/audit-manufacturing.py')
    geometry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(geometry)
    paste = geometry.gerber(directory / 'F_Paste.gbr')[0]
    circuit = json.loads(source_bytes)
    source_refs = {e['source_component_id']: e['name'] for e in circuit if e['type'] == 'source_component'}
    refs = {e['pcb_component_id']: source_refs[e['source_component_id']] for e in circuit if e['type'] == 'pcb_component'}
    pads = [e for e in circuit if e['type'] == 'pcb_smtpad' and e['layer'] == 'top']
    rows, errors = [], []
    for via in circuit:
        if via['type'] != 'pcb_via' or 'top' not in via['layers']:
            continue
        hole = geometry.shape({**via, 'shape': 'circle', 'width': via['hole_diameter'], 'height': via['hole_diameter']})
        overlaps = []
        for pad in pads:
            area = hole.intersection(geometry.shape(pad)).area
            if area > 1e-5:
                ep = pad.get('shape') == 'rect' and min(pad.get('width', 0), pad.get('height', 0)) > 2 and refs[pad['pcb_component_id']] in {'U_PD', 'U_MCU', 'U_DRV'}
                overlaps.append({'ref': refs[pad['pcb_component_id']], 'pad_id': pad['pcb_smtpad_id'], 'hole_overlap_mm2': area, 'requires_filled_capped_EP_process': ep})
        filled_ep = bool(overlaps) and all(p['requires_filled_capped_EP_process'] for p in overlaps)
        paste_overlap = paste.intersection(hole).area
        row = {'via_id': via['pcb_via_id'], 'center_mm': [via['x'], via['y']], 'outer_diameter_mm': via['outer_diameter'], 'hole_diameter_mm': via['hole_diameter'], 'native_SMT_pad_overlaps': overlaps, 'actual_paste_drill_overlap_mm2': paste_overlap, 'process': 'filled and copper capped; supplier acceptance pending' if filled_ep else 'ordinary plated via'}
        rows.append(row)
        if not filled_ep and (overlaps or paste_overlap > 1e-7):
            errors.append(row)
    if source.read_bytes() != source_bytes:
        raise ValueError('Frozen source changed during via/stencil inspection')
    result = {'source_sha256': source_sha, 'actual_archive_sha256': archive_sha, 'actual_F_Paste_sha256': paste_sha, 'actual_drill_sha256': {name: info['sha256'] for name, info in audit['files'].items() if name.endswith('.drl')}, 'status': 'FAIL' if errors else 'PASS', 'top_spanning_vias_checked': len(rows), 'filled_capped_EP_vias': [r for r in rows if r['process'].startswith('filled')], 'ordinary_via_drill_paste_or_SMT_overlap_errors': errors, 'via_measurements': rows, 'scope': 'Actual independently parsed stencil; native via drills reconciled against actual Excellon by the bound CAM audit. No physical filling/capping or reflow qualification is claimed.'}
    (directory / 'via-paste-inspection.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'source_sha256', 'top_spanning_vias_checked', 'ordinary_via_drill_paste_or_SMT_overlap_errors']}, indent=2))
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
