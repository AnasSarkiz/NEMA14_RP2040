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
checks=[]
for path in ['artifacts/mount-drill-verification.json','artifacts/mechanical/mount-usb-screen.json','artifacts/manufacturing/audit.json','artifacts/resume-validation.json','src/board.tsx','docs/mounting-usb-verification.md']:
    data=file(path); assert data==(root/path).read_bytes(), path+' public evidence differs'
    checks.append({'path':path,'sha256':sha(data)})
git_remote = subprocess.check_output(['git','-C',str(root),'remote','get-url','origin'],text=True).strip()
repo = git_remote.removeprefix('https://github.com/').removesuffix('.git')
github=[]
for path in ['artifacts/board.circuit.json','index.circuit.json','artifacts/nema14-gerbers.zip','imports/supplier/TYPE_C_31_M_12/TYPE_C_31_M_12.step']:
    if not (root/path).exists():
        candidates=list((root/'imports/supplier/TYPE_C_31_M_12').glob('*.step')); assert len(candidates)==1
        path=str(candidates[0].relative_to(root))
    url='https://raw.githubusercontent.com/'+repo+'/'+revision+'/'+path
    with urllib.request.urlopen(url,timeout=60) as r: data=r.read()
    assert sha(data)==sha((root/path).read_bytes()), 'GitHub bytes differ: '+path
    github.append({'path':path,'sha256':sha(data),'url':url})
page='https://tscircuit.com/'+name
with urllib.request.urlopen(page,timeout=60) as r: page_status=r.status; assert page_status==200
receipt={'passed':True,'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'public_package':name,'version':version,'package_release_id':rid,'package_is_private':False,'ready_to_build':True,'public_page':page,'page_http_status':page_status,'github_revision':revision,'github_commit_url':'https://github.com/'+repo+'/commit/'+revision,'public_file_count':len(files),'review_board_sha256':sha(board_bytes),'public_index_sha256':sha(remote_bytes),'public_dist_sha256':sha(dist_bytes),'geometry_and_functional_records_unchanged':True,'cad_urls_pinned_to_revision':True,'mount_coordinates_mm':sorted(expected),'mount_diameter_mm':3.2,'public_gerber_archive_sha256':sha(archive),'public_drill_sha256':sha(drill),'public_drill_coordinates_mm':[[float(x),float(y)] for x,y in mounts],'public_evidence_checks':checks,'public_github_checks':github,'full_manufacturing_audit_passed':False,'rear_motor_compatibility_verified':False,'physical_hardware_tested':False}
(root/'artifacts/publication-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
