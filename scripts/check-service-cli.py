"""Record real native CLI exits; placement advisories remain visible."""
import subprocess,pathlib,json,os,hashlib
root=pathlib.Path(__file__).resolve().parents[1];os.chdir(root);out=root/'artifacts/validation';env=os.environ.copy();env['PATH']=str(root/'node_modules/.bin')+':'+env['PATH'];env['XDG_CONFIG_HOME']='/workspace/.config';results=[]
for label,args in [('netlist',['netlist','index.circuit.tsx']),('pin-specification',['pin_specification','index.circuit.tsx']),('source',['source','index.circuit.tsx']),('placement',['placement','index.circuit.tsx']),('schematic',['schematic-placement','artifacts/final-source.circuit.json'])]:
 command=['tsci','check']+args;r=subprocess.run(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);log=out/('service-cli-'+label+'.txt');log.write_text(r.stdout);results.append({'name':label,'command':command,'exit_code':r.returncode,'output':str(log.relative_to(root)),'output_sha256':hashlib.sha256(log.read_bytes()).hexdigest()});print(label,r.returncode,flush=True)
report={'source_entry_sha256':hashlib.sha256((root/'index.circuit.tsx').read_bytes()).hexdigest(),'prepared_source_sha256':hashlib.sha256((root/'artifacts/final-source.circuit.json').read_bytes()).hexdigest(),'commands':results,'placement_advisories_are_not_suppressed':True};(out/'service-cli-results.json').write_text(json.dumps(report,indent=2)+'\n')
assert all(r['exit_code']==0 for r in results if r['name']!='placement'),results
p=(out/'service-cli-placement.txt').read_text();assert 'Errors: 0\nWarnings: 0' in p,p
