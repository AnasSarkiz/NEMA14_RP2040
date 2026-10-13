"""Prune only redundant dangling copper until native DRC is clean.

Every edit preserves the actual physical-pad partitions. Any clearance, short,
open or unknown error blocks this helper and must be resolved independently.
"""
import json,pathlib,os,subprocess,hashlib
root=pathlib.Path(__file__).resolve().parents[1];env=dict(os.environ);env['PATH']=str(root/'node_modules/.bin')+':'+env['PATH'];py='/workspace/.routing-venv/bin/python';rows=[]
for attempt in range(12):
 log=root/'artifacts/engineering-fixes'/('copper-DRC-pass-'+str(attempt)+'.txt')
 with log.open('w') as out:r=subprocess.run(['bun','scripts/check.ts'],cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
 report=json.loads((root/'artifacts/drc-report.json').read_text());errors=report['errors'];rows.append({'iteration':attempt,'exit_code':r.returncode,'errors':len(errors),'log':str(log.relative_to(root))});print(rows[-1],flush=True)
 if not errors and r.returncode==0:break
 if any('dangling endpoint' not in e.get('message','') for e in errors):raise RuntimeError('Copper DRC includes real or unrecognized errors; see current report')
 before=hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest()
 for s in ['prune-same-side-stubs.py','trim-same-side-stubs.py','clean-same-side-copper.py','fill-ground.py']:
  with log.open('a') as out:subprocess.run([py,'scripts/'+s],cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT,check=True)
 if hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest()==before:raise RuntimeError('No safe copper cleanup found')
else:raise RuntimeError('Native DRC has not converged')
(root/'artifacts/engineering-fixes/copper-cleanup-verification.json').write_text(json.dumps({'native_DRC_zero_errors':True,'iterations':rows,'board_sha256':hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest()},indent=2)+'\n')
