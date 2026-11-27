"""Record the one bounded native stage without turning solver success into board acceptance."""
from pathlib import Path
import json,hashlib,math,sys,importlib.util
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets
from shapely.geometry import Point,LineString
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);v.spec=json.load(open('experiments/placement/generated.json'));r=Path('artifacts/iteration-8/native-VREG');before=json.load(open(r/'before.circuit.json'));after=json.load(open(r/'native.circuit.json'));changed=v.compare_fixed(before,after);assert not changed,changed;critical,cu=v.verify(r/'native.circuit.json',require_clean=False)
old_ids={e.get(e['type']+'_id') for e in before if e['type'] in ['pcb_trace','pcb_via']};bf=[e for e in before if e['type'] in ['pcb_trace','pcb_via']];af=[e for e in after if e['type'] in ['pcb_trace','pcb_via'] and e.get(e['type']+'_id') in old_ids];dump=lambda j:json.dumps(j,separators=(',',':')).encode();assert dump(bf)==dump(af);assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in json.load(open(r/'source-inputs.json')).items());native=resolve_copper_nets(after);rows=[]
for e in native:
 if e['type']!='pcb_trace':continue
 for a,z in zip(e['route'],e['route'][1:]):
  if a['route_type']!=z['route_type'] or a['route_type']!='wire' or a['layer']!=z['layer']:continue
  poly=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=128)
  for k in [x for x in native if x['type']=='pcb_keepout']:
   gap=poly.distance(Point(k['center']['x'],k['center']['y']).buffer(k['radius'],quad_segs=128))
   if gap<.15-1e-6:rows.append({'trace':e['pcb_trace_id'],'layer':a['layer'],'actual_trace_edge_to_keepout_gap_mm':gap,'required_native_keepout_clearance_mm':.15,'keepout_center_mm':[k['center']['x'],k['center']['y']]})
report={'before_traces':sum(e['type']=='pcb_trace' for e in before),'before_vias':sum(e['type']=='pcb_via' for e in before),'after_traces':sum(e['type']=='pcb_trace' for e in after),'after_vias':sum(e['type']=='pcb_via' for e in after),'all_fixed_records_byte_equivalent':True,'fixed_record_sha256':hashlib.sha256(dump(bf)).hexdigest(),'runtime_hashes_match_final_sources':True,'actual_vreg_connected':not any(x['net']=='VREG' for x in cu['disconnected_nets']),'independent':critical['independent'],'additional_native_keepout_clearance_findings':rows,'critical':critical,'cli_exit':json.load(open(r/'exit.json')),'native_result':json.load(open(r/'result.json')),'routed_controller_qualified':False,'fabrication_ready':False};(r/'verification.json').write_text(json.dumps(report,indent=2)+'\n');(r/'copper.json').write_text(json.dumps(cu,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['critical','native_result']})
