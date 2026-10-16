"""Run the current native, connectivity, schematic and manufacturing checks."""
import datetime,hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
out=ROOT/'artifacts/ch224a-migration';logs=out/'validation';logs.mkdir(exist_ok=True)
env=dict(os.environ);env['PATH']=str(ROOT/'node_modules/.bin')+':'+env['PATH'];env['XDG_CONFIG_HOME']='/workspace/.config'
steps=[
    ('source-generation',['npm','run','source:check']),
    ('typescript',['npm','run','typecheck']),
    ('build-and-native-drc',['npm','run','build']),
    ('physical-connectivity',[sys.executable,'scripts/verify-connectivity.py']),
    ('circuit-json-schema',['npm','run','check:schema']),
    ('schematic-placement-and-connectivity',['npm','run','check:schematic']),
    ('a4-pdf',[sys.executable,'scripts/export-a4-pdf.py']),
    ('gerbers-bom-and-cpl',['npm','run','export']),
    ('trace-widths',['npm','run','check:copper']),
    ('mounting-holes-and-clearance',['npm','run','check:mounts']),
    ('manufacturing-cam',['npm','run','check:manufacturing']),
    ('gerber-shorts',['npm','run','shorts']),
    ('circular-keepout-regression',['npm','run','check:circle']),
    ('migration-pin-map-and-preservation',['npm','run','check:pd']),
]
results=[]
for name,command in steps:
    print('RUN',name,flush=True)
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (logs/(name+'.log')).open('w') as f:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
    results.append({'check':name,'command':command,'started_utc':started,'exit_code':result.returncode,'log':str((logs/(name+'.log')).relative_to(ROOT))})
    path=ROOT/'artifacts/board.circuit.json'
    receipt={'passed':all(r['exit_code']==0 for r in results) and len(results)==len(steps),'completed_checks':len(results),'required_checks':len(steps),'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'version':json.loads((ROOT/'package.json').read_text())['version'],'checks':results,'hardware_operation_verified':False,'manufacturing_release':False}
    (out/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS' if result.returncode==0 else 'FAIL',name,flush=True)
    if result.returncode:
        print('See',logs/(name+'.log'),flush=True)
        sys.exit(result.returncode)
print('All',len(steps),'migration validation checks passed.',flush=True)
