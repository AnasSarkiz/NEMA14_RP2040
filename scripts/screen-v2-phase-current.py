"""Screen the actual fixed current setting against internal phase copper.

IPC-2221 is a conservative sizing estimate, not a substitute for measured
temperature, ground-return qualification or a manufacturing release.
"""
import hashlib,json,math,sys
from pathlib import Path
from v2_route_io import g

parts={e['name']:e for e in g.j if e['type']=='source_component'}
ohms=lambda name:float(parts[name]['resistance'])
high,low=ohms('R_REF_H'),ohms('R_REF_L')
nominal_vref=3.3*low/(high+low)
max_vref=3.3*1.05*(low*1.01)/(high*.99+low*1.01)
current=max(max_vref/(8*ohms(n)*.99) for n in ['R_SA','R_SB'])
policy=json.loads((g.ROOT/'src/layer-routing-policy.json').read_text())
width=.3;thickness=.0175;rise=20
capacity=.024*rise**.44*((width/.0254)*(thickness/.0254))**.725
lengths={n:0. for n in ['A_DRV_PLUS','B_DRV_PLUS','A_PLUS','B_PLUS','A_MINUS','B_MINUS']}
undersized=[]
for e in g.j:
    if e['type']!='pcb_trace':continue
    name=g.nets.get(g.key(e))
    if name not in lengths:continue
    for a,b in zip(e['route'],e['route'][1:]):
        if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='inner1':
            lengths[name]+=math.hypot(a['x']-b['x'],a['y']-b['y'])
            if min(a['width'],b['width'])<width-1e-6:undersized.append(e['pcb_trace_id'])
resistance=.01724*(policy['maximum_total_phase_inner1_length_mm']/1000)/(width*thickness)
report={'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),
        'scope':'Fixed-current and copper sizing estimate; not thermal or electrical release',
        'supply_assumption_V':[3.3,3.3*1.05],'resistor_tolerance_assumption':.01,
        'nominal_current_A':{n:nominal_vref/(8*ohms(n)) for n in ['R_SA','R_SB']},
        'maximum_trip_current_A':current,'internal_trace_width_mm':width,
        'internal_copper_thickness_assumption_mm':thickness,'estimated_rise_budget_C':rise,
        'IPC2221_internal_current_capacity_A':capacity,
        'bounded_section_resistance_ohm':resistance,'bounded_section_peak_loss_W':current**2*resistance,
        'inner1_phase_lengths_mm':lengths,'undersized_inner1_phase_traces':undersized,
        'passed':current<=capacity and not undersized and max(lengths.values())<=policy['maximum_total_phase_inner1_length_mm']+1e-6,
        'fabrication_ready':False}
(g.ROOT/'artifacts/v2/routing/phase-current-screen.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(not report['passed'])
