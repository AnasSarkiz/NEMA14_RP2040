"""Verify the native one-shunt singular/plural crossing evidence, without changing Core."""
from pathlib import Path
import sys,json,hashlib,importlib.util
sys.path.insert(0,'scripts')
from routing_geometry import resolve_copper_nets,pad_cut_topology
from native_sources import source_owner_names
s=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
root=Path('artifacts/iteration-6');cases={};before_routes=None;controls=[]
for mode in ['singular','plural','protected-plural']:
 p=root/('ab-'+mode);a=json.load(open(p/'before.circuit.json'));b=json.load(open(p/'native.circuit.json'));before={e['pcb_trace_id']:e for e in a if e['type']=='pcb_trace'};after={e['pcb_trace_id']:e for e in b if e['type']=='pcb_trace'};assert len(before)==4
 routes={k:e['route'] for k,e in before.items()}
 if before_routes is None:before_routes=routes
 else:assert routes==before_routes,'A/B starts from different physical copper'
 changed=[k for k,v in before.items() if after.get(k)!=v];cu=g.inspect(str(p/'native.circuit.json'));(p/'copper.json').write_text(json.dumps(cu,indent=2)+'\n');st={e['source_trace_id']:e for e in b if e['type']=='source_trace'};widths={}
 for k,v in before.items():
  name=st[v['source_trace_id']]['name'];expected=.16 if name.startswith('KELVIN') else .45;actual=[e for e in b if e['type']=='pcb_trace' and e.get('source_trace_id')==v['source_trace_id']];w=sorted({n['width'] for e in actual for n in e['route'] if n['route_type']=='wire'});assert w==[expected],(mode,name,w);widths[name]=w
 srj=json.load(open(p/'native-input.srj.json'));cases[mode]={'before_sha256':hashlib.sha256((p/'before.circuit.json').read_bytes()).hexdigest(),'after_sha256':hashlib.sha256((p/'native.circuit.json').read_bytes()).hexdigest(),'native_editable_prior_traces':len(srj.get('traces',[])),'authored_trace_record_changes':changed,'actual_widths_mm':widths,'independent':{k:len(cu[k]) for k in ['shorts','clearance_violations','disconnected_nets','board_edge_violations']},'geometry_pass':cu['geometric_clearance_pass'],'full_coupon_connectivity':cu['full_board_connectivity_pass'],'record':json.load(open(p/'receipt.json'))}
 if mode!='plural':assert not changed and cu['geometric_clearance_pass'] and cu['full_board_connectivity_pass'],mode
 else:assert changed,'Negative plural control failed to reproduce mutation'
 for stage,j in [('before',a),('after',b)]:
  if stage=='before' and mode!='singular':continue
  j=resolve_copper_nets(j);owners=source_owner_names(j);sp={e['source_port_id']:e for e in j if e['type']=='source_port'};ports={(owners[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in j if e['type']=='pcb_port'};pads={e['pcb_port_id']:e for e in j if e['type']=='pcb_smtpad'}
  for pole,pin in [('POS','pin1'),('NEG','pin2')]:
   shunt=ports['R_SHUNT_A',pin];amp=ports['U_IA','IN_'+pole];power=ports['P_A_'+pole,'pin1'];key=sp[shunt['source_port_id']]['subcircuit_connectivity_map_key'];r=pad_cut_topology(j,key,shunt['pcb_port_id'],amp['pcb_port_id'],power['pcb_port_id'],g.pad_shape(pads[shunt['pcb_port_id']]),'top',g.pad_shape);controls.append({'mode':mode,'stage':stage,'pole':pole,**r})
report={'same_authored_route_bytes_before_native_routing':True,'cases':cases,'actual_pad_cuts':controls,'core_modified':False,'unmerged_stack_used':False,'upstream_references':['https://github.com/tscircuit/core/issues/5462','https://github.com/tscircuit/core/pull/5473','https://github.com/tscircuit/core/pull/5475'],'interpretation':'Singular native copper is fixed; equivalent plural copper is editable and one power branch mutates. The diagnostic fixed-input adapter preserves plural records. This is board-specific evidence, not proof that the unmerged PR has a plural-path regression.'};(root/'ab-verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v['authored_trace_record_changes'] for k,v in cases.items()});print('Pad-cut controls',len(controls),'passing',sum(x['actual_shunt_pad_is_required_pickup'] for x in controls))
