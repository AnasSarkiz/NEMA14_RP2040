"""Check the native artwork, actual CAM clearances and unchanged fabrication data."""
import hashlib, importlib.util, io, json, pathlib, re, subprocess, zipfile
import cairosvg
from shapely.geometry import LineString, box
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/bottom-markings'
BASELINE = 'a6ddd7a'
PREFIX = 'pcb_silkscreen_path_bottom_marking_'
spec = importlib.util.spec_from_file_location('audit', ROOT/'scripts/audit-manufacturing.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
sha = lambda b: hashlib.sha256(b).hexdigest()

def native_ink(records):
    return unary_union([LineString([(p['x'],p['y']) for p in e['route']]).buffer(e['stroke_width']/2,quad_segs=16) for e in records])

def svg_geometry(geometry, color):
    result = []
    for polygon in getattr(geometry, 'geoms', [geometry]):
        if polygon.is_empty:
            continue
        rings = [polygon.exterior]+list(polygon.interiors)
        # Mirror X and invert Y to show the physical underside.
        d = ' '.join('M'+' L'.join(f'{-x:.6f},{-y:.6f}' for x,y in ring.coords)+' Z' for ring in rings)
        result.append(f'<path d="{d}" fill="{color}" fill-rule="evenodd"/>')
    return ''.join(result)

def canonical_cam(data):
    # Native export refreshes timestamps and declares silk apertures on other
    # layers too, renumbering the existing apertures. Compare the actual
    # fabrication commands with selected apertures resolved to their shape.
    text = data.decode()
    apertures = dict(re.findall(r'%ADD(\d+)([^%]+)\*%', text))
    text = re.sub(r'%ADD\d+[^%]+\*%\n?', '', text)
    text = re.sub(r'(?m)^D(\d+)\*$', lambda m:'APERTURE:'+apertures[m[1]], text)
    return '\n'.join(line for line in text.splitlines() if not any(s in line for s in ['CreationDate,','Created by tscircuit (builder) date','; DRILL file {tscircuit} date']))

def main():
    raw = (ROOT/'artifacts/board.circuit.json').read_bytes()
    board = json.loads(raw)
    baseline_raw = subprocess.check_output(['git','show',BASELINE+':artifacts/board.circuit.json'],cwd=ROOT)
    marks = [e for e in board if e.get('pcb_silkscreen_path_id','').startswith(PREFIX)]
    assert marks and all(e['layer']=='bottom' and e['stroke_width']==.15 for e in marks)
    assert [e for e in board if e not in marks] == json.loads(baseline_raw), 'Existing records changed'
    artwork_source = json.loads((ROOT/'src/bottom-markings.json').read_text())
    expected = [route for g in artwork_source['groups'] for route in g['routes']]
    assert [[list(p.values()) for p in e['route']] for e in marks] == expected
    assert artwork_source['warning'] == 'For evaluation only; not FCC approved for resale.'
    assert [g['name'] for g in artwork_source['groups'][:2]] == ['For evaluation only;', 'not FCC approved for resale.']
    with zipfile.ZipFile(io.BytesIO(subprocess.check_output(['git','show',BASELINE+':artifacts/nema14-gerbers.zip'],cwd=ROOT))) as old, zipfile.ZipFile(ROOT/'artifacts/nema14-gerbers.zip') as new:
        assert set(old.namelist()) == set(new.namelist())
        changed = [name for name in new.namelist() if old.read(name)!=new.read(name)]
        fabrication_changes = [name for name in new.namelist() if canonical_cam(old.read(name))!=canonical_cam(new.read(name))]
        assert fabrication_changes == ['B_SilkScreen.gbr'], fabrication_changes
        archive_sha = sha((ROOT/'artifacts/nema14-gerbers.zip').read_bytes())
    cam = ROOT/'artifacts/manufacturing'
    silk = audit.gerber(cam/'B_SilkScreen.gbr')[0]
    mask = audit.gerber(cam/'B_Mask.gbr')[0]
    holes = unary_union([audit.drill(p)[0] for p in cam.glob('*.drl')])
    artwork = native_ink(marks)
    # Allow only Gerber coordinate quantization / 0.5 um polygon simplification.
    assert artwork.difference(silk.buffer(.001)).area < 1e-6, 'Artwork missing from fabrication silkscreen'
    assert artwork.distance(mask) >= .15
    assert artwork.distance(holes) >= .1
    assert box(-17.4,-17.4,17.4,17.4).covers(artwork)
    groups = []
    start = 0
    for group in artwork_source['groups']:
        group_ink = native_ink(marks[start:start+len(group['routes'])])
        groups.append({'name':group['name'],'bounds_mm':list(group_ink.bounds),
                       'mask_clearance_mm':group_ink.distance(mask),'drill_clearance_mm':group_ink.distance(holes)})
        start += len(group['routes'])
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-18 -18 36 36" width="1200" height="1200">'
    svg += '<rect x="-18" y="-18" width="36" height="36" fill="#f3f4f6"/>'
    svg += '<rect x="-17.5" y="-17.5" width="35" height="35" rx="0.15" fill="#124f38"/>'
    svg += svg_geometry(mask,'#d5b36b')+svg_geometry(holes,'#f3f4f6')+svg_geometry(silk,'#ffffff')+'</svg>'
    OUT.mkdir(exist_ok=True)
    (OUT/'bottom-silkscreen.svg').write_text(svg)
    cairosvg.svg2png(bytestring=svg.encode(),write_to=str(OUT/'bottom-silkscreen.png'),output_width=1500,output_height=1500)
    report = {'passed':True,'baseline_commit':BASELINE,'before_board_sha256':sha(baseline_raw),
              'board_sha256':sha(raw),'fabrication_archive_sha256':archive_sha,
              'all_existing_native_records_unchanged':True,'source_vectors_match_native_paths':True,
              'only_changed_fabrication_commands':fabrication_changes,
              'regenerated_CAM_members_with_byte_changes':changed,
              'CAM_comparison':'timestamps and unused aperture declarations ignored; selected aperture shapes and all fabrication commands compared',
              'copper_mask_paste_drill_outline_BOM_CPL_commands_identical':True,
              'bottom_artwork_intact_in_fabrication_Gerber':True,'minimum_stroke_mm':.15,
              'mask_clearance_mm':artwork.distance(mask),'drill_clearance_mm':artwork.distance(holes),
              'warning':artwork_source['warning'],'underside_mirroring_applied':True,
              'official_logo_svg_sha256':sha((ROOT/'references/branding/tscircuit-official-logo.svg').read_bytes()),
              'groups':groups,'preview_source':'actual fabrication B_SilkScreen/B_Mask/Excellon; underside view'}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
