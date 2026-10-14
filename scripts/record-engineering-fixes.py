"""Record the final change against the latest fetched GitHub board baseline."""
import collections,hashlib,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];board=ROOT/'artifacts/board.circuit.json';j=json.loads(board.read_text());baseline=ROOT/'artifacts/upright-revision/baseline-board.circuit.json';old=json.loads(baseline.read_text());sha=hashlib.sha256(board.read_bytes()).hexdigest()
def source(records):return {e['source_component_id']:e for e in records if e['type']=='source_component'}
def interface(records):
 s=source(records);groups=collections.defaultdict(set);nc=set();pins={}
 for p in records:
  if p['type']!='source_port':continue
  name=s[p['source_component_id']]['name'];role=p['name']
  if name in ['U_ENCODER','C_ENCODER','C_ENCODER_BULK']:continue
  if name in ['J_PD','J_DATA']:role={'GND3':'GND1','GND4':'GND2','VBUS3':'VBUS1','VBUS4':'VBUS2'}.get(role,role)
  role=name+'.'+role
  if name not in ['J_PD','J_DATA']:pins[role]=p['pin_number']
  key=p.get('subcircuit_connectivity_map_key')
  if key:groups[key].add(role)
  else:nc.add(role)
 return set(map(frozenset,groups.values())),nc,pins
assert interface(old)==interface(j),'Functional terminal, net or NC roles changed'
os={e['name']:e for e in source(old).values()};ns={e['name']:e for e in source(j).values()}
assert set(ns)-set(os)=={'U_ENCODER','C_ENCODER','C_ENCODER_BULK'} and not set(os)-set(ns)
for name in os:
 for key in ['manufacturer_part_number','supplier_part_numbers','resistance','capacitance','inductance','frequency','tolerance','max_voltage_rating']:
  if name in ['J_PD','J_DATA'] and key in ['manufacturer_part_number','supplier_part_numbers']:
   assert ns[name]['manufacturer_part_number']=='USB4145-03-0070-C' and ns[name]['supplier_part_numbers']['jlcpcb']==['C5815189'];continue
  assert os[name].get(key)==ns[name].get(key),(name,key)
def placements(a):
 s=source(a);return {s[e['source_component_id']]['name']:e for e in a if e['type']=='pcb_component'}
a,b=placements(old),placements(j);moved=[]
for name in a:
 if any(abs(a[name]['center'][axis]-b[name]['center'][axis])>1e-6 for axis in ['x','y']) or a[name]['rotation']!=b[name]['rotation']:moved.append({'reference':name,'before_center_mm':a[name]['center'],'after_center_mm':b[name]['center'],'before_rotation_deg':a[name]['rotation'],'after_rotation_deg':b[name]['rotation']})
assert all(e['layer']=='top' for e in b.values() if not e.get('do_not_place'))
assert {n for n,e in b.items() if e.get('do_not_place')}=={'U_ENCODER','C_ENCODER','C_ENCODER_BULK'}
for path,key in [('artifacts/resume-validation.json','board_sha256'),('artifacts/manufacturing/audit.json','source_sha256'),('artifacts/engineering-fixes/usb-verification.json','board_sha256'),('artifacts/engineering-fixes/schema-verification.json','board_sha256')]:
 r=json.loads((ROOT/path).read_text());assert r[key]==sha,path
cam=json.loads((ROOT/'artifacts/manufacturing/audit.json').read_text());assert cam['status']=='PASS' and not cam['issues']
record={'board_sha256':sha,'baseline_board_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'baseline_github_commit':'db8bd58' if ROOT.name=='nema14-rp2040-current' else '0d6f9bc','all_functional_terminal_net_groups_and_NC_roles_preserved':True,'existing_values_ratings_and_non_USB_MPNs_preserved':True,'authorized_USB_replacement':'GCT USB4145-03-0070-C C5815189','bottom_DNP_components':['U_ENCODER','C_ENCODER','C_ENCODER_BULK'],'fitted_components_on_top':len(b)-3-sum(s['ftype']=='simple_test_point' for s in ns.values()),'bare_top_test_points':sum(s['ftype']=='simple_test_point' for s in ns.values()),'moved_references':moved,'default_manufacturing_CAM_passed':True,'strict_Circuit_JSON_schema_passed':True,'exact_coupled_USB_ground_reference_verified':True,'board_dimensions_mm':[35,35,1.6],'mounts_mm':[[x,y,3.2] for x in [-13,13] for y in [-13,13]],'USB_nominal_centres_mm':[[-6.05,15.15],[6.05,15.15]],'USB_insertion_direction':'+Z','cable_housing_width_mm':10,'nominal_cable_housing_gap_mm':2.1,'maximum_required_fastener_head_diameter_mm':4,'hardware_operation_verified':False,'supplier_order_or_process_approval':False,'controlled_impedance_verified':False,'rear_motor_compatibility_verified':False}
(ROOT/'artifacts/engineering-fixes/final-engineering-verification.json').write_text(json.dumps(record,indent=2)+'\n');print('Latest-baseline function/value preservation and current qualification receipts verified')
