"""Native CLI source replay only. Routing is deliberately blocked by the full stress gate."""
from pathlib import Path
import subprocess,json,time,shutil,hashlib
r=Path('artifacts/iteration-9');cfg=Path('tscircuit.config.ts');original=cfg.read_bytes();control=b'export default { platformConfig: { partsEngineDisabled: true, schematicDisabled: true } }\n';args=['tsci','build','experiments/tolerance/candidate.tsx','--routing-disabled','--disable-parts-engine','--inject-props','{"process":"small-hole-screen"}'];start=time.monotonic()
try:
 cfg.write_bytes(control)
 with (r/'native-cli.log').open('w') as f:
  try:code=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
  except subprocess.TimeoutExpired:code=124
finally:cfg.write_bytes(original)
assert cfg.read_bytes()==original
(r/'native-cli-exit.json').write_text(json.dumps({'exit_code':code,'wall_s':time.monotonic()-start,'command':args,'scope':'Source generation only; no native routing stage allowed','schematic_drawing_disabled_only':True,'normal_config_restored':True,'normal_config_sha256':hashlib.sha256(original).hexdigest(),'PCB_DRC_thresholds_unchanged':True},indent=2)+'\n')
if code==0:shutil.copyfile('dist/experiments/tolerance/candidate/circuit.json',r/'native-cli.circuit.json')
print('Native CLI generation exit',code);raise SystemExit(code)
