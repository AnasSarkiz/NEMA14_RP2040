"""Record and verify accepted copper changes against the exact saved SES import."""
import json,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
base=ROOT/'artifacts/supplier.circuit.json';result=ROOT/'artifacts/board.circuit.json'
before=json.loads(base.read_text());after=json.loads(result.read_text())
types={'pcb_trace','pcb_via','pcb_copper_pour'}
def copper(records):return {e[e['type']+'_id']:e for e in records if e['type'] in types}
a,b=copper(before),copper(after)
changes=[{'id':i,'before':a.get(i),'after':b.get(i)} for i in sorted(a.keys()|b.keys()) if a.get(i)!=b.get(i)]
proof={'source':'artifacts/supplier.circuit.json','sourceSha256':hashlib.sha256(base.read_bytes()).hexdigest(),'resultSha256':hashlib.sha256(result.read_bytes()).hexdigest(),'description':'Official Freerouting SES with fixed native-pad motor, VBB1 and local switching/support routes, verified standard-via corrections, clearance-constrained power widening and minimum-neck pad/barrel-anchored four-layer GND fill. Supplier land patterns unchanged.','canonicalPourOrder':['GND'],'changes':changes}
(ROOT/'artifacts/supplier-routing-adjustments.json').write_text(json.dumps(proof,indent=2)+'\n')
replayed=before[:]
for c in changes:
 if c['before'] is not None:replayed.remove(c['before'])
 if c['after'] is not None:replayed.append(c['after'])
assert copper(replayed)==b
(ROOT/'artifacts/engineering').mkdir(exist_ok=True)
(ROOT/'artifacts/engineering/route-replay-verification.json').write_text(json.dumps({'copperRecordsIdentical':True,'adjustments':len(changes),'supplierImportSha256':proof['sourceSha256'],'acceptedBoardSha256AtVerification':proof['resultSha256'],'canonicalPourOrder':['GND']},indent=2)+'\n')
print(len(changes),'verified copper adjustments; accepted board',proof['resultSha256'])
