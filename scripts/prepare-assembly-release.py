"""Stage an assembly-only patch against the exact published 1.12.0 PCB.

This gate verifies assembly evidence and byte-exact baseline preservation.
It does not rerun or certify the inherited electrical/manufacturing qualification.
The optional --publish flag uploads the validated stage using native registry APIs.
"""
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, tempfile
import urllib.parse, urllib.request

root = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--publish', action='store_true')
args = parser.parse_args()
meta = json.loads((root/'package.json').read_text())
name = 'AnasSarkiz/'+meta['name']
assert meta['version'] == '1.12.1'
api = 'https://registry-api.tscircuit.com/'
def get(endpoint, **query):
    request = urllib.request.Request(api+endpoint, data=json.dumps(query).encode(), headers={'Content-Type':'application/json'}) if endpoint=='package_releases/get' else api+endpoint+'?'+urllib.parse.urlencode(query)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
baseline = get('package_releases/get', package_name_with_version=name+'@1.12.0')['package_release']
baseline_id = baseline['package_release_id']
remote_board = get('package_files/get', package_release_id=baseline_id, file_path='index.circuit.json')['package_file']['content_text'].encode()
board = (root/'index.circuit.json').read_bytes()
assert board == remote_board == (root/'artifacts/board.circuit.json').read_bytes(), 'Published PCB changed'
assembly_path = root/'assembly.circuit.json'
assembly_sha = sha(assembly_path)
assembly = json.loads(assembly_path.read_text())
native = json.loads(board)
assert assembly[:len(native)] == native
checks = ['assembly-fit-verification.json', 'harness-connection-verification.json', 'assembly-schema-verification.json']
for filename in checks:
    report = json.loads((root/'artifacts/top-assembly'/filename).read_text())
    assert report['passed'] and report['assembly_sha256'] == assembly_sha, filename+' is stale'
mesh = json.loads((root/'artifacts/top-assembly/harness-mesh-verification.json').read_text())
assert mesh['passed'] and mesh['glb_sha256'] == sha(root/'artifacts/top-assembly/assembled.glb')
render = json.loads((root/'artifacts/top-assembly/assembly-render-verification.json').read_text())
assert render['passed'] and all(sha(root/path) == digest for path,digest in render['files'].items())
connection = json.loads((root/'artifacts/top-assembly/harness-connection-verification.json').read_text())
assert connection['motor_wire_outlet_faces_JST_board_edge']
env = dict(os.environ, PATH=str(root/'node_modules/.bin')+':'+os.environ['PATH'], XDG_CONFIG_HOME='/workspace/.config')
subprocess.run(['npm', 'run', 'typecheck'], cwd=root, env=env, check=True)

stage = pathlib.Path(tempfile.mkdtemp(prefix=meta['name']+'-assembly-1.12.1-', dir='/tmp'))
rows = get('package_files/list', package_release_id=baseline_id)['package_files']
paths = {row['file_path'] for row in rows if not row['file_path'].startswith('dist/')}
# Preserve all prior source/artifacts and add the new assembly sources/evidence.
for directory in ['src', 'scripts', 'docs', 'references', 'artifacts/top-assembly']:
    paths.update(p.relative_to(root).as_posix() for p in (root/directory).rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc', '.glb', '.js', '.html'])
paths.add('artifacts/board.circuit.json')
paths.discard('artifacts/top-assembly/assembly-publication-verification.json')
for relative in sorted(paths):
    path = pathlib.PurePosixPath(relative)
    assert not path.is_absolute() and '..' not in path.parts
    source = root/relative
    assert source.is_file(), 'Missing published source: '+relative
    target = stage/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
proof = {
    'passed': True, 'scope': 'assembly-only preview patch; inherited PCB qualification not recertified',
    'baseline_package': name+'@1.12.0', 'baseline_release_id': baseline_id,
    'board_sha256': hashlib.sha256(board).hexdigest(), 'assembly_sha256': assembly_sha,
    'published_board_bytes_preserved': True, 'motor_wire_outlet_faces_JST_board_edge': True,
    'mechanical_checks': checks+['harness-mesh-verification.json', 'assembly-render-verification.json'],
    'physical_assembly_tested': False,
}
(stage/'artifacts/top-assembly/assembly-release-readiness.json').write_text(json.dumps(proof, indent=2)+'\n')
(root/'artifacts/top-assembly/assembly-release-readiness.json').write_text(json.dumps(proof, indent=2)+'\n')
os.symlink(root/'node_modules', stage/'node_modules', target_is_directory=True)
for entry in ['index.circuit.json', 'assembly.circuit.json']:
    subprocess.run(['tsci', 'build', entry], cwd=stage, env=env, check=True)
    assert json.loads((stage/'dist'/entry.removesuffix('.circuit.json')/'circuit.json').read_text()) == json.loads((root/entry).read_text())
print('Validated assembly-only release stage:', stage, flush=True)
(root/'artifacts/top-assembly/assembly-release-stage.json').write_text(json.dumps({'stage':str(stage)}, indent=2)+'\n')
if args.publish:
    # Normal registry release creation/upload, with no PCB source substitutions.
    subprocess.run(['python3', str(root/'scripts/ensure-registry-release.py'), str(stage)], check=True)
    # Recovery uploader traverses files; remove the local dependency link first.
    (stage/'node_modules').unlink()
    subprocess.run(['python3', str(root/'scripts/recover-publication.py'), str(stage)], check=True)
