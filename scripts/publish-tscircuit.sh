#!/usr/bin/env bash
# Publish saved copper and pin supplier CAD URLs without modifying review inputs.
set -euo pipefail
project_root=$(cd "$(dirname "$0")/.." && pwd)
python3 "$project_root/scripts/verify-publish-readiness.py" --prototype
python3 "$project_root/scripts/verify-jlcpcb-review.py"
package_stage=$(mktemp -d /tmp/nema14-supplier-package.XXXXXX)
trap 'status=$?; if [ "$status" -eq 0 ]; then rm -rf "$package_stage"; else echo "Publication stage retained for recovery: $package_stage" >&2; fi' EXIT
export PATH="$project_root/node_modules/.bin:$PATH"
python3 - "$project_root" "$package_stage" <<'PYSTAGE'
import hashlib,json,pathlib,re,shutil,subprocess,sys
root,stage=map(pathlib.Path,sys.argv[1:])
revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
for d in ['src','docs','scripts','references','tests']:
 if (root/d).is_dir():shutil.copytree(root/d,stage/d,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pdf'))
for f in ['index.circuit.tsx','assembly.circuit.json','assembly-preview.circuit.tsx','README.md','package.json','package-lock.json','tsconfig.json','tscircuit.config.json']:shutil.copy2(root/f,stage/f)
for f in (root/'imports/supplier').rglob('*.tsx'):
 target=stage/f.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
# Preserve native model files imported by newly cloned supplier TSX modules.
for f in (stage/'imports/supplier').rglob('*.tsx'):
 for asset in re.findall(r'from\s+[\"\'](\./[^\"\']+\.(?:obj|step))[\"\']',f.read_text()):
  relative=(f.parent/asset).relative_to(stage);source=root/relative
  assert source.is_file(),relative
  shutil.copy2(source,stage/relative)

(stage/'artifacts').mkdir()
for f in (root/'artifacts').glob('schematic-a4-page-*.svg'):shutil.copy2(f,stage/'artifacts'/f.name)
for f in ['schematic-a4.pdf','bom.csv','source-bom.csv','pick_and_place.csv','drc-report.json','physical-connectivity.json','jlcpcb-import-report.json']:
 if (root/'artifacts'/f).exists():shutil.copy2(root/'artifacts'/f,stage/'artifacts'/f)
shutil.copy2(root/'artifacts/schematic-a4-page-01.svg',stage/'artifacts/schematic.svg')
for name in ['mounting-change-proof.json','mount-drill-verification.json','check-output.txt','native-check.txt','shorts-output.txt','resume-validation.json','nema14-gerbers.zip','same-side-routing-proof.json','same-side-copper-repairs.json','same-side-pruned-stubs.json','same-side-trimmed-stubs.json','same-side-copper-cleanup.json','same-side-local-ripup.json','same-side-power-width-repair.json','trace-width-review.json','presentation-verification.json']:
 if (root/'artifacts'/name).exists():shutil.copy2(root/'artifacts'/name,stage/'artifacts'/name)
for relative in ['mechanical/mount-usb-screen.json','manufacturing/audit.json','mechanical/opposite-edge-fit.svg','mechanical/opposite-edge-fit.png']:
 source=root/'artifacts'/relative;target=stage/'artifacts'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)

upright=stage/'artifacts/upright-revision';upright.mkdir()
for name in ['via-fabrication-verification.json','oscillator-verification.json','native-circle-checker.json','circle-checker-regression.json','thermal-restoration.json']:
 shutil.copy2(root/'artifacts/upright-revision'/name,upright/name)

engineering=stage/'artifacts/engineering-fixes';engineering.mkdir()
for name in ['usb-verification.json','schema-verification.json','export-policy.json','usb-routing-plan.json','native-json-compatibility.json','final-engineering-verification.json']:
 source=root/'artifacts/engineering-fixes'/name
 if source.exists():shutil.copy2(source,engineering/name)
shutil.copytree(root/'artifacts/jlcpcb-review',stage/'artifacts/jlcpcb-review',ignore=shutil.ignore_patterns('cam','order-source.circuit.json'))
shutil.copytree(root/'artifacts/opposite-edge',stage/'artifacts/opposite-edge',ignore=shutil.ignore_patterns('baseline*','*.txt','*.npy','mcu-routing-window.png','rejected-phase-*.json'))
shutil.copytree(root/'artifacts/edge-resistors',stage/'artifacts/edge-resistors')
shutil.copytree(root/'artifacts/schematic-redesign',stage/'artifacts/schematic-redesign',ignore=shutil.ignore_patterns('baseline*.json'))
shutil.copytree(root/'artifacts/validation-resume',stage/'artifacts/validation-resume')
shutil.copytree(root/'artifacts/jst-restoration',stage/'artifacts/jst-restoration')
shutil.copytree(root/'artifacts/reference-feedback',stage/'artifacts/reference-feedback')
top=stage/'artifacts/top-assembly';top.mkdir()
for name in ['functional-preservation.json','connector-decision.json','placement-plan.json','copper-transfer.json','assembly-preview.circuit.json','assembly-build-verification.json','assembly-fit-verification.json','assembly-schema-verification.json','assembly-render-verification.json','model-downloads.json','assembly-complete.png','assembly-top.png']:
 shutil.copy2(root/'artifacts/top-assembly'/name,top/name)
board_path=root/'artifacts/board.circuit.json';original=json.loads(board_path.read_text())
assert json.loads((root/'index.circuit.json').read_text())==original
j=json.loads(board_path.read_text())
pattern=re.compile(r'(https://raw\.githubusercontent\.com/AnasSarkiz/(?:NEMA17_Controller|NEMA14_RP2040)/)main(/imports/supplier/)')
def pin(s):
 s=pattern.sub(lambda m:'https://raw.githubusercontent.com/AnasSarkiz/NEMA14_RP2040/'+revision+m[2],s)
 return s.replace(str(root)+'/imports/supplier/','https://raw.githubusercontent.com/AnasSarkiz/NEMA14_RP2040/'+revision+'/imports/supplier/')
for f in (stage/'imports/supplier').rglob('*.tsx'):f.write_text(pin(f.read_text()))
preview_path=stage/'artifacts/top-assembly/assembly-preview.circuit.json'
preview_path.write_text(pin(preview_path.read_text()))
assembly_path=stage/'assembly.circuit.json'
assembly_path.write_text(json.dumps(json.loads(pin(assembly_path.read_text())),separators=(',',':'))+'\n')
assert json.loads(assembly_path.read_text())==json.loads(preview_path.read_text())
assert json.loads((root/'artifacts/top-assembly/assembly-fit-verification.json').read_text())['passed']

for e in j:
 if e['type']=='cad_component':
  for field in ['model_obj_url','model_step_url']:
   if isinstance(e.get(field),str):e[field]=pin(e[field])
strip_urls=lambda records:[{k:v for k,v in e.items() if not(e['type']=='cad_component' and k in ['model_obj_url','model_step_url'])} for e in records]
assert strip_urls(j)==strip_urls(original),'Publication changed reviewed geometry or circuit records'
assert all('/'+revision+'/imports/supplier/' in e[field] for e in j if e['type']=='cad_component' and e.get('model_obj_url') for field in ['model_obj_url','model_step_url'])
(stage/'index.circuit.json').write_text(json.dumps(j,separators=(',',':'))+'\n')
config=stage/'tscircuit.config.json';c=json.loads(config.read_text());c['includeBoardFiles']=['index.circuit.json','assembly.circuit.json'];c['previewComponentPath']='assembly.circuit.json';config.write_text(json.dumps(c,indent=2)+'\n')
proof={'github_revision':revision,'review_board_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest(),'published_board_sha256':hashlib.sha256((stage/'index.circuit.json').read_bytes()).hexdigest(),'only_cad_url_metadata_changed':True,'saved_routing_preserved':True,'pinned_cad_components':sum(e['type']=='cad_component' and bool(e.get('model_obj_url')) for e in j)}
(stage/'artifacts/publication-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Prepared source package:',json.dumps(proof))
PYSTAGE
cd "$package_stage"
XDG_CONFIG_HOME=/workspace/.config tsci build index.circuit.json
XDG_CONFIG_HOME=/workspace/.config tsci build assembly.circuit.json
python3 - "$package_stage" <<'PYDIST'
import json,pathlib,sys
stage=pathlib.Path(sys.argv[1]);saved=json.loads((stage/'index.circuit.json').read_text());built=json.loads((stage/'dist/index/circuit.json').read_text())
assert built==saved,'Native CLI dist build differs from saved routing'
(stage/'dist/index/circuit.json').write_text(json.dumps(built,separators=(',',':'))+'\n')
assembly=json.loads((stage/'assembly.circuit.json').read_text())
assert json.loads((stage/'dist/assembly/circuit.json').read_text())==assembly
(stage/'dist/assembly/circuit.json').write_text(json.dumps(assembly,separators=(',',':'))+'\n')
print('Including verified compact native PCB and assembly dist files')
PYDIST
# Verify uploads even when the CLI returns zero: it can report failed files
# after a partial fallback upload. Native bounded archives repair missing rows.
if [ "${1:-}" = "--bounded-upload" ]; then
  python3 "$project_root/scripts/ensure-registry-release.py" "$package_stage"
fi
if [ "${1:-}" != "--recover-only" ] && [ "${1:-}" != "--bounded-upload" ]; then
  upload_log=$(mktemp /tmp/nema14-registry-upload.XXXXXX)
  XDG_CONFIG_HOME=/workspace/.config tsci push index.circuit.tsx --include-dist --compress > "$upload_log" 2>&1 || true
  python3 - "$upload_log" <<'PYLOG'
import pathlib,sys
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
 if len(line)<500 and any(word in line for word in ['Publish completed','failed upload','Error:','uploaded']):print(line)
PYLOG
fi
python3 "$project_root/scripts/recover-publication.py" "$package_stage"
python3 "$project_root/scripts/verify-publication.py" "$project_root"
python3 "$project_root/scripts/verify-assembly-publication.py" "$project_root"
python3 - "$package_stage" <<'PYVERSION'
import json,pathlib,sys
p=pathlib.Path(sys.argv[1]);print('Published registry version:',json.loads((p/'package.json').read_text())['version'])
PYVERSION
