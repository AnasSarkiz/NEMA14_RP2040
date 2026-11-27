"""Fresh native/independent checks; the physical improvement must retain its native rejection."""
from pathlib import Path
import subprocess,json,tempfile,gzip,copy,hashlib,math
root=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_bytes() if p.exists() else gzip.decompress(Path(str(p)+'.gz').read_bytes()))
with tempfile.TemporaryDirectory(prefix='nema14-jst-loop-') as tmp:
 p=Path(tmp)
 subprocess.run(['bun','experiments/loop-check/render.ts',str(p/'candidate.circuit.json')],cwd=root,check=True)
 subprocess.run(['bun','experiments/integrated/check-native.ts',str(p/'candidate.circuit.json'),str(p/'native.json'),'--all'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 subprocess.run(['python3','experiments/loop-check/audit.py',str(p)],cwd=root,check=True,stdout=subprocess.DEVNULL)
 fresh=read(p/'candidate.circuit.json');golden=read(root/'artifacts/iteration-14/candidate.circuit.json')
 def records(data,typ):
  out=copy.deepcopy([e for e in data if e['type']==typ])
  for e in out:
   if typ=='cad_component':e.pop('model_obj_url',None);e.pop('model_step_url',None)
   if typ=='pcb_trace':
    actual=sum(math.dist((u['x'],u['y']),(v['x'],v['y'])) for u,v in zip(e['route'],e['route'][1:]) if u['route_type']==v['route_type']=='wire' and u['layer']==v['layer']);assert abs(e.pop('trace_length')-actual)<1e-12
  return out
 for typ in ['source_component','source_port','source_net','source_trace','pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_via','pcb_trace','pcb_board','pcb_hole','pcb_keepout','pcb_courtyard_outline','cad_component']:assert records(fresh,typ)==records(golden,typ),typ
 a=read(p/'audit.json');assert a['complete_external_decoupling_connections_verified'] and a['native']['new_ground_length_error']['maximum_trace_length']==1 and a['preserved_whole_pcb_trace_records']==44 and a['preserved_via_whole_records']==22
 assert a['new_route_closest_foreign_objects'][0]['simultaneous_stressed_gap_mm']>.18 and len(a['inherited_all_SMT_star_hole_failures'])==2
 assert a['full_board_disconnected_nets_before_after']==[59,59] and a['ground_island_count_before_after']==[83,82]
 # The independent audit must reject fake length caches, source-rule changes, width changes and prior fixed-copper edits.
 source={e['source_trace_id']:e.get('name') for e in fresh if e['type']=='source_trace'}
 for mutation in ['cache','limit','width','old-copper']:
  bad=copy.deepcopy(fresh);new=next(e for e in bad if e['type']=='pcb_trace' and source[e['source_trace_id']]=='VREG_GROUND_LOOP')
  if mutation=='cache':new['trace_length']=.9
  elif mutation=='limit':next(e for e in bad if e['type']=='source_trace' and e.get('name')=='VREG_GROUND_LOOP')['max_length']=5
  elif mutation=='width':new['route'][0]['width']=.15
  else:next(e for e in bad if e['type']=='pcb_trace' and source[e['source_trace_id']]=='AUTHORED_CP1_CORRIDOR')['route'][0]['x']+=.001
  (p/'candidate.circuit.json').write_text(json.dumps(bad));result=subprocess.run(['python3','experiments/loop-check/audit.py',str(p)],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);assert result.returncode!=0,mutation
 subprocess.run(['bun','experiments/loop-check/ep-diagnose.ts',str(p/'ep-controls')],cwd=root,check=True,stdout=subprocess.DEVNULL)
 d=read(p/'ep-controls/diagnosis.json');rows={r['mode']:r for r in d['rows']}
 assert [len(rows[n]['via_in_pad']) for n in ['own','own-exposed','foreign','outside','no-vias']]==[4,4,4,0,0]
 assert len(rows['own']['via_pad_clearance'])==0 and len(rows['foreign']['via_pad_clearance'])==4
 assert d['schema_unknown_fill_fields_retained']==d['props_unknown_fill_fields_retained']==[] and all(r['global_allow_flag'] is None for r in d['rows']) and d['DRC_suppressed'] is False
print('PASS: physical VREG external legs close with0.1804mm stressed clearance,44fixed traces/22vias/fourKelvin cuts exact; native ground1mm gate and2inherited drill failures retained. Minimal EP controls4/4/4/0/0; no fill representation, DRC bypass, process adoption or further routing.')
