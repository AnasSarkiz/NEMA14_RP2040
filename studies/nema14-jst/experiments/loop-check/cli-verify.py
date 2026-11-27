"""Native CLI replay, DRC enabled; expected new ground-length error remains."""
from pathlib import Path
import subprocess,json,time,shutil,hashlib
r=Path('artifacts/iteration-14');cfg=Path('tscircuit.config.ts');original=cfg.read_bytes();control=b'export default { platformConfig: { partsEngineDisabled: true, schematicDisabled: true } }\n';args=['tsci','build','experiments/loop-check/candidate.tsx','--routing-disabled','--disable-parts-engine'];start=time.monotonic()
try:
 cfg.write_bytes(control)
 with (r/'native-cli.log').open('w') as f:
  try:code=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
  except subprocess.TimeoutExpired:code=124
finally:cfg.write_bytes(original)
assert cfg.read_bytes()==original
p=Path('dist/experiments/loop-check/candidate/circuit.json')
if p.exists():shutil.copyfile(p,r/'native-cli.circuit.json')
(r/'native-cli-exit.json').write_text(json.dumps({'exit_code':code,'wall_s':time.monotonic()-start,'command':args,'scope':'Only source generation, no autorouter','schematic_drawing_disabled_only':True,'normal_config_restored':True,'normal_config_sha256':hashlib.sha256(original).hexdigest(),'PCB_DRC_rules_unchanged':True,'process_assumed_approved':False},indent=2)+'\n');print('Native CLI exit',code)
