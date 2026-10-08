"""Apply one source-native cap relocation and two bounded route changes.
Authoritative source generated first; every unrelated physical record preserved.
"""
import json,pathlib,hashlib,copy
ROOT=pathlib.Path(__file__).resolve().parents[1];p=ROOT/'artifacts/board.circuit.json';before_bytes=p.read_bytes();before=json.loads(before_bytes);fresh=json.loads((ROOT/'artifacts/final-source.circuit.json').read_text());snap=(ROOT/'artifacts/rp-cp1-restoration-input.circuit.json').read_bytes();assert before_bytes==snap,'Parent copper changed during held mutation scope'
source=next(e for e in fresh if e['type']=='source_component' and e['name']=='C_CP');sid=source['source_component_id'];cid=next(e['pcb_component_id'] for e in fresh if e['type']=='pcb_component' and e['source_component_id']==sid)
def iscap(e):return (e.get('pcb_component_id')==cid and e['type'].startswith('pcb_')) or (e['type']=='cad_component' and e.get('source_component_id')==sid)
def ident(e):return e.get(e['type']+'_id')
replacement={ident(e):e for e in fresh if iscap(e)};assert set(replacement)=={ident(e) for e in before if iscap(e)}
j=[replacement[ident(e)] if iscap(e) else copy.deepcopy(e) for e in before]
proof={'inputSha256':hashlib.sha256(before_bytes).hexdigest(),'freshSourceSha256':hashlib.sha256((ROOT/'artifacts/final-source.circuit.json').read_bytes()).hexdigest(),'sourcePlacementChange':{'reference':'C_CP','from':[-4.7,-11.4,270],'to':[-5.1,-11.4,270],'unchangedNativeFootprint':True},'freshNativePhysicalRecordsReplaced':list(replacement),'unrelatedPhysicalRecordsUnchanged':True}
assert [e for e in j if not iscap(e)]==[e for e in before if not iscap(e)]
# Replace the driver-enable fanout while preserving every other net's copper.
remove={'supplier_repair_control_fanout_U_DRV_ENABLE_N','supplier_repair_control_fanout_U_DRV_ENABLE_N_via'};assert remove<={ident(e) for e in j};j=[e for e in j if ident(e) not in remove]
proposal=json.loads((ROOT/'artifacts/rp-cp1-single-cap-move-proposal.json').read_text());adds=proposal['additions']
for e in adds:
 field=e['type']+'_id';e[field]=e[field].replace('supplier_repair_CP1_fanout_U_DRV_ENABLE_N','supplier_repair_relocated_U_DRV_ENABLE_N')
j+=adds
original=next(e for e in json.loads((ROOT/'artifacts/rp-control-fanout-input.circuit.json').read_text()) if e.get('pcb_trace_id')=='engineering_local_12');assert not any(e.get('pcb_trace_id')=='engineering_local_12' for e in j);j.append(copy.deepcopy(original))
sp={e['source_port_id']:e for e in fresh if e['type']=='source_port'};ports={e['pcb_port_id']:e for e in fresh if e['type']=='pcb_port'};capports={pid:e for pid,e in ports.items() if e['pcb_component_id']==cid};endpoint_changes=[]
for e in j:
 if e['type']!='pcb_trace':continue
 for node in e['route']:
  pid=node.get('start_pcb_port_id',node.get('end_pcb_port_id'))
  if pid in capports:
   port=capports[pid];old=[node['x'],node['y']];node['x']=port['x'];node['y']=port['y'];endpoint_changes.append({'trace':e['pcb_trace_id'],'capPin':sp[port['source_port_id']]['name'],'old':old,'new':[port['x'],port['y']]})
assert {e['capPin'] for e in endpoint_changes}=={'pin1','pin2'}
proof.update({'removedRouteIds':sorted(remove),'addedRouteIds':[ident(e) for e in adds]+['engineering_local_12'],'capEndpointsMovedToExactNativePadCentres':endpoint_changes,'routeChangesOnly':['Driver EN fanout replacement','CP1 original top route restoration with centered cap endpoint','CP2 centered cap endpoint'],'unrelatedCopperUnchanged':True})
changed=remove|{ident(e) for e in adds}|{'engineering_local_12'}|{e['trace'] for e in endpoint_changes};cu=lambda records:{ident(e):e for e in records if e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour'] and ident(e) not in changed};assert cu(j)==cu(before)
p.write_text(json.dumps(j,indent=2)+'\n');proof['resultBeforePresentationSyncSha256']=hashlib.sha256(p.read_bytes()).hexdigest();(ROOT/'artifacts/validation/rp-cp1-bounded-fix-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
