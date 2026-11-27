"""Regress actual native replay, fixed-record preservation, and rejected controls."""
from pathlib import Path
import json,sys,subprocess,importlib.util,hashlib
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets
from shapely.geometry import LineString
from shapely.ops import unary_union
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def read(p):
 import gzip
 p=Path(p);return json.loads(p.read_bytes() if p.exists() else gzip.decompress(Path(str(p)+'.gz').read_bytes()))
root=Path('artifacts/iteration-6');tmp=Path('.config/anchored');tmp.mkdir(parents=True,exist_ok=True)
def command(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
# Fresh native source replay, including the otherwise unapproved .20mm comparison.
command(['bun','experiments/anchored/render.ts',str(tmp/'fresh.circuit.json'),'--scope=guarded','--small-star']);report,cu=v.verify(tmp/'fresh.circuit.json');assert cu['geometric_clearance_pass']
# Generator only accepts fresh copper-free native placement; moved pads alter regenerated anchors.
command(['bun','experiments/anchored/render.ts',str(tmp/'moved.circuit.json'),'--scope=guarded','--no-copper','--shift-shunt=.25']);command([sys.executable,'experiments/anchored/generate.py',str(tmp/'moved.circuit.json'),str(tmp/'moved-generated.json')]);fresh=read('experiments/anchored/generated.json');moved=read(tmp/'moved-generated.json')
for pin in ['pin1','pin2']:
 ref='R_SHUNT_A.'+pin;assert abs(moved['anchor_port_positions_mm'][ref][0]-fresh['anchor_port_positions_mm'][ref][0]-.25)<1e-10
for pole in ['POS','NEG']:
 name='KELVIN_A_'+pole;assert abs(moved['actual_pad_edges'][name][0]-fresh['actual_pad_edges'][name][0]-.25)<1e-10
bad=subprocess.run([sys.executable,'experiments/anchored/generate.py',str(tmp/'fresh.circuit.json'),str(tmp/'must-not-exist.json')],capture_output=True,text=True);assert bad.returncode and 'freshly generated without copper' in bad.stderr
# Physical branch geometry must be identical for mixed vs all-plural, despite differing record syntax.
def physical_paths(b):
 b=resolve_copper_nets(b);st={e['source_trace_id']:e.get('name','') for e in b if e['type']=='source_trace'};out={}
 for e in b:
  if e['type']!='pcb_trace':continue
  points=[]
  for node in e['route']:
   q={k:node[k] for k in ['route_type','x','y','width','layer']}
   # A duplicate identical endpoint has zero length and no added physical copper.
   # Every nonzero segment, real coordinate, width, layer and net stays exact.
   if not points or q!=points[-1]:points.append(q)
  out[st[e['source_trace_id']]]={'route':points,'net':e['subcircuit_connectivity_map_key']}
 return out
assert physical_paths(read(root/'current-coupon.circuit.json'))==physical_paths(read(root/'current-coupon-plural.circuit.json'))
forced=read(root/'current-coupon-forced-single-copper.json');assert len(forced['clearance_violations'])==5,'All-singular control must expose clipped-endpoint extension'
# Saved final CLI actual records compare exactly, not with coordinate or width tolerances.
case=root/'cli-guarded-CP1';before=read(case/'before.circuit.json');after=read(case/'native.circuit.json');assert not v.compare_fixed(before,after);assert sum(e['type']=='pcb_trace' for e in before)==32;assert sum(e['type']=='pcb_via' for e in before)==20
for field in ['x','width']:
 import copy,math
 edited=copy.deepcopy(after);t=next(e for e in edited if e['type']=='pcb_trace');t['route'][0][field]=math.nextafter(t['route'][0][field],math.inf);assert v.compare_fixed(before,edited)
rejected=read(case/'native.circuit.verification.json');assert rejected['native_fixed_copper']['whole_record_byte_equivalent'];assert rejected['independent']['clearance_violations']==2 and not rejected['geometric_clearance_pass'];assert read(case/'exit.json')['exit_code']==1
profile=read(root/'current-process.json');locked=read(root/'locked-process.json');assert profile['summary']['negative_assumption_adjusted_SMT_margins']==1;assert profile['summary']['width_plus_20_percent_spacing_findings']==11;assert locked['summary']['negative_assumption_adjusted_annular_margins']==4;assert not profile['supplier_acceptance_verified']
# Fresh native singular/plural crossing A/B. These runners exercise pinned Core, no patch.
for mode in ['singular','plural','protected-plural']:command(['bun','experiments/anchored/run-ab.ts',mode])
command([sys.executable,'experiments/anchored/verify-ab.py'])
print('PASS: fresh 53-part native geometry; 4 real pad cuts; 2 phase-only returns with conducted barrels; moved-anchor regeneration; copper-input rejection; mixed/plural geometry equivalence; 5 all-singular rejections; exact fixed-record controls; native singular/plural A/B. Full board and manufacturing remain rejected.')
