"""Route independent >=0.30 mm winding trunks, then Kelvin shunt pickups.

Run with --reset to replace only the four inline-shunt net copper trees.
Supplier pads and every other net remain fixed. Full physical/native/CAM
qualification is required afterward, including the functional Kelvin audit.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=Path(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--source=')),ROOT/'artifacts/v2/routing/freerouted.circuit.json'))
directory=source.parent
reset_nets={q.split('=',1)[1] for q in sys.argv if q.startswith('--reset-net=')}
assert reset_nets <= {'A_DRV_PLUS','B_DRV_PLUS','A_PLUS','B_PLUS'}
if '--reset' in sys.argv or reset_nets:
    j=json.loads(source.read_text());nets={e['name']:e['subcircuit_connectivity_map_key'] for e in j if e['type']=='source_net'}
    keys={nets[n] for n in (reset_nets or {'A_DRV_PLUS','B_DRV_PLUS','A_PLUS','B_PLUS'})}
    traces=[e for e in j if e['type']=='pcb_trace' and e['pcb_trace_id'].startswith('v2_escape_')
            and set(e.get('pcb_port_ids',[])) & {'pcb_port_226','pcb_port_228'}]
    sites={(q['x'],q['y']) for t in traces for q in t['route'] if q['route_type']=='via'}
    retained={t['pcb_trace_id'] for t in traces}
    retained.update(e['pcb_via_id'] for e in j if e['type']=='pcb_via' and e.get('subcircuit_connectivity_map_key') in keys
                    and any(abs(e['x']-x)<1e-6 and abs(e['y']-y)<1e-6 for x,y in sites))
    old=[e for e in j if e['type'] in ['pcb_trace','pcb_via'] and e.get('subcircuit_connectivity_map_key') in keys]
    (directory/'winding-copper-before-reset.json').write_text(json.dumps(old,indent=2)+'\n')
    removed=[e[e['type']+'_id'] for e in old if e[e['type']+'_id'] not in retained]
    j=[e for e in j if e['type']!='pcb_copper_pour' and e.get(e['type']+'_id') not in removed]
    source.write_text(json.dumps(j,indent=2)+'\n')
    print('Reset winding copper:',len(removed),'records; retained driver fanouts:',len(retained),flush=True)
if '--reset-only' in sys.argv:
    assert '--reset' in sys.argv or reset_nets
    raise SystemExit(0)

common=[sys.executable,str(ROOT/'scripts/route-v2-repair.py'),'--source',str(source),'--fast-grid',
        '--protect-signals','--max-ripped-traces=0','--via-pad-mm=.5','--grid-step-mm=.025',
        '--grid-margin-mm=.003','--max-expanded=10000000','--search-weight=1',
        '--repair-log='+str(directory/'winding-repairs.json')]
for phase,pin,motor,amp in [('A',24,1,'U_IA'),('B',26,3,'U_IB')]:
    for net,start,number,goal,goal_pin in [(phase+'_DRV_PLUS','U_DRV',pin,'R_SHUNT_'+phase,1),
                                         (phase+'_PLUS','R_SHUNT_'+phase,2,'J_MOTOR',motor)]:
        print('MAIN',net,flush=True)
        subprocess.run(common+['--net='+net,'--start-ref='+start,'--start-pad='+str(number),
                       '--goal-ref='+goal,'--goal-pad='+str(goal_pin),'--avoid-ref='+amp,'--phase-bridges'],check=True,cwd=ROOT)
    for net,pin,goal_pin in [(phase+'_DRV_PLUS',2,1),(phase+'_PLUS',3,2)]:
        print('KELVIN',net,flush=True)
        kelvin=[q if not q.startswith('--via-pad-mm=') else '--via-pad-mm=.45' for q in common]
        subprocess.run(kelvin+['--net='+net,'--start-ref='+amp,'--start-pad='+str(pin),
                       '--goal-ref=R_SHUNT_'+phase,'--goal-pad='+str(goal_pin),'--kelvin',
                       '--layers=top,inner2,bottom'],check=True,cwd=ROOT)
print('Winding routing pass saved',hashlib.sha256(source.read_bytes()).hexdigest(),flush=True)
