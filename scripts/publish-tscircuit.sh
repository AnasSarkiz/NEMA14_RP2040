#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd "$(dirname "$0")/.." && pwd)
package_stage=$(mktemp -d /tmp/nema14-supplier-package.XXXXXX)
trap 'rm -rf "$package_stage"' EXIT
python3 - "$project_root" "$package_stage" <<'PY'
import json,pathlib,shutil,sys
root,stage=map(pathlib.Path,sys.argv[1:])
for d in ['src','docs','scripts']:shutil.copytree(root/d,stage/d)
for f in ['index.circuit.tsx','README.md','package.json','package-lock.json','tsconfig.json','tscircuit.config.json']:shutil.copy2(root/f,stage/f)
(stage/'artifacts').mkdir()
for f in (root/'imports/supplier').rglob('*.tsx'):
 target=stage/f.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
for f in (root/'artifacts').glob('schematic-a4-page-*.svg'):shutil.copy2(f,stage/'artifacts'/f.name)
shutil.copytree(root/'artifacts/validation',stage/'artifacts/validation')
for f in ['bom.csv','drc-report.json','physical-connectivity.json','verification.json','presentation-verification.json','jlcpcb-import-report.json','pcb-top.png','pcb-bottom.png','pcb-inner1.png','pcb-inner2.png','schematic-a4.pdf','schematic-a4.png','schematic.svg']:
 if (root/'artifacts'/f).exists():shutil.copy2(root/'artifacts'/f,stage/'artifacts'/f)
# Source compilation can write an overview SVG; publish the checked A4 first sheet.
shutil.copy2(root/'artifacts/schematic-a4-page-01.svg',stage/'artifacts/schematic.svg')
j=json.loads((root/'artifacts/board.circuit.json').read_text())
(stage/'artifacts/board.circuit.json').write_text(json.dumps(j,separators=(',',':'))+'\n')
(root/'index.circuit.json').write_text(json.dumps(j,separators=(',',':'))+'\n')
shutil.copy2(root/'index.circuit.json',stage/'index.circuit.json')
assert json.loads((stage/'index.circuit.json').read_text())==j
assert json.loads((stage/'artifacts/board.circuit.json').read_text())==j
print('Prepared compact source package with unchanged saved copper')
PY
cd "$package_stage"
XDG_CONFIG_HOME=/workspace/.config tsci push index.circuit.tsx --compress
# The CLI increments a conflicting release version; keep the repo metadata aligned.
python3 - "$project_root" "$package_stage" <<'PY'
import json,pathlib,sys
root,stage=map(pathlib.Path,sys.argv[1:]);p=root/'package.json';j=json.loads(p.read_text());j['version']=json.loads((stage/'package.json').read_text())['version'];p.write_text(json.dumps(j,indent=2)+'\n')
p=root/'package-lock.json';j=json.loads(p.read_text());j['version']=json.loads((root/'package.json').read_text())['version'];j['packages']['']['version']=j['version'];p.write_text(json.dumps(j,indent=2)+'\n')
PY
