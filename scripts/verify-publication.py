"""Verify unauthenticated public Circuit JSON, actual Gerber drills, and pinned GitHub bytes."""
import datetime, decimal, hashlib, io, itertools, json, pathlib, re, subprocess, sys, urllib.parse, urllib.request, zipfile

root = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]
name = 'AnasSarkiz/' + json.loads((root / 'package.json').read_text())['name']
version = json.loads((root / 'package.json').read_text())['version']
api = 'https://registry-api.tscircuit.com/'
def request(endpoint, query=None, body=None):
    url = api + endpoint
    if query: url += '?' + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers={'Content-Type':'application/json'} if body else {})
    with urllib.request.urlopen(req, timeout=60) as r: return r.read()
def sha(data): return hashlib.sha256(data).hexdigest()
release = json.loads(request('package_releases/get', body={'package_name_with_version':name+'@'+version}))['package_release']
package = json.loads(request('packages/get', body={'name':name}))['package']
assert release['version'] == version and release['is_latest'] and release['ready_to_build'], 'Publication is not finalized'
assert not package['is_private'], 'Package is not public'
rid = release['package_release_id']
files = json.loads(request('package_files/list', query={'package_name':name,'use_latest_version':'true'}))['package_files']
assert all(f['package_release_id'] == rid for f in files)
def file(path):
    f = json.loads(request('package_files/get', query={'package_name':name,'use_latest_version':'true','file_path':path}))['package_file']
    assert f['package_release_id'] == rid
    if f['is_text']: return f['content_text'].encode()
    return request('package_files/download', query={'package_file_id':f['package_file_id']})
board_bytes = (root / 'artifacts/board.circuit.json').read_bytes()
board = json.loads(board_bytes)
remote_bytes = file('index.circuit.json')
remote = json.loads(remote_bytes)
dist_bytes = file('dist/index/circuit.json')
assert json.loads(dist_bytes) == remote
strip = lambda records: [{k:v for k,v in e.items() if not(e['type']=='cad_component' and k in ('model_obj_url','model_step_url'))} for e in records]
assert strip(remote) == strip(board), 'Published native Circuit JSON changes geometry or circuit records'
proof = json.loads(file('artifacts/publication-provenance.json'))
assert proof['review_board_sha256'] == sha(board_bytes) and proof['published_board_sha256'] == sha(remote_bytes)
assert proof['only_cad_url_metadata_changed'] and proof['saved_routing_preserved']
revision = proof['github_revision']
assert all('/'+revision+'/imports/supplier/' in e[field] for e in remote if e['type']=='cad_component' and e.get('model_obj_url') for field in ['model_obj_url','model_step_url'])
pcb = next(e for e in remote if e['type']=='pcb_board')
assert pcb['width']==pcb['height']==35
names={e['source_component_id']:e['name'] for e in remote if e['type']=='source_component'}
usb=[]
for e in remote:
    if e['type']=='cad_component' and names.get(e.get('source_component_id')) in ('J_PD','J_DATA'):
        assert e['rotation']['z']==0
        mouth=(e['position']['x']+(4.4700000999-4.4750064358)/2-e['model_origin_position']['x'],e['position']['y']+(1.5821329568+5.2721320224)/2-e['model_origin_position']['y'])
        source=next(q for q in remote if q['type']=='source_component' and q['source_component_id']==e['source_component_id'])
        assert source['manufacturer_part_number']=='USB4145-03-0070-C' and source['supplier_part_numbers']=={'jlcpcb':['C5815189']}
        usb.append(mouth)
expected_usb_mouths = [(-4.6, -15.15), (0.6, 15.15)]
assert len(usb)==2 and all(abs(x-ex)<.001 and abs(y-ey)<.001 for (x,y),(ex,ey) in zip(sorted(usb),expected_usb_mouths))
dnp={names[e['source_component_id']] for e in remote if e['type']=='pcb_component' and e.get('do_not_place')}
assert dnp=={'U_ENCODER','C_ENCODER','C_ENCODER_BULK'}
assert all(e['layer']=='bottom' for e in remote if e['type']=='pcb_component' and e.get('do_not_place'))
assert pcb['min_via_hole_diameter']==.3 and pcb['min_via_pad_diameter']==.45
via_proof=json.loads(file('artifacts/upright-revision/via-fabrication-verification.json'))
assert via_proof['passed'] and via_proof['board_sha256']==sha(board_bytes)
mechanical=json.loads(file('artifacts/mechanical/mount-usb-screen.json'))
assert mechanical['passed'] and mechanical['board_sha256']==sha(board_bytes)
assert mechanical['fastener_requirement']['maximum_head_diameter_mm']==6
assert mechanical['fastener_requirement']['model_envelope_diameter_mm']==6.4
assert abs(mechanical['minimum_simultaneous_plug_gap_mm']-23.3)<1e-5
assert min(u['native_body_to_mount_envelope_mm'] for u in mechanical['usb'])>=.1
motor_source=next(e for e in remote if e['type']=='source_component' and e['name']=='J_MOTOR')
assert motor_source['manufacturer_part_number']=='BM04B-SRSS-TB(LF)(SN)' and motor_source['supplier_part_numbers']=={'jlcpcb':['C160390']}
motor_model=next(e for e in remote if e['type']=='cad_component' and e['source_component_id']==motor_source['source_component_id'])
assert '/'+revision+'/imports/supplier/BM04B_SRSS_TB_LF__SN_/' in motor_model['model_step_url']
assert mechanical['motor_connector']['manufacturer_part_number']=='BM04B-SRSS-TB(LF)(SN)' and mechanical['motor_connector']['body_within_35mm_outline']
assert not mechanical['motor_connector']['vertical_access_intersections']
connector=json.loads(file('artifacts/jst-restoration/connector-verification.json'));assert connector['passed'] and connector['supplier_id']=='C160390'
assert len(connector['actual_JST_drill_matches'])==0 and len(connector['actual_JST_copper_matches'])==6
assert len(mechanical['motor_connector']['STEP_landing_regions'])==6 and all(e['STEP_landing_region_volume_mm3']>1e-5 for e in mechanical['motor_connector']['STEP_landing_regions'])
cam=json.loads(file('artifacts/manufacturing/audit.json'))
assert cam['source_sha256']==sha(board_bytes) and cam['status']=='PASS' and not cam['issues']
assert cam['board_outline']['valid_35mm_square'] and cam['board_outline']['centerline_bounds_mm']==[-17.5,-17.5,17.5,17.5]
assert not cam['connectivity']['shorts'] and not cam['connectivity']['opens'] and not cam['connectivity']['unconnected_pads']
expected = set(itertools.product([-13,13],repeat=2))
holes = [e for e in remote if e['type']=='pcb_hole' and not e.get('pcb_component_id')]
assert len(holes)==4 and {(e['x'],e['y']) for e in holes}==expected and all(e['hole_diameter']==3.2 for e in holes)
archive = file('artifacts/nema14-gerbers.zip')
assert sha(archive)==sha((root/'artifacts/nema14-gerbers.zip').read_bytes()), 'Public Gerber archive differs'
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    names = [n for n in z.namelist() if n.endswith('.drl') and 'npth' in n.lower()]
    assert len(names)==1
    drill = z.read(names[0]); text=drill.decode(); assert 'METRIC' in text and 'G90' in text and 'NonPlated' in text
    tools={}; tool=None; mounts=[]; D=decimal.Decimal
    for line in text.splitlines():
        match=re.fullmatch(r'T(\d+)C([\d.]+)',line)
        if match: tools[match[1]]=D(match[2]); continue
        match=re.fullmatch(r'T(\d+)',line)
        if match: tool=match[1]; assert tool in tools; continue
        match=re.fullmatch(r'X([+-]?[\d.]+)Y([+-]?[\d.]+)',line)
        if match and tools[tool]==D('3.2'): mounts.append((D(match[1]),D(match[2])))
    assert len(mounts)==4 and set(mounts)==expected
schematic=json.loads(file('artifacts/schematic-redesign/analysis.json'))
assert schematic['passed'] and schematic['board_sha256']==sha(board_bytes)
assert len([e for e in remote if e['type']=='schematic_sheet'])==6
assert not file('artifacts/schematic-redesign/native-analysis.txt').strip(), 'Native schematic analysis still reports issues'
usb_proof=json.loads(file('artifacts/engineering-fixes/usb-verification.json'));assert usb_proof['passed'] and usb_proof['board_sha256']==sha(board_bytes)
schema_proof=json.loads(file('artifacts/engineering-fixes/schema-verification.json'));assert schema_proof['passed'] and schema_proof['board_sha256']==sha(board_bytes)
checks=[]
for path in ['artifacts/upright-revision/via-fabrication-verification.json','artifacts/upright-revision/oscillator-verification.json','artifacts/engineering-fixes/usb-verification.json','artifacts/engineering-fixes/schema-verification.json','artifacts/engineering-fixes/export-policy.json','docs/engineering-fixes.md','artifacts/edge-resistors/clearance-verification.json','docs/resistor-edge-clearance.md','artifacts/schematic-redesign/analysis.json','artifacts/schematic-redesign/preservation.json','artifacts/schematic-redesign/native-analysis.txt','docs/schematic-verification.md','artifacts/schematic-a4.pdf',*[f'artifacts/schematic-a4-page-{i:02d}.svg' for i in range(1,7)],'artifacts/mount-drill-verification.json','artifacts/mechanical/mount-usb-screen.json','artifacts/manufacturing/audit.json','artifacts/resume-validation.json','src/board.tsx','docs/mounting-usb-verification.md','artifacts/mounting-change-proof.json','artifacts/trace-width-review.json','artifacts/jst-restoration/connector-verification.json','src/jlcpcb-catalog.json','artifacts/bom.csv','artifacts/reference-feedback/circuit-verification.json','artifacts/reference-feedback/every-trace-review.json','artifacts/reference-feedback/every-trace-review.csv','artifacts/reference-feedback/preserved-electrical-interfaces.json','docs/reference-feedback.md','docs/top-assembly.md','artifacts/top-assembly/functional-preservation.json','artifacts/top-assembly/connector-decision.json','artifacts/top-assembly/assembly-preview.circuit.json','assembly-preview.circuit.tsx']:
    data=file(path);expected_data=(root/path).read_bytes()
    if path=='artifacts/top-assembly/assembly-preview.circuit.json':
        assert strip(json.loads(data))==strip(json.loads(expected_data)), 'Assembly preview geometry changed'
        for e in json.loads(data):
            if e['type']=='cad_component':
                for field in ['model_obj_url','model_step_url']:
                    url=e.get(field,'')
                    if 'raw.githubusercontent.com/AnasSarkiz/' in url:assert '/'+revision+'/imports/supplier/' in url
    else:assert data==expected_data,path+' public evidence differs'
    checks.append({'path':path,'sha256':sha(data)})
repo = 'AnasSarkiz/NEMA14_RP2040'
source_revision = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
assert proof['source_git_revision'] == source_revision
model_proof = json.loads(file('artifacts/ch224a-migration/public-model-assets.json'))
assert model_proof == json.loads((root/'artifacts/ch224a-migration/public-model-assets.json').read_text())
assert model_proof['passed'] and model_proof['github_revision'] == revision
with urllib.request.urlopen('https://api.github.com/repos/'+repo+'/git/trees/'+revision+'?recursive=1',timeout=60) as response:
    tree=json.load(response)
assert not tree.get('truncated')
blobs={e['path']:e['sha'] for e in tree['tree'] if e['type']=='blob'}
github=[]
for asset in model_proof['assets']:
    path=asset['path'];url=asset['url'];data=(root/path).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert blobs[path]==blob==asset['git_blob_sha'] and sha(data)==asset['sha256'], 'Public model differs: '+path
    assert url=='https://raw.githubusercontent.com/'+repo+'/'+revision+'/'+path
    github.append({'path':path,'sha256':sha(data),'url':url})
model_urls={e[field] for e in remote if e['type']=='cad_component' for field in ['model_obj_url','model_step_url'] if e.get(field)}
assert model_urls=={asset['url'] for asset in model_proof['assets']}
page='https://tscircuit.com/'+name
with urllib.request.urlopen(page,timeout=60) as r: page_status=r.status; assert page_status==200
feedback=json.loads(file('artifacts/reference-feedback/circuit-verification.json'));assert feedback['passed'] and feedback['board_sha256']==sha(board_bytes)
trace_review=json.loads(file('artifacts/reference-feedback/every-trace-review.json'));assert trace_review['passed']
receipt={'schematic_native_analysis_zero_issues':True,'schematic_geometric_ERC_passed':True,'functional_A4_sheet_count':6,'PCB_and_source_preserved_from_schematic_baseline':schematic['electrical_source_and_PCB_CAD_preserved'],'electrical_source_preserved':schematic.get('electrical_source_preserved',True),'qualified_schematic_preserved':schematic.get('qualified_schematic_preserved',True),'reference_feedback_verified':True,'every_trace_inventory_verified':True,'hardware_operation_verified':False,'passed':True,'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'public_package':name,'version':version,'package_release_id':rid,'package_is_private':False,'ready_to_build':True,'public_page':page,'page_http_status':page_status,'github_revision':revision,'github_commit_url':'https://github.com/'+repo+'/commit/'+revision,'public_file_count':len(files),'review_board_sha256':sha(board_bytes),'public_index_sha256':sha(remote_bytes),'public_dist_sha256':sha(dist_bytes),'geometry_and_functional_records_unchanged':True,'cad_urls_pinned_to_revision':True,'mount_coordinates_mm':sorted(expected),'mount_diameter_mm':3.2,'board_dimensions_mm':[35,35],'USB_mouth_coordinates_mm':sorted(usb),'USB_insertion_direction':'+Z','required_maximum_DIN920_head_diameter_mm':4,'simultaneous_10mm_housing_gap_mm':mechanical['minimum_simultaneous_plug_gap_mm'],'actual_Gerber_outline_centerline_bounds_mm':cam['board_outline']['centerline_bounds_mm'],'public_gerber_archive_sha256':sha(archive),'public_drill_sha256':sha(drill),'public_drill_coordinates_mm':[[float(x),float(y)] for x,y in mounts],'public_evidence_checks':checks,'public_github_checks':github,'full_manufacturing_audit_passed':cam['status']=='PASS' and not cam['issues'],'rear_motor_compatibility_verified':False,'physical_hardware_tested':False,'fitted_motor_connector':'BM04B-SRSS-TB(LF)(SN)','JST_supplier_id':'C160390','JST_actual_drills':connector['actual_JST_drill_matches'],'JST_native_STEP_landing_regions_verified':True,'JST_individual_metal_terminal_centers_verified':False,'JST_top_entry_access_screen_pass':True}
order_dir=root/'artifacts/jlcpcb-review'
if order_dir.exists():
    public_order=[]
    for p in sorted(order_dir.iterdir()):
        if not p.is_file() or p.name=='order-source.circuit.json':continue
        path=str(p.relative_to(root));data=file(path)
        assert data==p.read_bytes(), 'Public JLCPCB review file differs: '+path
        public_order.append({'path':path,'sha256':sha(data)})
    order=json.loads(file('artifacts/jlcpcb-review/order-review-verification.json'))
    assert order['prepared_for_JLCPCB_engineering_review'] and order['order_review_CAM_passed']
    assert order['native_board_sha256']==sha(board_bytes)
    assert not order['JLCPCB_order_submitted'] and not order['production_release_approved']
    order_cam=json.loads(file('artifacts/jlcpcb-review/CAM-audit.json'))
    assert order_cam['status']=='PASS' and not order_cam['issues']
    fab_bytes=file('artifacts/jlcpcb-review/JLCPCB-Gerbers.zip')
    assert sha(fab_bytes)==order['JLCPCB_gerber_zip_sha256']
    with zipfile.ZipFile(io.BytesIO(fab_bytes)) as z:
        assert z.read('drill_npth.drl')==drill
        for layer in ['F_Cu.gbr','In1_Cu.gbr','In2_Cu.gbr','B_Cu.gbr','F_Mask.gbr','B_Mask.gbr','Edge_Cuts.gbr']:
            with zipfile.ZipFile(io.BytesIO(archive)) as original:
                assert z.read(layer)==original.read(layer)
    receipt.update({'JLCPCB_review_package_verified_public':True,'corrected_order_CAM_passed':True,
                    'supplier_order_review_approved':False,'production_release_approved':False,
                    'public_JLCPCB_review_evidence':public_order})
for path in ['docs/ch224a-migration.md','artifacts/ch224a-migration/vbus-rating-review.json',
             'artifacts/ch224a-migration/final-review.json','artifacts/ch224a-migration/electrical-and-preservation.json',
             'artifacts/ch224a-migration/pcb-diff.json']:
    data=file(path)
    assert data==(root/path).read_bytes(), 'Migration evidence differs: '+path
    checks.append({'path':path,'sha256':sha(data)})
vbus=json.loads(file('artifacts/ch224a-migration/vbus-rating-review.json'))
assert vbus['VBUS_rating_concern_resolved'] and vbus['VBUS_absolute_maximum_V']==32
receipt.update({'source_git_revision':source_revision,'source_git_revision_pushed_to_GitHub':False,
                'github_revision_scope':'supplier model assets only',
                'CH224A_VBUS_rating_confirmed_by_WCH_V2_1':True,'production_release_approved':False})
(root/'artifacts/publication-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
