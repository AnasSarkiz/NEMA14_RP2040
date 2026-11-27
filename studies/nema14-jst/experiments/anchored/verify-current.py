"""Physical checks for the separate anchored diagnostic; never a controller release gate."""
from pathlib import Path
import json,sys,math,hashlib,importlib.util,copy
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets,pad_cut_topology,shared_outside_pad
from native_sources import source_owner_names
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
s=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
root=Path('artifacts/iteration-6');spec=json.load(open('experiments/anchored/generated.json'))
def index(b):
 names=source_owner_names(b);sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={(names[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'};pads={e['pcb_port_id']:e for e in b if e['type']=='pcb_smtpad'};st={e['source_trace_id']:e for e in b if e['type']=='source_trace'};pcs={names[e['source_component_id']]:e for e in b if e['type']=='pcb_component'};return sp,pp,pads,st,pcs

def length(ts):return sum(math.hypot(a['x']-z['x'],a['y']-z['y']) for t in ts for a,z in zip(t['route'],t['route'][1:]) if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer'])
def verify(path,require_clean=True):
 raw=Path(path).read_bytes();b=resolve_copper_nets(json.loads(raw));sp,pp,pads,st,pcs=index(b);traces=[e for e in b if e['type']=='pcb_trace'];vs=[e for e in b if e['type']=='pcb_via'];via={v['name']:next(e for e in vs if math.hypot(e['x']-v['x'],e['y']-v['y'])<1e-9) for v in spec['vias']};fragments={f['name']:f for f in spec['fragments']}
 def group(n):return [e for e in traces if st[e['source_trace_id']].get('name','')==n or st[e['source_trace_id']].get('name','').startswith(n+'__')]
 for f in spec['fragments']:
  ts=group(f['name']);assert len(ts)==1,(f['name'],len(ts));assert all(n['width']==f['width_mm'] for t in ts for n in t['route'] if n['route_type']=='wire'),f['name']
  key=st[ts[0]['source_trace_id']]['subcircuit_connectivity_map_key'];assert ts[0]['subcircuit_connectivity_map_key']==key
  for selector in [f['from'],f['to']]:
   owner,pin=selector[1:].split(' > .')
   if owner.startswith('V_'):
    assert via[owner]['subcircuit_connectivity_map_key']==key and pin in via[owner]['layers'],(f['name'],selector,'wrong real barrel net/layer')
   else:assert sp[pp[owner,pin]['source_port_id']]['subcircuit_connectivity_map_key']==key,(f['name'],selector,'wrong net')
 for ref,xy in spec['anchor_port_positions_mm'].items():
  q=pp[tuple(ref.split('.'))];assert [q['x'],q['y']]==xy,('stale',ref)
 def branch_shapes(ts):
  by={}
  for t in ts:
   for a,z in zip(t['route'],t['route'][1:]):
    if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:by.setdefault(a['layer'],[]).append(LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(min(a['width'],z['width'])/2,quad_segs=128))
  wires={l:unary_union(gs) for l,gs in by.items()};keys={e['subcircuit_connectivity_map_key'] for e in ts}
  for v in vs:
   if v.get('subcircuit_connectivity_map_key') not in keys:continue
   shape=g.pad_shape(v).difference(g.pad_shape(v,True))
   if not any(l in wires and shape.intersection(wires[l]).area>1e-10 for l in v['layers']):continue
   for l in v['layers']:by.setdefault(l,[]).append(shape)
  return {l:unary_union(gs) for l,gs in by.items()}
 pickups=[];lengths={}
 for phase in 'AB':
  for pole,pin,target,power in [('POS','pin1',('U_DRV','OUT1A' if phase=='A' else 'OUT2A'),'DRV'),('NEG','pin2',('J_MOTOR',phase+'_PLUS'),'COIL')]:
   name=f'KELVIN_{phase}_{pole}';kn=group(name);pn=group(f'POWER_{phase}_{power}');port=pp['R_SHUNT_'+phase,pin];pad=g.pad_shape(pads[port['pcb_port_id']]);amp=pp['U_I'+phase,'IN_'+pole];key=sp[port['source_port_id']]['subcircuit_connectivity_map_key'];topo=pad_cut_topology(b,key,port['pcb_port_id'],amp['pcb_port_id'],pp[target]['pcb_port_id'],pad,'top',g.pad_shape);assert topo['actual_shunt_pad_is_required_pickup'],name;overlap=shared_outside_pad(branch_shapes(kn),branch_shapes(pn),pad,'top');assert overlap<1e-8,(name,overlap);edge=spec['actual_pad_edges'][name];assert pad.boundary.distance(Point(*edge))<1e-6
   pickups.append({'branch':name,'actual_body_facing_edge_mm':edge,'shared_winding_copper_outside_pad_mm2':overlap,**topo})
 for n in list(spec['paths'])+['AUTHORED_SENSE_A','AUTHORED_SENSE_B']:lengths[n]=length(group(n))
 # Use only this phase's three wires, two real annular barrels, source pad, and EP.
 # Subtract ALL actual drilled holes from planar wires/pads as well as the via rings.
 def return_connected(phase,missing=None,narrow=False):
  ts=[t for suffix in ['TOP','INNER','EP'] for t in group('RETURN_'+phase+'_'+suffix)];holes=unary_union([g.pad_shape(v,True) for v in vs]);records=[]
  for t in ts:
   for a,z in zip(t['route'],t['route'][1:]):
    if a['route_type']!=z['route_type'] or a['route_type']!='wire' or a['layer']!=z['layer']:continue
    if min(a['width'],z['width'])<.6 or narrow:return False
    shape=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(.3,quad_segs=128).difference(holes)
    for part in list(shape.geoms) if hasattr(shape,'geoms') else [shape]:records.append((part,[a['layer']],None))
  ends=[pp['R_S'+phase,'pin2']['pcb_port_id'],pp['U_DRV','EP']['pcb_port_id']]
  for pid in ends:
   shape=g.pad_shape(pads[pid]).difference(holes)
   for part in list(shape.geoms) if hasattr(shape,'geoms') else [shape]:records.append((part,['top'],pid))
  for i,n in enumerate(['V_G'+phase,'V_STAR_'+phase]):
   if missing==i:continue
   v=via[n];records.append((g.pad_shape(v).difference(g.pad_shape(v,True)),v['layers'],None))
  parent=list(range(len(records)))
  def find(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  for i,(poly,ls,_) in enumerate(records):
   for j,(other,ls2,_) in enumerate(records[:i]):
    if set(ls)&set(ls2) and poly.intersection(other).area>1e-10:parent[find(j)]=find(i)
  return bool(set.intersection(*[{find(i) for i,r in enumerate(records) if r[2]==pid} for pid in ends]))
 returns=[]
 for phase in 'AB':
  ts=[t for suffix in ['TOP','INNER','EP'] for t in group('RETURN_'+phase+'_'+suffix)];wire=length(ts);access=0 if phase=='A' else next(r['via_axis_access_mm'] for r in spec['returns'] if r['name']=='RETURN_B_TOP');depth=.035/2+.1164+.0152/2;total=wire+access+2*depth;upper=wire+access+2*.160
  assert return_connected(phase) and all(not return_connected(phase,missing=i) for i in [0,1]) and not return_connected(phase,narrow=True);assert total<=5 and upper<=5
  returns.append({'phase':phase,'actual_wire_mm':wire,'annulus_end_to_axis_access_mm':access,'conducted_top_to_inner1_barrel_mm':depth,'conducted_barrels':2,'finished_stack_centerline_mm':total,'engineering_depth_upper_bound_mm':.160,'conditional_upper_total_mm':upper,'unchanged_maximum_mm':5,'actual_width_mm':.6,'isolated_phase_connected_after_drill_subtraction':True,'missing_barrel_and_narrow_wire_rejected':True,'stack_tolerances_confirmed':False})
 accepted=resolve_copper_nets(json.load(open('artifacts/final-source.circuit.json')));assert hashlib.sha256(Path('artifacts/final-source.circuit.json').read_bytes()).hexdigest()=='fe986e028cb398ebf3ed7fcbd9fd5dd8133b64c80aeac673c0540aa5c98cf06b';_,_,_,_,oldpcs=index(accepted)
 for name in ['J_PD','J_DATA','J_MOTOR','U_ENCODER','C_ENCODER','C_ENCODER_BULK']:
  for field in ['center','rotation','layer']:assert pcs[name][field]==oldpcs[name][field],(name,field)
 for typ,fields in [('pcb_board',['width','height','thickness','num_layers','min_trace_width','min_trace_to_pad_edge_clearance','min_board_edge_clearance','min_via_pad_diameter']),('pcb_hole',['x','y','hole_diameter']),('pcb_keepout',['center','radius','layers'])]:assert [{k:e.get(k) for k in fields} for e in b if e['type']==typ]==[{k:e.get(k) for k in fields} for e in accepted if e['type']==typ],typ
 cu=g.inspect(str(path))
 if require_clean:assert cu['geometric_clearance_pass']
 return {'input_sha256':hashlib.sha256(raw).hexdigest(),'four_actual_pad_pickups':pickups,'planar_wire_lengths_mm':lengths,'actual_ground_returns':returns,'fixed_mechanics_match_accepted':True,'accepted_source_unchanged':True,'independent':{k:len(cu[k]) for k in ['shorts','clearance_violations','drill_spacing_violations','hole_trace_violations','board_edge_violations','screw_keepout_violations','disconnected_nets']},'geometric_clearance_pass':cu['geometric_clearance_pass'],'full_controller_promoted':False,'manufacturing_qualified':False},cu

def compare_fixed(before,after):
 before={e[e['type']+'_id']:e for e in before if e['type'] in ['pcb_trace','pcb_via']};after={e[e['type']+'_id']:e for e in after if e['type'] in ['pcb_trace','pcb_via']};return [k for k,e in before.items() if json.dumps(after.get(k),separators=(',',':'))!=json.dumps(e,separators=(',',':'))]
if __name__=='__main__':
 path=Path(sys.argv[1] if len(sys.argv)>1 else root/'current-coupon.circuit.json');report,cu=verify(path,require_clean=len(sys.argv)<3)
 if len(sys.argv)>2:
  case=Path(sys.argv[2]);before=json.load(open(case/'before.circuit.json'));after=json.load(open(path));changed=compare_fixed(before,after);assert not changed,changed;assert len([e for e in before if e['type']=='pcb_trace'])==32;assert len([e for e in before if e['type']=='pcb_via'])==20
  sources=json.load(open(case/'source-inputs.json'));assert all(hashlib.sha256(Path('experiments/anchored',n).read_bytes()).hexdigest()==h for n,h in sources.items()),'Source changed during native run';assert not any(e['net']=='CP1' for e in cu['disconnected_nets']);report['native_fixed_copper']={'whole_record_byte_equivalent':True,'serialized_record_sha256_before':hashlib.sha256(json.dumps([e for e in before if e['type'] in ['pcb_trace','pcb_via']],separators=(',',':')).encode()).hexdigest(),'serialized_record_sha256_after':hashlib.sha256(json.dumps([e for e in after if e['type'] in ['pcb_trace','pcb_via'] and any(z.get(z['type']+'_id')==e.get(e['type']+'_id') for z in before if z['type']==e['type'])],separators=(',',':')).encode()).hexdigest(),'trace_records':32,'via_records':20,'source_hashes_match':True,'CP1_connected':True,'bounded_native':json.load(open(case/'result.json'))}
  # Negative controls reject even one representable coordinate/width/net change.
  controls=[]
  for field in ['coordinate','width','net']:
   edited=copy.deepcopy(after);t=next(e for e in edited if e['type']=='pcb_trace')
   if field=='net':t['source_trace_id']='wrong-source'
   else:
    key='x' if field=='coordinate' else 'width';t['route'][0][key]=math.nextafter(t['route'][0][key],math.inf)
   assert compare_fixed(before,edited);controls.append(field)
  report['exact_record_mutation_controls']=controls
 out=path.with_suffix('.verification.json');out.write_text(json.dumps(report,indent=2)+'\n');path.with_suffix('.copper.json').write_text(json.dumps(cu,indent=2)+'\n');print(json.dumps({'path':str(path),'independent':report['independent'],'returns':report['actual_ground_returns'],'fixed':report.get('native_fixed_copper')},indent=2))
