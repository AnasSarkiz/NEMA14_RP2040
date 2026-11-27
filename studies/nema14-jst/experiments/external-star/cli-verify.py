"""Two native CLI source-only controls. No routing allowed through rejected width/loop gates."""
from pathlib import Path
import subprocess,json,time,shutil,hashlib
r=Path('artifacts/iteration-12');cfg=Path('tscircuit.config.ts');original=cfg.read_bytes();control=b'export default { platformConfig: { partsEngineDisabled: true, schematicDisabled: true } }\n';rows=[]
try:
 cfg.write_bytes(control)
 for mode,entry in [('external','candidate'),('direct','top-direct')]:
  args=['tsci','build','experiments/external-star/'+entry+'.tsx','--routing-disabled','--disable-parts-engine'];start=time.monotonic()
  with (r/(mode+'-cli.log')).open('w') as f:
   try:code=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
   except subprocess.TimeoutExpired:code=124
  rows.append({'mode':mode,'exit_code':code,'wall_s':time.monotonic()-start,'command':args})
  if code==0:shutil.copyfile('dist/experiments/external-star/'+entry+'/circuit.json',r/(mode+'-cli.circuit.json'))
finally:cfg.write_bytes(original)
assert cfg.read_bytes()==original
(r/'cli-exit.json').write_text(json.dumps({'runs':rows,'scope':'Native source generation only; no routing stage is allowed','normal_config_restored':True,'normal_config_sha256':hashlib.sha256(original).hexdigest(),'thresholds_unchanged':True},indent=2)+'\n');print(rows);raise SystemExit(0 if all(e['exit_code']==0 for e in rows) else 1)
