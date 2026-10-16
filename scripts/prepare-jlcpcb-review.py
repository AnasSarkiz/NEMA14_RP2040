#!/usr/bin/env python3
"""Create a separately identified order-review CAM package from frozen native CAD.

Copper, mask, drill and outline bytes are copied unchanged. Only assembly tables,
paste and silkscreen are corrected. The native export remains historical evidence.
No supplier placement approval, stock check or physical qualification is implied.
"""
import csv, hashlib, importlib.util, json, math, pathlib, subprocess, zipfile
from html import escape
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely.affinity import scale

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/jlcpcb-review'
CAM = OUT / 'cam'
BARE = set() # Derived from native simple_test_point records below.
spec = importlib.util.spec_from_file_location('cam_audit', ROOT / 'scripts/audit-manufacturing.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write_csv(path, fields, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def write_gerber(path, geometry):
    """Emit boolean result as metric RS-274X regions, including clear holes."""
    lines = ['G04 Verified JLCPCB order-review CAM; see manifest.json*',
             '%FSLAX46Y46*%', '%MOMM*%', '%ADD10C,0.010000*%', 'D10*', 'G01*']
    polygons = list(geometry.geoms) if hasattr(geometry, 'geoms') else [geometry]
    for polygon in polygons:
        if polygon.is_empty:
            continue
        assert polygon.geom_type == 'Polygon'
        for ring, polarity in [(polygon.exterior, 'D')] + [(r, 'C') for r in polygon.interiors]:
            lines += [f'%LP{polarity}*%', 'G36*']
            for i, (x, y) in enumerate(ring.coords):
                lines.append(f'X{round(x*1e6)}Y{round(y*1e6)}D{2 if i==0 else 1:02}*')
            lines.append('G37*')
    lines += ['%LPD*%', 'M02*']
    path.write_text('\n'.join(lines) + '\n')

def font_geometry(text, x, y, alphabet, size=1., stroke=.15):
    shapes = []
    width = (len(text)*.8-.15)*size
    for i, character in enumerate(text):
        for segment in alphabet.get(character.upper(), []):
            shapes.append(LineString([(x-width/2+(i*.8+segment['x1']*.65)*size,
                                      y+(segment['y1']-.5)*size),
                                     (x-width/2+(i*.8+segment['x2']*.65)*size,
                                      y+(segment['y2']-.5)*size)]).buffer(stroke/2, quad_segs=8))
    return unary_union(shapes)

def main():
    OUT.mkdir(exist_ok=True)
    CAM.mkdir(exist_ok=True)
    raw = (ROOT / 'artifacts/board.circuit.json').read_bytes()
    native = json.loads(raw)
    src = {e['source_component_id']: e for e in native if e['type']=='source_component'}
    BARE.update(s['name'] for s in src.values() if s['ftype']=='simple_test_point')
    pc = {e['pcb_component_id']: e for e in native if e['type']=='pcb_component'}
    pads = [e for e in native if e['type']=='pcb_smtpad']
    original_zip = ROOT / 'artifacts/nema14-gerbers.zip'
    with zipfile.ZipFile(original_zip) as z:
        members = {pathlib.Path(n).name: z.read(n) for n in z.namelist() if not n.endswith('/')}
    for path in CAM.iterdir():
        if path.suffix in {'.csv', '.gbr', '.drl'}:
            path.unlink()
    for name, data in members.items():
        (CAM/name).write_bytes(data)

    # Generated supplier apertures shrink every pad to 70% in both dimensions.
    # Keep that policy except where it fails the unchanged 100 um stencil screen.
    # QFN exposed pads use four separated windows totaling 60% of copper area.
    paste = []
    aperture_changes = []
    for pad in pads:
        ref = src[pc[pad['pcb_component_id']]['source_component_id']]['name']
        if ref in BARE or pc[pad['pcb_component_id']].get('do_not_place'):
            continue
        if pad['shape']=='polygon':
            geometry = scale(audit.shape(pad), xfact=.7, yfact=.7, origin='centroid')
            assert geometry.geom_type=='Polygon' and not geometry.interiors
            paste.append({'type':'pcb_solder_paste','pcb_solder_paste_id':f'order_paste_{len(paste)}',
                          'pcb_component_id':pad['pcb_component_id'],'pcb_smtpad_id':pad['pcb_smtpad_id'],
                          'shape':'polygon','layer':pad['layer'],
                          'points':[{'x':x,'y':y} for x,y in geometry.exterior.coords]})
            continue
        assert pad['shape'] in {'rect','pill','rotated_pill'}, f'Unsupported fitted SMT pad: {ref} {pad}'
        w, h = pad['width'], pad['height']
        if ref in {'U_MCU','U_DRV','U_PD'} and w>2 and h>2:
            aw, ah = w*math.sqrt(.6)/2, h*math.sqrt(.6)/2
            windows = [(pad['x']+dx*w/4, pad['y']+dy*h/4, aw, ah)
                       for dx in (-1,1) for dy in (-1,1)]
            policy = 'four windows; 60% exposed-pad area'
        else:
            factor = .7
            while min(w,h)*factor/.1 < 1.5 or w*h*factor/(2*(w+h)*.1) < .70:
                factor += .05
            assert factor <= .95 + 1e-9, f'100 um stencil cannot release {ref} {pad}'
            windows = [(pad['x'], pad['y'], w*factor, h*factor)]
            policy = f'{factor:.2f} linear pad scale'
        for x,y,aw,ah in windows:
            paste.append({'type':'pcb_solder_paste','pcb_solder_paste_id':f'order_paste_{len(paste)}',
                          'pcb_component_id':pad['pcb_component_id'],'pcb_smtpad_id':pad['pcb_smtpad_id'],
                          'shape':pad['shape'],'layer':pad['layer'],'x':x,'y':y,'width':aw,'height':ah,
                          'ccw_rotation':pad.get('ccw_rotation',0)})
        if pad['shape'] in {'pill','rotated_pill'}:
            paste[-1]['radius']=min(aw,ah)/2
        if len(windows)>1 or factor>.700001:
            aperture_changes.append({'reference':ref,'pad':pad['pcb_smtpad_id'],'policy':policy})
    reviewed = [e for e in native if e['type']!='pcb_solder_paste'] + paste
    assert [e for e in reviewed if e['type']!='pcb_solder_paste'] == [e for e in native if e['type']!='pcb_solder_paste']
    source_path = OUT / 'order-source.circuit.json'
    source_path.write_text(json.dumps(reviewed, indent=2)+'\n')
    for side, name in [('top','F_Paste.gbr'), ('bottom','B_Paste.gbr')]:
        write_gerber(CAM/name, unary_union([audit.shape(e) for e in paste if e['layer']==side]))

    # Imported reference captions can retain obsolete placement offsets. Build
    # whole, readable captions from current component centers instead of cutting
    # letters over pads. Omitted captions remain in the assembly drawing/table.
    alphabet = json.loads((ROOT/'scripts/order-alphabet.json').read_text())
    silk_changes = []
    for side, silk_name, mask_name in [('top','F_SilkScreen.gbr','F_Mask.gbr'),
                                      ('bottom','B_SilkScreen.gbr','B_Mask.gbr')]:
        original, _, _ = audit.gerber(CAM/silk_name)
        mask, _, _ = audit.gerber(CAM/mask_name)
        holes = unary_union([audit.drill(CAM/n)[0] for n in members if n.endswith('.drl')])
        safe = box(-17.399,-17.399,17.399,17.399).difference(mask.buffer(.151)).difference(holes.buffer(.101))
        outlines, labels, omitted = [], [], []
        occupied = Polygon()
        layer_components = [c for c in pc.values() if c['layer']==side]
        layer_components.sort(key=lambda c: (0 if src[c['source_component_id']]['name'].startswith('J_') else
                                            1 if src[c['source_component_id']]['name'].startswith('U_') else 2,
                                            src[c['source_component_id']]['name']))
        # Mask holes define solderability; physical courtyard geometry defines
        # where adjacent reference captions can fit without hiding under parts.
        body_guard = unary_union([box(c['center']['x']-c['width']/2,c['center']['y']-c['height']/2,
                                      c['center']['x']+c['width']/2,c['center']['y']+c['height']/2)
                                  for c in layer_components])
        knockout_roles = []
        if side == 'top':
            role_marks=[e for e in native if e['type']=='pcb_silkscreen_text' and e.get('text') in ['PWR','DATA'] and e['layer']=='top']
            assert len(role_marks)==2 and {e['text'] for e in role_marks}=={'PWR','DATA'}
            for mark in role_marks:
                caption=mark['text'];x=mark['anchor_position']['x'];y=mark['anchor_position']['y'];font=mark['font_size'];assert font>=.8
                letters=font_geometry(caption,x,y,alphabet,size=font,stroke=.15)
                region=box(*letters.bounds).buffer(.25,join_style='mitre')
                assert safe.covers(region) and not region.intersects(body_guard), 'Role marking conflicts with a pad, hole or component: '+caption
                knockout=region.difference(letters)
                labels.append(knockout);occupied=occupied.union(region.buffer(.2))
                knockout_roles.append({'caption':caption,'centre_mm':[x,y],'font_height_mm':font,'negative_stroke_mm':.15,'rectangle_bounds_mm':list(region.bounds)})
        for c in layer_components:
            ref = src[c['source_component_id']]['name']
            cx,cy = c['center']['x'],c['center']['y']
            w,h = c['width'],c['height']
            border = box(cx-w/2-.2,cy-h/2-.2,cx+w/2+.2,cy+h/2+.2).boundary.buffer(.075)
            outlines.append(border.intersection(safe))
            positions = []
            for distance in (.75,1.,1.5,2.):
                for offset in (0,-.5,.5,-1.,1.):
                    positions += [(cx+offset,cy+h/2+distance),(cx+offset,cy-h/2-distance),
                                  (cx+w/2+distance+len(ref)*.4,cy+offset),
                                  (cx-w/2-distance-len(ref)*.4,cy+offset)]
            found = False
            for x,y in positions:
                text = font_geometry(ref,x,y,alphabet,size=1.3,stroke=.15)
                if not text.is_empty and safe.covers(text) and not text.intersects(occupied) and not text.intersects(body_guard):
                    labels.append(text)
                    occupied = occupied.union(text.buffer(.2))
                    found = True
                    break
            if not found:
                omitted.append(ref)
        clipped = unary_union(outlines+labels).simplify(.0005,preserve_topology=True)
        write_gerber(CAM/silk_name, clipped)
        silk_changes.append({'layer':side,'original_area_mm2':original.area,
                             'new_area_mm2':clipped.area,'reference_captions_placed':len(labels),
                             'captions_omitted_for_clearance':omitted,'knockout_role_markings':knockout_roles,
                             'policy':'current component outlines and intact reference captions; board inset 0.101 mm, mask guard 0.151 mm, drill guard 0.101 mm; full references in assembly files'})

    # Source identities, not display abbreviations, determine procurement.
    bom, cpl, manual, orientations = [], [], [], []
    old_bom = {e['Designator']:e for e in csv.DictReader((CAM/'bom.csv').open())}
    for component in pc.values():
        s = src[component['source_component_id']]
        ref = s['name']
        if ref in BARE or component.get('do_not_place'):
            continue
        part_numbers = s.get('supplier_part_numbers',{}).get('jlcpcb',[])
        assert len(part_numbers)==1 and s.get('manufacturer_part_number'), f'Missing purchasing identity: {ref}'
        mpn = s['manufacturer_part_number']
        value = s.get('display_resistance',s.get('display_capacitance',mpn))
        footprint = old_bom[ref]['Footprint']
        row = {'Designator':ref, 'Comment':mpn, 'Value':value,'Footprint':footprint,
               'JLCPCB Part #':part_numbers[0],'Manufacturer Part Number':mpn}
        bom.append(row)
        position = {'Designator':ref,'Mid X':f"{component['center']['x']:.6f}",
                    'Mid Y':f"{component['center']['y']:.6f}", 'Layer':component['layer'],
                    'Rotation':component.get('rotation',0)}
        cpl.append(position)
        part_pads = [e for e in native if e['type'] in {'pcb_smtpad','pcb_plated_hole'} and e.get('pcb_component_id')==component['pcb_component_id']]
        orientations.append({'reference':ref, 'part':part_numbers[0], 'mpn':mpn,
                             'center_mm':component['center'], 'layer':component['layer'],
                             'rotation_deg':component.get('rotation',0),
                             'pin1_location':component.get('pin1_location'),
                             'physical_pads':[{'pin_hints':p.get('port_hints',[]),'center_mm':list(audit.shape(p).centroid.coords)[0]} for p in part_pads],
                             'manufacturer_pickup_datum_and_rotation_approved':False,
                             'process':'top-side SMT; USB shell tabs need secondary soldering' if ref in {'J_PD','J_DATA'} else 'top-side SMT'})
    bom_fields = list(bom[0])
    write_csv(CAM/'bom.csv', bom_fields, bom)
    write_csv(CAM/'pick_and_place.csv', list(cpl[0]), cpl)
    smt = bom
    grouped = {}
    for row in smt:
        key = (row['JLCPCB Part #'],row['Comment'],row['Footprint'])
        grouped.setdefault(key,[]).append(row['Designator'])
    write_csv(OUT/'JLCPCB-BOM.csv', ['Comment','Designator','Footprint','LCSC Part #'],
              [{'Comment':key[1],'Designator':','.join(refs),'Footprint':key[2],'LCSC Part #':key[0]}
               for key,refs in grouped.items()])
    write_csv(OUT/'JLCPCB-CPL.csv', list(cpl[0]), cpl)
    write_csv(OUT/'Manual-THT-BOM.csv', bom_fields, manual)
    (OUT/'placement-orientation-review.json').write_text(json.dumps(orientations,indent=2)+'\n')
    # All CAM used by the independent audit is inside this exact archive.
    cam_zip = OUT/'review-cam.zip'
    with zipfile.ZipFile(cam_zip,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(CAM.iterdir()):
            if p.suffix in {'.csv','.gbr','.drl'}:
                z.write(p,p.name)
    fab_zip = OUT/'JLCPCB-Gerbers.zip'
    with zipfile.ZipFile(fab_zip,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(CAM.iterdir()):
            if p.suffix in {'.gbr','.drl'} and p.name not in {'F_Fab.gbr','B_Fab.gbr'}:
                z.write(p,p.name)
    unchanged = {name:sha(data) for name,data in members.items()
                 if name.endswith('.drl') or name.endswith('_Cu.gbr') or name.endswith('_Mask.gbr') or name=='Edge_Cuts.gbr'}
    assert all((CAM/name).read_bytes()==members[name] for name in unchanged)
    assert (ROOT/'artifacts/board.circuit.json').read_bytes()==raw
    bottom = [row['Designator'] for row in cpl if row['Layer']=='bottom']
    manifest = {'native_board_sha256':sha(raw), 'native_export_sha256':sha(original_zip.read_bytes()),
                'order_source_sha256':sha(source_path.read_bytes()),'review_cam_sha256':sha(cam_zip.read_bytes()),
                'fabrication_zip_sha256':sha(fab_zip.read_bytes()),
                'source_github_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'electrical_source_and_all_nonpaste_records_unchanged':True,
                'copied_unchanged_copper_mask_drill_outline':unchanged,
                'fitted_components':len(bom),'SMT_components':len(smt), 'manual_THT_components':len(manual),
                'bottom_SMT_references':bottom, 'excluded_bare_interfaces':sorted(BARE),'excluded_DNP_references':sorted(src[c['source_component_id']]['name'] for c in pc.values() if c.get('do_not_place')),
                'paste_changes':aperture_changes, 'silkscreen_changes':silk_changes,
                'assembly_preview_approved_by_JLCPCB':False,'physical_hardware_tested':False,
                'rear_motor_compatibility_verified':False,
                'process_requests':{'layers':4,'dimensions_mm':[35,35],'thickness_mm':1.6,
                                    'outer_copper_min_um':35,'inner_copper_min_um':17.5,
                                    'via_barrel_plating_min_um':20,'surface_finish':'ENIG requested for bare contact pads',
                                    'stencil_thickness_um':100,
                                    'thermal_via_process':'filled and capped/planarized via-in-pad; supplier must confirm capability and quote',
                                    'assembly_sides':'top and bottom' if bottom else 'top',
                                    'JST_process':'top-side SMT C160390; no drilled JST terminals'}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ['native_board_sha256','fitted_components','SMT_components','bottom_SMT_references']},indent=2))

if __name__=='__main__':
    main()
