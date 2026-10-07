"""Replay recorded supplier routing corrections against the exact SES import."""
import json,pathlib
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json'
j=json.loads((root/'artifacts/supplier.circuit.json').read_text());proof=json.loads((root/'artifacts/supplier-routing-adjustments.json').read_text());ids={e.get(e['type']+'_id'):e for e in j}
for c in proof['changes']:
 assert ids.get(c['id'])==c['before'],c['id']+' input mismatch'
 if c['before'] is not None:j.remove(ids[c['id']])
 if c['after'] is not None:j.append(c['after'])
path.write_text(json.dumps(j,indent=2)+'\n');print('Replayed',len(proof['changes']),'PCB adjustments; refresh presentation and run checks.')
