"""Meaningful full native replay and rejection controls; no router or upstream A/B rerun here."""
from pathlib import Path
import json,sys,copy,subprocess,importlib.util,math,gzip
sys.path.insert(0,'scripts')
from native_sources import source_owner_names
root=Path('artifacts/iteration-7');tmp=Path('.config/full-placement');tmp.mkdir(parents=True,exist_ok=True)
def read(p):
 p=Path(p);return json.loads(p.read_bytes() if p.exists() else gzip.decompress(Path(str(p)+'.gz').read_bytes()))
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
fresh=tmp/'fresh.circuit.json';run(['bun','experiments/placement/render.ts',str(fresh),'--small-hole-screen']);run([sys.executable,'experiments/placement/screen.py',str(fresh),str(tmp/'screen.json')]);screen=read(tmp/'screen.json');assert screen['full_nominal_placement_pass'] and not screen['native_errors_by_type'];assert screen['top_courtyards']==101
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);v.spec=read('experiments/placement/generated.json');critical,cu=v.verify(fresh);assert len(critical['four_actual_pad_pickups'])==4;assert all(r['finished_stack_centerline_mm']<=5 for r in critical['actual_ground_returns'])
# Exact physical/source replay; only the recomputed derived length cache has a numerical tolerance.
a=read(root/'full-authored.circuit.json');b=read(fresh);types=['source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_courtyard_outline','pcb_via','pcb_trace','pcb_board','pcb_hole','pcb_keepout']
def normalize(j,typ):
 rows=copy.deepcopy([e for e in j if e['type']==typ])
 if typ=='pcb_trace':
  for e in rows:
   assert abs(e['trace_length']-v.length([e]))<=1e-12;e.pop('trace_length',None)
 return rows
for typ in types:assert normalize(a,typ)==normalize(b,typ),'Native replay changed '+typ
# A new courtyard overlap must fail even when no pad touches.
wrong=copy.deepcopy(b);names=source_owner_names(wrong);pc={e['pcb_component_id']:names[e['source_component_id']] for e in wrong if e['type']=='pcb_component'};courts={pc[e['pcb_component_id']]:e for e in wrong if e['type']=='pcb_courtyard_outline' and e['layer']=='top'};courts['C_TEMP']['outline']=copy.deepcopy(courts['U_TEMP']['outline']);f=tmp/'bad-courtyard.json';f.write_text(json.dumps(wrong));bad=subprocess.run([sys.executable,'experiments/placement/screen.py',str(f),str(tmp/'bad-screen.json')],stdout=subprocess.DEVNULL);assert bad.returncode==1;assert not read(tmp/'bad-screen.json')['full_nominal_placement_pass']
# Pin/net corruption is rejected by the full source contract.
wrong=copy.deepcopy(b);owners=source_owner_names(wrong);port=next(e for e in wrong if e['type']=='source_port' and owners[e['source_component_id']]=='U_IA' and e['name']=='IN_NEG');port['subcircuit_connectivity_map_key']='incorrect-current-sense-net';f=tmp/'bad-pin-contract.json';f.write_text(json.dumps(wrong));result=subprocess.run([sys.executable,'experiments/placement/screen.py',str(f),str(tmp/'bad-pin.json')],capture_output=True,text=True);assert result.returncode!=0 and 'Source pin/net contract changed' in result.stderr
# Previous actual CP1 violations reproduce; new source corridor clears the unchanged rule.
old=read(root/'cp1-reproduction.json');assert len(old['violations'])==2 and all(e['actual_clearance_mm']<.15 for e in old['violations']);corridor=read('experiments/placement/cp1-path.json');assert corridor['minimum_foreign_copper_clearance_mm']>=.175
loc=read(root/'critical-verification.json')['locality'];assert loc['previous_pass']==41 and loc['candidate_pass']==43 and not loc['regressed_previous_passes'];mfg=read(root/'process-screen.json');assert all(mfg['summary'][k]==0 for k in ['negative_assumption_adjusted_SMT_margins','negative_assumption_adjusted_annular_margins','assumption_adjusted_inner_via_rule_failures']);assert mfg['summary']['width_plus_20_percent_spacing_findings']==11 and not mfg['supplier_acceptance_verified'];assert read(root/'locked-process-screen.json')['summary']['negative_assumption_adjusted_annular_margins']==4
# Keep the actual native output rejected, with exact fixed-record preservation.
case=root/'native-CP2';before=read(case/'before.circuit.json');after=read(case/'native.circuit.json');assert not v.compare_fixed(before,after);receipt=read(case/'verification.json');assert receipt['all_fixed_records_byte_equivalent'] and receipt['before_traces']==33 and receipt['before_vias']==20 and receipt['independent']['disconnected_nets']==62 and receipt['independent']['clearance_violations']==2 and receipt['cli_exit']['exit_code']==1;assert not receipt['routed_controller_qualified']
for key in ['x','width']:
 changed=copy.deepcopy(after);t=next(e for e in changed if e['type']=='pcb_trace');t['route'][0][key]=math.nextafter(t['route'][0][key],math.inf);assert v.compare_fixed(before,changed)
print('PASS: full 102-part native replay; 101 courtyards; 0 nominal copper/courtyard conflicts; four actual shunt-pad cuts; two real barrel-inclusive returns; 43/59 locality with all 41 prior passes; pin/courtyard/record rejection controls. CP2 route, production locality and fabrication remain rejected.')
