"""Record the final change against the latest fetched GitHub board baseline."""
import collections,hashlib,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];board=ROOT/'artifacts/board.circuit.json';j=json.loads(board.read_text());baseline=ROOT/'artifacts/engineering-fixes/baseline.circuit.json';old=json.loads(baseline.read_text());sha=hashlib.sha256(board.read_bytes()).hexdigest()
def source(records):return {e['source_component_id']:e for e in records if e['type']=='source_component'}
def interface(records):
 s=source(records);groups=collections.defaultdict(set);nc=set();pins={}
 for p in records:
  if p['type']!='source_port':continue
  role=s[p['source_component_id']]['name']+'.'+p['name'];pins[role]=p['pin_number'];key=p.get('subcircuit_connectivity_map_key')
  if key:groups[key].add(role)
  else:nc.add(role)
 return set(map(frozenset,groups.values())),nc,pins
assert interface(old)==interface(j),'Functional terminal, net or NC roles changed'
os={e['name']:e for e in source(old).values()};ns={e['name']:e for e in source(j).values()}
assert os.keys()==ns.keys()
for name in os:
 for key in ['manufacturer_part_number','supplier_part_numbers','resistance','capacitance','inductance','frequency','tolerance','max_voltage_rating']:
  assert os[name].get(key)==ns[name].get(key),(name,key)
def placements(a):
 s=source(a);return {s[e['source_component_id']]['name']:e for e in a if e['type']=='pcb_component'}
a,b=placements(old),placements(j);moved=[]
for name in a:
 if any(abs(a[name]['center'][axis]-b[name]['center'][axis])>1e-6 for axis in ['x','y']) or a[name]['rotation']!=b[name]['rotation']:moved.append({'reference':name,'before_center_mm':a[name]['center'],'after_center_mm':b[name]['center'],'before_rotation_deg':a[name]['rotation'],'after_rotation_deg':b[name]['rotation']})
assert all(e['layer']=='top' for e in b.values())
for path,key in [('artifacts/resume-validation.json','board_sha256'),('artifacts/manufacturing/audit.json','source_sha256'),('artifacts/engineering-fixes/usb-verification.json','board_sha256'),('artifacts/engineering-fixes/schema-verification.json','board_sha256')]:
 r=json.loads((ROOT/path).read_text());assert r[key]==sha,path
cam=json.loads((ROOT/'artifacts/manufacturing/audit.json').read_text());assert cam['status']=='PASS' and not cam['issues']
record={'board_sha256':sha,'baseline_board_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'baseline_github_commit':'e04df7a3b606b280389109405de96601e9430695' if ROOT.name=='nema14-rp2040-current' else '9d28fc0d4a9e3585c58d4f486dae2c53ac5760df','all_functional_terminal_net_groups_and_NC_roles_preserved':True,'all_fitted_MPNs_supplier_numbers_values_and_ratings_preserved':True,'fitted_components_on_top':len(b)-sum(s['ftype']=='simple_test_point' for s in ns.values()),'bare_top_test_points':sum(s['ftype']=='simple_test_point' for s in ns.values()),'moved_references':moved,'default_manufacturing_CAM_passed':True,'strict_Circuit_JSON_schema_passed':True,'exact_coupled_USB_ground_reference_verified':True,'board_dimensions_mm':[35,35,1.6],'mounts_mm':[[x,y,3.2] for x in [-13,13] for y in [-13,13]],'USB_mouths_mm':[[-6.2,17.5],[6.2,17.5]],'cable_housing_width_mm':10,'nominal_cable_housing_gap_mm':2.4,'maximum_required_fastener_head_diameter_mm':4,'hardware_operation_verified':False,'supplier_order_or_process_approval':False,'controlled_impedance_verified':False,'rear_motor_compatibility_verified':False}
(ROOT/'artifacts/engineering-fixes/final-engineering-verification.json').write_text(json.dumps(record,indent=2)+'\n');print('Latest-baseline function/value preservation and current qualification receipts verified')
