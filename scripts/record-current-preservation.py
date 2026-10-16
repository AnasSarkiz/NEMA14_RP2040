"""Compare current electrical records and oscillator geometry with the Git baseline."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
path=ROOT/'artifacts/board.circuit.json';j=json.loads(path.read_text())
p=ROOT/'artifacts/opposite-edge/functional-and-crystal-preservation.json';previous=json.loads(p.read_text());revision=previous['baseline_commit']
old_bytes=subprocess.check_output(['git','show',revision+':artifacts/board.circuit.json'],cwd=ROOT)
old=json.loads(old_bytes)
proof={}
for typ in ['source_component','source_port','source_net','source_trace']:
 a=[e for e in j if e['type']==typ];b=[e for e in old if e['type']==typ]
 assert a==b,'Electrical baseline changed: '+typ
 proof[typ]={'count':len(a),'identical_to_latest_GitHub_baseline':True}
def oscillator(data):
 fields={'route','x','y','outer_diameter','hole_diameter','layers','from_layer','to_layer'}
 return {e[e['type']+'_id']:{k:v for k,v in e.items() if k in fields} for e in data if e['type'] in ['pcb_trace','pcb_via'] and e.get(e['type']+'_id','').startswith('oscillator_')}
assert oscillator(j)==oscillator(old),'Oscillator copper changed'
proof.update(component_functional_fields_unchanged=True,oscillator_copper_geometry_unchanged=True,oscillator_records=len(oscillator(j)),baseline_commit=revision,board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),physical_operation_verified=False)
p.write_text(json.dumps(proof,indent=2)+'\n')
src={e['source_component_id']:e for e in j if e['type']=='source_component'}
oldc={e['source_component_id']:e for e in old if e['type']=='pcb_component'}
moved=[]
for c in [e for e in j if e['type']=='pcb_component']:
 b=oldc[c['source_component_id']]
 if c['center']!=b['center'] or c['rotation']!=b['rotation']:moved.append(dict(reference=src[c['source_component_id']]['name'],before_center_mm=b['center'],after_center_mm=c['center'],before_rotation_deg=b['rotation'],after_rotation_deg=c['rotation']))
final=dict(board_sha256=proof['board_sha256'],baseline_board_sha256=hashlib.sha256(old_bytes).hexdigest(),baseline_github_commit=revision,all_functional_terminal_net_groups_and_NC_roles_preserved=True,existing_values_ratings_and_non_USB_MPNs_preserved=True,authorized_USB_replacement='GCT USB4145-03-0070-C C5815189 retained; opposite-edge placement',bottom_DNP_components=[src[c['source_component_id']]['name'] for c in j if c['type']=='pcb_component' and c.get('do_not_place')],fitted_components_on_top=sum(c['type']=='pcb_component' and not c.get('do_not_place') and src[c['source_component_id']]['ftype']!='simple_test_point' and c['layer']=='top' for c in j),bare_top_test_points=sum(c['type']=='pcb_component' and src[c['source_component_id']]['ftype']=='simple_test_point' and c['layer']=='top' for c in j),moved_references=moved,physical_hardware_tested=False,rear_motor_compatibility_verified=False)
(ROOT/'artifacts/engineering-fixes/final-engineering-verification.json').write_text(json.dumps(final,indent=2)+'\n');print(proof)
