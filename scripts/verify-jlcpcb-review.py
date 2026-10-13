#!/usr/bin/env python3
"""Gate the separate JLCPCB engineering-review files against frozen CAD and CAM."""
import csv, datetime, hashlib, json, pathlib, subprocess, zipfile
from placement_advisories import orientation_advisories_only
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/jlcpcb-review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    subprocess.run(['node','scripts/check-order-paste-schema.mjs'],cwd=ROOT,check=True)
    subprocess.run(['node','scripts/audit-native-json-compatibility.mjs'],cwd=ROOT,check=True)
    manifest=json.loads((OUT/'manifest.json').read_text())
    board_path=ROOT/'artifacts/board.circuit.json'
    board=json.loads(board_path.read_text())
    source=json.loads((OUT/'order-source.circuit.json').read_text())
    assert manifest['native_board_sha256']==sha(board_path)
    assert manifest['order_source_sha256']==sha(OUT/'order-source.circuit.json')
    assert [e for e in source if e['type']!='pcb_solder_paste']==[e for e in board if e['type']!='pcb_solder_paste']
    cam=json.loads((OUT/'cam/audit.json').read_text())
    assert cam['source_sha256']==manifest['order_source_sha256']
    assert cam['status']=='PASS' and not cam['issues'], cam['issues']
    assert cam['archive']['sha256']==sha(OUT/'review-cam.zip')
    assert manifest['review_cam_sha256']==sha(OUT/'review-cam.zip')
    assert manifest['fabrication_zip_sha256']==sha(OUT/'JLCPCB-Gerbers.zip')
    with zipfile.ZipFile(OUT/'JLCPCB-Gerbers.zip') as z:
        for name in z.namelist():
            assert z.read(name)==(OUT/'cam'/name).read_bytes()
            if name in manifest['copied_unchanged_copper_mask_drill_outline']:
                assert hashlib.sha256(z.read(name)).hexdigest()==manifest['copied_unchanged_copper_mask_drill_outline'][name]
        assert len([n for n in z.namelist() if n.endswith('_Cu.gbr')])==4
        assert {'drill_npth.drl','drill-L1-L4.drl','Edge_Cuts.gbr'}<=set(z.namelist())
    src={e['source_component_id']:e for e in board if e['type']=='source_component'}
    pc={src[e['source_component_id']]['name']:e for e in board if e['type']=='pcb_component'}
    expected={n for n,c in pc.items() if src[c['source_component_id']]['ftype']!='simple_test_point'}
    purchasing={}
    for row in csv.DictReader((OUT/'JLCPCB-BOM.csv').open()):
        for ref in row['Designator'].split(','):
            assert ref not in purchasing
            purchasing[ref]=row
            s=src[pc[ref]['source_component_id']]
            assert row['LCSC Part #'] in s['supplier_part_numbers']['jlcpcb']
            assert row['Comment']==s['manufacturer_part_number']
    assert set(purchasing)==expected
    placements={}
    for row in csv.DictReader((OUT/'JLCPCB-CPL.csv').open()):
        ref=row['Designator'];assert ref not in placements
        placements[ref]=row;c=pc[ref]
        for field,value in [('Mid X',c['center']['x']),('Mid Y',c['center']['y']),('Rotation',c['rotation'])]:
            assert abs(float(row[field])-value)<.000001
        assert row['Layer']==c['layer']
    assert set(placements)==expected
    manual=list(csv.DictReader((OUT/'Manual-THT-BOM.csv').open()))
    assert not manual, 'All fitted components are top-side SMT; USB shell joints are in the separate joint plan'
    native=json.loads((ROOT/'artifacts/resume-validation.json').read_text())
    assert native['board_sha256']==sha(board_path) and native['native_STEP_mechanical_pass']
    checks={e['check']:e for e in native['checks']}
    assert len(checks)==20
    for name,check in checks.items():
        if name=='native_placement' and check['exit_code']:
            assert orientation_advisories_only((ROOT/check['log']).read_text()), 'Placement log has unreviewed diagnostics or real DRC failures'
            continue
        assert check['exit_code']==0, name
    for relative,key in [('artifacts/reference-feedback/every-trace-review.json','passed'),
                         ('artifacts/reference-feedback/circuit-verification.json','passed')]:
        proof=json.loads((ROOT/relative).read_text())
        assert proof[key] and proof['board_sha256']==sha(board_path)
    receipt={'prepared_for_JLCPCB_engineering_review':True,
             'order_review_CAM_passed':True,'native_order_paste_schema_passed':True,'native_board_sha256':sha(board_path),
             'order_source_sha256':manifest['order_source_sha256'],
             'JLCPCB_gerber_zip_sha256':sha(OUT/'JLCPCB-Gerbers.zip'),
             'SMT_components':len(expected),'manual_THT_components':0,
             'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'every_trace_and_segment_reviewed':True,'electrical_geometry_and_connections_preserved':True,
             'default_export_manufacturing_qualified':True,
             'upstream_native_export_retained_as_diagnostic':True,
             'JLCPCB_order_submitted':False,'JLCPCB_review_approved':False,
             'production_release_approved':False,'hardware_operation_verified':False,
             'rear_motor_compatibility_verified':False,
             'remaining_supplier_review_items':[
                 'Confirm native land-pattern CPL datum, pickup rotation, pin 1 and all polarized parts in JLCPCB placement preview; USB body and land-pattern centers differ.',
                 'Confirm filled/capped planarized exposed-pad vias, 100 um stencil windows, paste/reflow process and requested copper/plating minima.',
                 'Confirm exact BOM availability and quote; no substitutions authorized.',
                 ('Confirm two-sided SMT support; quote USB shell secondary soldering or use the separate manual THT plan.' if manifest['bottom_SMT_references'] else 'Confirm top-side SMT support; quote USB shell secondary soldering or use the separate manual THT plan.'),
                 'Review USB signal/reference layout and switching/sense/ground current paths; no controlled-impedance, EMC or thermal hardware qualification is claimed.'
             ],
             'remaining_CAD_tooling_review':[],
             'remaining_hardware_validation':[
                 'Program firmware and verify USB data, PD 15 V negotiation, 3.3 V regulation and backfeed isolation.',
                 'Measure phase current and thermal behavior; exercise motor, TMP102, LEDs and buzzer.',
                 'Verify real cables, fasteners, underside clearance and mounting stack; rear motor fit is unverified.'
             ]}
    receipt_path=OUT/'order-review-verification.json'
    if receipt_path.exists():
        previous=json.loads(receipt_path.read_text())
        without_time=lambda d:{k:v for k,v in d.items() if k!='verified_at_utc'}
        if without_time(previous)==without_time(receipt):
            receipt['verified_at_utc']=previous['verified_at_utc']
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
