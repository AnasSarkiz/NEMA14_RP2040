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
for d in ['src','docs','scripts']:shutil.copytree(root/d,stage/d,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for f in ['index.circuit.tsx','README.md','package.json','package-lock.json','tsconfig.json','tscircuit.config.json']:shutil.copy2(root/f,stage/f)
for f in (root/'imports/supplier').rglob('*.tsx'):
 target=stage/f.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
(stage/'artifacts').mkdir()
for f in (root/'artifacts').glob('schematic-a4-page-*.svg'):shutil.copy2(f,stage/'artifacts'/f.name)
for f in ['bom.csv','source-bom.csv','pick_and_place.csv','drc-report.json','physical-connectivity.json','jlcpcb-import-report.json']:
 if (root/'artifacts'/f).exists():shutil.copy2(root/'artifacts'/f,stage/'artifacts'/f)
shutil.copy2(root/'artifacts/schematic-a4-page-01.svg',stage/'artifacts/schematic.svg')
board_path=root/'artifacts/board.circuit.json';original=json.loads(board_path.read_text())
assert json.loads((root/'index.circuit.json').read_text())==original
j=json.loads(board_path.read_text())
catalog=json.loads((root/'src/jlcpcb-catalog.json').read_text())
source={e['source_component_id']:e for e in j if e['type']=='source_component'}
replacements={}
for e in j:
 if e['type']!='cad_component' or not e.get('model_obj_url'):continue
 ref=source[e['source_component_id']]['name'];part=catalog['parts'][catalog['components'][ref]]
 for ext,field in [('obj','model_obj_url'),('step','model_step_url')]:
  asset=next(f for f in part['modelFiles']if f.endswith('.'+ext));assert (root/asset).is_file()
  assert hashlib.sha256((root/asset).read_bytes()).hexdigest()==part['sha256'][ext]
  url='https://raw.githubusercontent.com/AnasSarkiz/NEMA14_RP2040/'+revision+'/'+asset
  replacements[e[field]]=url;replacements[e[field].split('&cachebust_origin=')[0]]=url;e[field]=url
for folder in [stage/'imports/supplier',stage/'src']:
 for f in folder.rglob('*.tsx'):
  text=f.read_text()
  for before,after in sorted(replacements.items(),key=lambda kv:-len(kv[0])):text=text.replace(before,after)
  f.write_text(text)
strip_urls=lambda records:[{k:v for k,v in e.items() if not(e['type']=='cad_component' and k in ['model_obj_url','model_step_url'])} for e in records]
assert strip_urls(j)==strip_urls(original),'Publication changed reviewed geometry or circuit records'
assert all('/'+revision+'/' in e[field] for e in j if e['type']=='cad_component' and e.get('model_obj_url') for field in ['model_obj_url','model_step_url'])
(stage/'index.circuit.json').write_text(json.dumps(j,separators=(',',':'))+'\n')
config=stage/'tscircuit.config.json';c=json.loads(config.read_text());c['includeBoardFiles']=['index.circuit.json'];config.write_text(json.dumps(c,indent=2)+'\n')
proof={'github_revision':revision,'review_board_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest(),'published_board_sha256':hashlib.sha256((stage/'index.circuit.json').read_bytes()).hexdigest(),'only_cad_url_metadata_changed':True,'saved_routing_preserved':True,'pinned_cad_components':sum(e['type']=='cad_component' and bool(e.get('model_obj_url')) for e in j)}
(root/'artifacts/validation/service-publication-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
(stage/'artifacts/publication-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Prepared source package:',json.dumps(proof))
PYSTAGE
cd "$package_stage"
XDG_CONFIG_HOME=/workspace/.config tsci build index.circuit.json
python3 - "$package_stage" <<'PYDIST'
import json,pathlib,sys
stage=pathlib.Path(sys.argv[1]);saved=json.loads((stage/'index.circuit.json').read_text());built=json.loads((stage/'dist/index/circuit.json').read_text())
assert built==saved,'Native CLI dist build differs from saved routing'
(stage/'dist/index/circuit.json').write_text(json.dumps(built,separators=(',',':'))+'\n')
print('Including verified compact native dist/index/circuit.json')
PYDIST
XDG_CONFIG_HOME=/workspace/.config tsci push index.circuit.tsx --include-dist --compress
python3 - "$package_stage" <<'PYVERSION'
import json,pathlib,sys
p=pathlib.Path(sys.argv[1]);print('Published registry version:',json.loads((p/'package.json').read_text())['version'])
PYVERSION
