"""Group saved copper collisions by the actual unplaced part and native terminal net."""
from pathlib import Path
import json,collections
from model import *
first=read('artifacts/iteration-6/first-causes.json');groups={}
for e in first['full_33_shorts_and_39_spacing']['findings']:
 n=e['unplaced_component'];row=groups.setdefault(n,{'original_pose':poses[n],'nets':sorted({q.get('subcircuit_connectivity_map_key','unconnected') for q in sp.values() if names[q['source_component_id']]==n}),'collisions':[]});row['collisions'].append({k:e[k] for k in ['a_ref','a_net','b_ref','b_net','clearance_mm','required_mm','short']})
netnames={e['subcircuit_connectivity_map_key']:e['name'] for e in b if e['type']=='source_net' and e.get('subcircuit_connectivity_map_key')}
for v in groups.values():v['nets']=[netnames.get(x,x) for x in v['nets']]
cc=court_conflicts(courts);r={'saved_head':'76db864634bfcfc97056d582e968288dde5f12a6','copper_spacing_findings':39,'shorts_included':33,'actual_unplaced_parts':len(groups),'by_unplaced_part':groups,'all_top_courtyard_conflicts':cc,'additional_unplaced_parts_in_courtyard_conflicts':sorted({e[k] for e in cc for k in ['a','b'] if e[k] not in groups and e[k] not in read('experiments/compact/candidate-poses.json')})};Path('artifacts/iteration-7/collision-groups.json').write_text(json.dumps(r,indent=2)+'\n');print('Grouped',len(groups),'unplaced parts;',len(cc),'courtyard conflicts')
