"""Use the board's legal 0.45/0.30 mm signal vias without losing pad connectivity.

Thermal and motor/power vias retain their larger annuli. Every accepted change
preserves the exact physical-pad partition of its net on all four layers.
"""
import json,hashlib
from v2_route_io import g

power={'GND','PD_VBUS','DATA_VBUS','LOGIC_IN','V3V3','V1V1','VREG','VCP','BUCK_SW',
       'A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','BUZZER_SINK'}
def signature(net):
    elements,roots=g.groups(net);islands={}
    for e,r in zip(elements,roots):
        if e.get('pcb_port_id'):islands.setdefault(r,set()).add(e['pcb_port_id'])
    return sorted(sorted(v) for v in islands.values())

changed=[];retained=[]
for net,name in g.nets.items():
    if name in power:continue
    vias=[v for v in g.j if v['type']=='pcb_via' and g.key(v)==net
          and v['outer_diameter']==.5 and v['hole_diameter']==.3]
    if not vias:continue
    before=signature(net)
    for v in vias:v['outer_diameter']=.45
    if signature(net)!=before:
        for v in vias:v['outer_diameter']=.5
        for v in vias:
            v['outer_diameter']=.45
            if signature(net)!=before:v['outer_diameter']=.5;retained.append(v['pcb_via_id'])
    for v in vias:
        if v['outer_diameter']!=.45:continue
        changed.append({'via':v['pcb_via_id'],'net':name,'x':v['x'],'y':v['y']})
        for t in g.j:
            if t['type']!='pcb_trace' or g.key(t)!=net:continue
            for p in t['route']:
                if p['route_type']=='via' and abs(p['x']-v['x'])<1e-6 and abs(p['y']-v['y'])<1e-6:
                    p['via_diameter']=.45
    assert signature(net)==before

g.path.write_text(json.dumps(g.j,indent=2)+'\n')
report={'drill_mm':.3,'signal_pad_mm':.45,'minimum_annulus_mm':.075,
        'physical_pad_partitions_unchanged':True,'changed':changed,'retained':retained,
        'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest()}
(g.ROOT/'artifacts/v2/routing/compacted-vias.json').write_text(json.dumps(report,indent=2)+'\n')
print('Compacted',len(changed),'signal vias; retained',len(retained),'needed larger contacts')
