"""Conservative moved-body OBJ bounds; not STEP, motor fit or handling qualification."""
from pathlib import Path
import json,math,hashlib,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from native_sources import source_owner_names
raw=Path(sys.argv[1]).read_bytes();j=json.loads(raw);delta=json.loads(Path(sys.argv[2]).read_text());plug=json.loads(Path(sys.argv[3]).read_text());catalog=json.loads((ROOT/'src/jlcpcb-catalog.json').read_text());sc=source_owner_names(j);cad={sc[e['source_component_id']]:e for e in j if e['type']=='cad_component'};pcs={sc[e['source_component_id']]:e for e in j if e['type']=='pcb_component'};rows=[]
baseline_path=ROOT/'artifacts/final-source.circuit.json';baseline_raw=baseline_path.read_bytes();assert hashlib.sha256(baseline_raw).hexdigest()==plug['board_sha256'],'Plug envelope must match the accepted native source'
baseline=json.loads(baseline_raw);bs={e['source_component_id']:e['name'] for e in baseline if e['type']=='source_component'};bcad={bs[e['source_component_id']]:e for e in baseline if e['type']=='cad_component'};bpcs={bs[e['source_component_id']]:e for e in baseline if e['type']=='pcb_component'}
geometry=lambda e:{k:v for k,v in e.items() if k not in ['model_obj_url','model_step_url']}
assert all(geometry(cad[n])==geometry(bcad[n]) for n in cad if n not in delta and n in catalog['components']),'Unchanged supplier transforms changed'
assert all(pcs[n]==bpcs[n] for n in ['J_PD','J_DATA','J_MOTOR','U_ENCODER']),'Fixed mechanical pose changed'
assert [e for e in j if e['type'] in ['pcb_board','pcb_hole','pcb_keepout']]==[e for e in baseline if e['type'] in ['pcb_board','pcb_hole','pcb_keepout']],'Board rules or mount geometry changed'
excluded=[n for n in delta if n not in catalog['components']]
assert all(n.startswith('TP_') for n in excluded),'Unknown non-supplier body'
for n in delta:
 if n in excluded:continue
 e=cad[n];part=catalog['parts'][catalog['components'][n]];rel=next(p for p in part['modelFiles'] if p.endswith('.obj'));data=(ROOT/rel).read_bytes();assert hashlib.sha256(data).hexdigest()==part['sha256']['obj'];v=[]
 for line in data.decode(errors='replace').splitlines():
  if not line.startswith('v '):continue
  q=list(map(float,line.split()[1:4]));q=[q[k]-e['model_origin_position'][a] for k,a in enumerate('xyz')]
  for a in 'xyz':
   angle=math.radians(e['rotation'][a]);c,t=math.cos(angle),math.sin(angle);x,y,z=q
   q=[x,c*y-t*z,t*y+c*z] if a=='x' else [c*x+t*z,y,-t*x+c*z] if a=='y' else [c*x-t*y,t*x+c*y,z]
  v.append([q[k]+e['position'][a] for k,a in enumerate('xyz')])
 lo=[min(q[k] for q in v) for k in range(3)];hi=[max(q[k] for q in v) for k in range(3)];gap=min(math.hypot(max(lo[0]-x,0,x-hi[0]),max(lo[1]-y,0,y-hi[1]))-3.2 for x in [-13,13] for y in [-13,13]);screens={}
 for label in ['seated_envelope','withdrawal_sweep','service_grip_envelope']:
  z=plug[label];screens[label]=math.sqrt(sum(max(lo[k]-z['max'][k],z['min'][k]-hi[k],0)**2 for k in range(3)))
 rows.append({'part':n,'supplier_obj_sha256':hashlib.sha256(data).hexdigest(),'native_transformed_supplier_bounds':{'min':lo,'max':hi},'minimum_screw_reserve_xy_gap_mm':gap,'plug_envelope_bounds_gaps_mm':screens,'layer':pcs[n]['layer']})
r={'native_input_sha256':hashlib.sha256(raw).hexdigest(),'scope':__doc__,'parts':rows,'screw_clear':all(q['minimum_screw_reserve_xy_gap_mm']>=0 for q in rows),'plug_clear':all(all(v>0 for v in q['plug_envelope_bounds_gaps_mm'].values()) for q in rows),'bottom_fitted_body_protrusion_below_board_mm':{q['part']:max(0,-.8-q['native_transformed_supplier_bounds']['min'][2]) for q in rows if q['layer']=='bottom'},'rear_motor_magnet_fit_verified':False,'physical_handling_verified':False,'bare_pad_testpoint_CAD_markers_not_supplier_bodies':excluded,'all_bare_testpoint_courtyards_still_checked':True};Path(sys.argv[4]).write_text(json.dumps(r,indent=2)+'\n');print('Body bounds',r['screw_clear'],r['plug_clear'],r['bottom_fitted_body_protrusion_below_board_mm']);raise SystemExit(0 if r['screw_clear'] and r['plug_clear'] else 1)
