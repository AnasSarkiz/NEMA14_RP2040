#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd "$(dirname "$0")/.." && pwd)
package_stage=$(mktemp -d /tmp/nema14-supplier-package.XXXXXX)
trap 'rm -rf "$package_stage"' EXIT
python3 - "$project_root" "$package_stage" <<'PY'
import json,pathlib,shutil,sys
root,stage=map(pathlib.Path,sys.argv[1:])
for d in ['src','docs']:shutil.copytree(root/d,stage/d)
for f in ['README.md','package.json','package-lock.json','tsconfig.json','tscircuit.config.json']:shutil.copy2(root/f,stage/f)
(stage/'artifacts').mkdir()
shutil.copytree(root/'artifacts/validation',stage/'artifacts/validation')
for f in ['bom.csv','drc-report.json','physical-connectivity.json','verification.json','presentation-verification.json','jlcpcb-import-report.json','pcb-top.png','pcb-bottom.png','pcb-inner1.png','pcb-inner2.png','schematic-a4.pdf','schematic-a4.png','schematic.svg']:
 if (root/'artifacts'/f).exists():shutil.copy2(root/'artifacts'/f,stage/'artifacts'/f)
j=json.loads((root/'artifacts/board.circuit.json').read_text())
(stage/'artifacts/board.circuit.json').write_text(json.dumps(j,separators=(',',':'))+'\n')
assert json.loads((stage/'artifacts/board.circuit.json').read_text())==j
print('Prepared compact source package with unchanged saved copper')
PY
cd "$package_stage"
XDG_CONFIG_HOME=/workspace/.config tsci push src/board.tsx --compress
# The CLI increments a conflicting release version; keep the repo metadata aligned.
python3 - "$project_root" "$package_stage" <<'PY'
import json,pathlib,sys
root,stage=map(pathlib.Path,sys.argv[1:]);p=root/'package.json';j=json.loads(p.read_text());j['version']=json.loads((stage/'package.json').read_text())['version'];p.write_text(json.dumps(j,indent=2)+'\n')
p=root/'package-lock.json';j=json.loads(p.read_text());j['version']=json.loads((root/'package.json').read_text())['version'];j['packages']['']['version']=j['version'];p.write_text(json.dumps(j,indent=2)+'\n')
PY
