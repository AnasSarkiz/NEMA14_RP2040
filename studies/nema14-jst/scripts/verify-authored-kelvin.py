from pathlib import Path
import sys,json,hashlib,math,importlib.util
from routing_geometry import resolve_copper_nets,pad_cut_topology,layer_copper,shared_outside_pad
spec=importlib.util.spec_from_file_location('copper',Path(__file__).with_name('inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
before=json.loads(Path(sys.argv[1]).read_text());raw=Path(sys.argv[2]).read_bytes();b=resolve_copper_nets(json.loads(raw))
sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={(sc[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'}
def named(j):
 names={e['source_trace_id']:e.get('name') for e in j if e['type']=='source_trace'}
 return {names[e['source_trace_id']]:e for e in j if e['type']=='pcb_trace' and names.get(e.get('source_trace_id'))}
old,new=named(before),named(b);rows=[]
for phase in 'AB':
 for pole,pin in [('POS','pin1'),('NEG','pin2')]:
  n='KELVIN_'+phase+'_'+pole;p='POWER_'+phase+'_'+pole;k=new[n];power=new[p];padport=pp['R_SHUNT_'+phase,pin];amplifier=pp['U_I'+phase,'IN_'+pole];terminal=pp['P_'+phase+'_'+pole,'pin1'];pad=next(e for e in b if e['type']=='pcb_smtpad' and e.get('pcb_port_id')==padport['pcb_port_id']);net=sp[padport['source_port_id']]['subcircuit_connectivity_map_key'];poly=g.pad_shape(pad)
  topology=pad_cut_topology(b,net,padport['pcb_port_id'],amplifier['pcb_port_id'],terminal['pcb_port_id'],poly,'top',g.pad_shape)
  copper=lambda ts:layer_copper(ts,b,g.pad_shape)
  length=lambda t:sum(math.hypot(a['x']-z['x'],a['y']-z['y']) for a,z in zip(t['route'],t['route'][1:]))
  pickup=k['route'][1];edge_distance=poly.boundary.distance(__import__('shapely').geometry.Point(pickup['x'],pickup['y']))
  rows.append({'branch':n,'fixed_geometry_preserved':k['route']==old[n]['route'] and power['route']==old[p]['route'],'kelvin_widths_mm':sorted({q['width'] for q in k['route'] if q['route_type']=='wire'}),'power_widths_mm':sorted({q['width'] for q in power['route'] if q['route_type']=='wire'}),'kelvin_length_mm':length(k),'power_length_mm':length(power),'pickup_centerline_at_actual_pad_edge_mm':edge_distance,'shared_copper_outside_actual_pad_mm2':shared_outside_pad(copper([k]),copper([power]),poly,'top'),'topology':topology})
r={'input_sha256':hashlib.sha256(raw).hexdigest(),'authored_source_sha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),'native_error_records':[(e['type'],e.get('message')) for e in b if e['type'].endswith('_error')],'branches':rows,'copper':g.inspect(sys.argv[2]),'manufacturing_qualified':False};Path(sys.argv[3]).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='copper'},indent=2));print('Copper',r['copper']['geometric_clearance_pass'],'connectivity',r['copper']['full_board_connectivity_pass'])
passed=all(q['fixed_geometry_preserved'] and q['topology']['actual_shunt_pad_is_required_pickup'] and q['shared_copper_outside_actual_pad_mm2']<1e-8 and q['pickup_centerline_at_actual_pad_edge_mm']<1e-6 and q['kelvin_widths_mm']==[.16] and q['power_widths_mm']==[.45] for q in rows) and not r['native_error_records'] and r['copper']['geometric_clearance_pass'] and r['copper']['full_board_connectivity_pass'];raise SystemExit(0 if passed else 1)
