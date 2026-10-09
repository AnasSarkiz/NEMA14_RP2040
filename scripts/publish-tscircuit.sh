#!/usr/bin/env bash
# Publish saved copper and pin supplier CAD URLs without modifying review inputs.
set -euo pipefail
project_root=$(cd "$(dirname "$0")/.." && pwd)
package_stage=$(mktemp -d /tmp/nema14-supplier-package.XXXXXX)
trap 'rm -rf "$package_stage"' EXIT
export PATH="$project_root/node_modules/.bin:$PATH"
python3 - "$project_root" "$package_stage" <<'PYSTAGE'
import hashlib,json,pathlib,re,shutil,subprocess,sys
root,stage=map(pathlib.Path,sys.argv[1:])
revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
for d in ['src','docs','scripts']:shutil.copytree(root/d,stage/d)
for f in ['index.circuit.tsx','README.md','package.json','package-lock.json','tsconfig.json','tscircuit.config.json']:shutil.copy2(root/f,stage/f)
for f in (root/'imports/supplier').rglob('*.tsx'):
 target=stage/f.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
(stage/'artifacts').mkdir()
for f in (root/'artifacts').glob('schematic-a4-page-*.svg'):shutil.copy2(f,stage/'artifacts'/f.name)
shutil.copytree(root/'artifacts/validation',stage/'artifacts/validation')
for f in ['bom.csv','source-bom.csv','pick_and_place.csv','nema14-gerbers.zip','drc-report.json','physical-connectivity.json','trace-width-review.json','ground-planes.json','verification.json','presentation-verification.json','jlcpcb-import-report.json','pcb-top.png','pcb-bottom.png','pcb-inner1.png','pcb-inner2.png','schematic-a4.pdf','schematic-a4.png','schematic.svg']:
 if (root/'artifacts'/f).exists():shutil.copy2(root/'artifacts'/f,stage/'artifacts'/f)
shutil.copy2(root/'artifacts/schematic-a4-page-01.svg',stage/'artifacts/schematic.svg')
board_path=root/'artifacts/board.circuit.json';original=json.loads(board_path.read_text())
assert json.loads((root/'index.circuit.json').read_text())==original
j=json.loads(board_path.read_text())
pattern=re.compile(r'(https://raw\.githubusercontent\.com/AnasSarkiz/(?:NEMA17_Controller|NEMA14_RP2040)/)main(/imports/supplier/)')
pin=lambda s:pattern.sub(lambda m:m[1]+revision+m[2],s)
for f in (stage/'imports/supplier').rglob('*.tsx'):f.write_text(pin(f.read_text()))
for e in j:
 if e['type']=='cad_component':
  for field in ['model_obj_url','model_step_url']:
   if isinstance(e.get(field),str):e[field]=pin(e[field])
strip_urls=lambda records:[{k:v for k,v in e.items() if not(e['type']=='cad_component' and k in ['model_obj_url','model_step_url'])} for e in records]
assert strip_urls(j)==strip_urls(original),'Publication changed reviewed geometry or circuit records'
assert all('/'+revision+'/imports/supplier/' in e[field] for e in j if e['type']=='cad_component' and e.get('model_obj_url') for field in ['model_obj_url','model_step_url'])
for f in ['index.circuit.json','artifacts/board.circuit.json']:(stage/f).write_text(json.dumps(j,separators=(',',':'))+'\n')
proof={'github_revision':revision,'review_board_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest(),'published_board_sha256':hashlib.sha256((stage/'index.circuit.json').read_bytes()).hexdigest(),'only_cad_url_metadata_changed':True,'saved_routing_preserved':True,'pinned_cad_components':sum(e['type']=='cad_component' and bool(e.get('model_obj_url')) for e in j)}
(stage/'artifacts/publication-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Prepared source package:',json.dumps(proof))
PYSTAGE
cd "$package_stage"
XDG_CONFIG_HOME=/workspace/.config tsci build index.circuit.json
python3 - "$package_stage" <<'PYDIST'
import json,pathlib,sys
stage=pathlib.Path(sys.argv[1]);saved=json.loads((stage/'index.circuit.json').read_text());built=json.loads((stage/'dist/index/circuit.json').read_text())
assert built==saved,'Native CLI dist build differs from saved routing'
print('Including verified native dist/index/circuit.json')
PYDIST
XDG_CONFIG_HOME=/workspace/.config tsci push index.circuit.tsx --include-dist --compress
python3 - "$package_stage" <<'PYVERSION'
import json,pathlib,sys
p=pathlib.Path(sys.argv[1]);print('Published registry version:',json.loads((p/'package.json').read_text())['version'])
PYVERSION
