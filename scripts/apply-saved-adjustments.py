"""Replay the reviewed local copper edits without running another autorouter."""
import json, pathlib

root = pathlib.Path(__file__).resolve().parents[1] / 'artifacts'
patch = json.loads((root / 'saved-copper-adjustments.json').read_text())
base = json.loads((root / patch['base']).read_text())
source = json.loads((root / patch['finalSource']).read_text())
removed = set(patch['removedCopperIds'])
copper = [e for e in base if e['type'] in ['pcb_trace', 'pcb_via']
          and e.get(e['type'] + '_id') not in removed]
copper += patch['insertedCopper']
annotations = [e for e in source if e['type'] not in
               ['pcb_trace', 'pcb_via', 'pcb_copper_pour']
               and not e['type'].endswith('_error')]
for e in annotations:
    if e['type'] == 'pcb_board':
        e['is_via_in_pad_allowed'] = True  # only three EP vias; check.ts checks the rest
(root / 'board.circuit.json').write_text(json.dumps(annotations + copper, indent=2) + '\n')
print('Replayed', len(patch['insertedCopper']), 'saved copper edits')
