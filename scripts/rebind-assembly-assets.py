"""Reuse assembly meshes only when the exact reviewed mounted STEP is unchanged."""
from pathlib import Path
import json,hashlib,zipfile
r=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=r/'assets/assembly/asset-manifest.json';a=json.loads(p.read_text());m=json.loads((r/'artifacts/mechanical/mechanical-review.json').read_text());archive=r/'artifacts/mechanical/mounted-front-carrier.step.zip'
assert m['board_sha256']==sha(r/'artifacts/board.circuit.json')
b=next(e for e in m['step_assembly_archives']if e['archive']==archive.name)
assert sha(archive)==b['archive_sha256']==a['mounted_step_archive_sha256'],'Changed STEP: regenerate assembly assets'
with zipfile.ZipFile(archive)as z:assert hashlib.sha256(z.read(b['member'])).hexdigest()==b['uncompressed_step_sha256']==a['mounted_step_member_sha256']
assert sha(r/'assets/assembly/models.json')==a['portable_models_json_sha256']
for model in a['models'].values():assert sha(r/model['path'])==model['sha256']
a['exact_step_rebind_proof']={'previous_source_board_sha256':a['source_board_sha256'],'unchanged_mounted_step_sha256':a['mounted_step_member_sha256'],'all_mesh_hashes_verified':True,'scope':'Metadata/copper revisions only; exact native mounted STEP geometry and every exported mesh unchanged'}
a['source_board_sha256']=sha(r/'artifacts/board.circuit.json');a['mechanical_review_sha256']=sha(r/'artifacts/mechanical/mechanical-review.json');p.write_text(json.dumps(a,indent=2)+'\n');print('Rebound verified unchanged mounted STEP and all eight mesh groups')
