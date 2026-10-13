"""Prevent publication of an unqualified or stale saved board revision."""
import hashlib,json,pathlib,re,sys
from placement_advisories import orientation_advisories_only
root=pathlib.Path(__file__).resolve().parents[1];board=root/'artifacts/board.circuit.json';sha=hashlib.sha256(board.read_bytes()).hexdigest();errors=[];prototype="--prototype" in sys.argv
receipt_path=root/'artifacts/resume-validation.json'
if not receipt_path.exists():errors.append('No complete current qualification receipt.')
else:
 r=json.loads(receipt_path.read_text())
 if r.get('board_sha256')!=sha:errors.append('Qualification receipt belongs to a different board revision.')
 if not r.get('native_STEP_mechanical_pass'):errors.append('Current native STEP mechanical check has not passed.')
 for e in r.get('checks',[]):
  if not e['exit_code']:continue
  if prototype and e['check']=='native_placement':
   log=(root/e['log']).read_text()
   if orientation_advisories_only(log):continue
  errors.append('Check failed: '+e['check'])
 required={'all_resistor_edge_clearances','schematic_geometry_ERC','typescript','drc','connectivity','fitted_JST_and_actual_drills','exact_mounts_and_actual_drills','native_json_checks','native_netlist','native_pin_specification','native_source','native_schematic-placement','native_placement','every_trace_review','reference_feedback','gerber_shorts','copper_widths','full_independent_CAM','strict_Circuit_JSON_schema','USB_coupled_copper_and_ground_reference'}
 if required-{e['check'] for e in r.get('checks',[])}:errors.append('Qualification receipt is missing required checks.')
 cam=json.loads((root/'artifacts/manufacturing/audit.json').read_text())
 if cam.get('source_sha256')!=sha:errors.append('Independent CAM receipt is stale.')
 if r.get('full_CAM_status')!='PASS' or cam.get('status')!='PASS' or cam.get('issues'):errors.append('Independent manufacturing audit has not passed.')
if json.loads((root/'index.circuit.json').read_text())!=json.loads(board.read_text()):errors.append('Delivered preview differs from the saved board.')
print(json.dumps({'publication_allowed':not errors,'board_sha256':sha,'publication_scope':'hardware prototype; supplier approval and bench qualification remain incomplete' if prototype else 'all recorded checks passed','blockers':errors},indent=2))
raise SystemExit(bool(errors))
