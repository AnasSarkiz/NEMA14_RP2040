"""Pinned native CLI control: temporarily disable schematic drawing, retain every PCB/DRC rule.
Always restore the exact normal config. This changes renderer configuration, not design data.
"""
from pathlib import Path
import subprocess,json,sys,hashlib,time
root=Path('artifacts/iteration-8');cfg=Path('tscircuit.config.ts');original=cfg.read_bytes();diagnostic=b'export default { platformConfig: { partsEngineDisabled: true, schematicDisabled: true } }\n';mode=sys.argv[1];assert mode in ['generation','normal-generation','VREG'];out=root/('native-'+mode);out.mkdir(exist_ok=True);start=time.monotonic()
args=['tsci','build','experiments/reconnect/native-entry.tsx','--disable-parts-engine','--inject-props',json.dumps({'process':'small-hole-screen','net':'VREG','out':str(out)})]
if mode.endswith('generation'):args+=['--routing-disabled']
try:
 cfg.write_bytes(original if mode=='normal-generation' else diagnostic)
 with (out/'cli.log').open('w') as f:
  try:result=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=45 if mode=='normal-generation' else 80);code=result.returncode
  except subprocess.TimeoutExpired:code=124
finally:cfg.write_bytes(original)
assert cfg.read_bytes()==original
(out/'exit.json').write_text(json.dumps({'exit_code':code,'elapsed_s':time.monotonic()-start,'command':args,'schematic_drawing_disabled_only':mode!='normal-generation','PCB_DRC_enabled':True,'normal_config_restored':True,'normal_config_sha256':hashlib.sha256(original).hexdigest(),'diagnostic_config_text':diagnostic.decode()},indent=2)+'\n');print('Native CLI',mode,'exit',code);sys.exit(0 if code in [0,1] else code)
