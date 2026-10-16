"""Verify immutable public supplier model blobs before publishing registry JSON.

Source commits may exist only locally. Retain the published model revision after
checking every referenced asset against GitHub's immutable blob hashes.
"""
import hashlib, json, pathlib, urllib.parse, urllib.request

root = pathlib.Path(__file__).resolve().parents[1]
board = json.loads((root/'index.circuit.json').read_text())
urls = sorted({e[field] for e in board if e['type'] == 'cad_component'
               for field in ['model_obj_url', 'model_step_url']
               if isinstance(e.get(field), str)})
revisions = {u.split('/')[5] for u in urls
             if u.startswith('https://raw.githubusercontent.com/AnasSarkiz/NEMA14_RP2040/')}
assert len(revisions) == 1, 'Expected one immutable, previously published model revision'
revision = revisions.pop()
assert len(revision) == 40 and all(c in '0123456789abcdef' for c in revision)
base = 'https://raw.githubusercontent.com/AnasSarkiz/NEMA14_RP2040/'+revision+'/'
with urllib.request.urlopen('https://api.github.com/repos/AnasSarkiz/NEMA14_RP2040/git/trees/'+revision+'?recursive=1', timeout=60) as response:
    tree = json.load(response)
assert not tree.get('truncated')
files = {e['path']: e for e in tree['tree'] if e['type'] == 'blob'}
assets = []
for url in urls:
    assert '/imports/supplier/' in url
    relative = 'imports/supplier/'+url.split('/imports/supplier/', 1)[1]
    local = root/relative
    if url.startswith('https://'):
        assert url == base+relative, 'Unexpected model host or revision'
    else:
        assert pathlib.Path(url) == local, 'Unexpected local model path'
    data = local.read_bytes()
    blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert files[relative]['sha'] == blob, 'Public model differs: '+relative
    assets.append({'path': relative, 'url': base+relative,
                   'sha256': hashlib.sha256(data).hexdigest(), 'git_blob_sha': blob})
report = {'passed': True, 'github_revision': revision,
          'scope': 'immutable supplier model assets; no source commit publication claimed',
          'assets': assets}
(root/'artifacts/ch224a-migration/public-model-assets.json').write_text(json.dumps(report, indent=2)+'\n')
print('Verified public supplier models:', len(assets), 'assets at', revision)
