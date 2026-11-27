"""Check the native/CAM review contract and retain its explicit rejection state."""
from pathlib import Path
import json,subprocess,tempfile,re,hashlib
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='nema14-jst-ep-') as tmp:
 subprocess.run(['bun','experiments/ep-process/render.ts',tmp],cwd=root,check=True)
 p=Path(tmp);load=lambda n:json.loads((p/n).read_text());native=load('candidate.circuit.json');cam=load('candidate-cam-review.circuit.json')
 ep=next(e for e in native if e['type']=='pcb_smtpad' and e.get('width')==3.15);port=next(e for e in native if e['type']=='pcb_port' and e['pcb_port_id']==ep['pcb_port_id']);sp=next(e for e in native if e['type']=='source_port' and e['source_port_id']==port['source_port_id']);vs=[e for e in native if e['type']=='pcb_via'];assert len(vs)==4 and all(v['hole_diameter']==.3 and v['outer_diameter']==.75 and v['subcircuit_connectivity_map_key']==sp['subcircuit_connectivity_map_key'] for v in vs)
 assert not any(e['type']=='pcb_trace' for e in native)
 errors=[e for e in native if 'error' in e['type']];assert len(errors)==4 and all(e['type']=='pcb_placement_error' and 'overlaps SMD pad D.EP' in e['message'] for e in errors)
 assert load('endpoint-outside-native.json')['by_type']=={'pcb_trace_error':2};assert load('endpoint-inside-native.json')['by_type']=={}
 assert all(len([e for e in load(n+'.circuit.json') if e['type']=='pcb_trace'])==2 for n in ['endpoint-outside','endpoint-inside'])
 additions=cam[len(native):];assert cam[:len(native)]==native and len(additions)==4 and all(e['type']=='pcb_solder_paste' and e['width']==e['height']==1.25 for e in additions)
 assert not any(e['type']=='pcb_solder_paste' and e.get('pcb_smtpad_id')==ep['pcb_smtpad_id'] for e in native)
 assert 'Never select every0.30mm via' in (p/'cam-review-only/README-DO-NOT-FABRICATE.md').read_text();assert len((p/'cam-review-only/SELECTIVE-FILL.csv').read_text().splitlines())==5
 g=(p/'cam-review-only/F_Paste.gbr').read_text();assert re.search(r'ADD\d+R,1\.250000X1\.250000',g),g[-500:]
 drill=(p/'cam-review-only/drill-L1-L4.drl').read_text();assert 'T10C0.300000' in drill and len(re.findall(r'^X.*Y',drill,re.M))==4
 # Repeat geometry must remain exact; only CAM creation timestamps vary.
 for n in ['candidate.circuit.json','candidate-cam-review.circuit.json','endpoint-outside.circuit.json','endpoint-inside.circuit.json']:
  assert load(n)==json.loads((root/'artifacts/iteration-13'/n).read_text()),n
proc=json.loads((root/'experiments/ep-process/process.json').read_text());assert proc['approved_for_manufacture'] is False and proc['planes_ground_returns_or_VREG_loop_routed'] is False and len(proc['array']['selective_fill_only'])==4
print('PASS: native own-ground via identity, four retained native EP placement errors, endpoint diagnostic2->0, explicit CAM-only paste4tiles, selective4hole drill; no process/board promotion or routing.')
