"""Summarize geometric copper changes against the frozen v1.12.2 baseline."""
import hashlib,json,math,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
commit=subprocess.check_output(['git','rev-list','--max-parents=0','HEAD'],cwd=ROOT,text=True).strip()
old=json.loads(subprocess.check_output(['git','show',commit+':index.circuit.json'],cwd=ROOT))
path=ROOT/'artifacts/board.circuit.json';new=json.loads(path.read_text())
key=lambda e:e.get(e['type']+'_id')
before={key(e):e for e in old if e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour']}
after={key(e):e for e in new if e['type'] in ['pcb_trace','pcb_via','pcb_copper_pour']}
oldnets={e['subcircuit_connectivity_map_key']:e['name'] for e in old if e['type']=='source_net'}
newnets={e['subcircuit_connectivity_map_key']:e['name'] for e in new if e['type']=='source_net'}
def geom(e):
    if e['type']=='pcb_trace':
        return [{k:v for k,v in p.items() if k not in ['start_pcb_port_id','end_pcb_port_id']} for p in e['route']]
    if e['type']=='pcb_via':return {k:e.get(k) for k in ['x','y','hole_diameter','outer_diameter','layers']}
    return e['brep_shape']
def describe(e,nets):return {'id':key(e),'type':e['type'],'net':nets.get(e.get('subcircuit_connectivity_map_key'))}
removed=[describe(e,oldnets) for k,e in before.items() if k not in after]
added=[describe(e,newnets) for k,e in after.items() if k not in before]
changed=[{'id':k,'type':e['type'],'net':newnets.get(e.get('subcircuit_connectivity_map_key'))} for k,e in after.items() if k in before and geom(e)!=geom(before[k])]
allowed={'GND','PD_VDD','PD_VHV','PD_CFG'}
assert all(row['net'] in allowed for row in removed+added+changed),'Unrelated copper geometry was changed.'
routes=[]
for e in new:
    if e['type']!='pcb_trace' or key(e) in before:continue
    lengths={}
    for a,b in zip(e['route'],e['route'][1:]):
        if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
            layer=a['layer'];lengths[layer]=lengths.get(layer,0)+math.hypot(a['x']-b['x'],a['y']-b['y'])
    routes.append({**describe(e,newnets),'length_mm_by_layer':lengths,'minimum_wire_width_mm':min(p['width'] for p in e['route'] if p['route_type']=='wire')})
report={'baseline_commit':commit,'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'unrelated_copper_geometry_preserved':True,'unchanged_trace_geometry_count':sum(e['type']=='pcb_trace' and k in after and geom(e)==geom(after[k]) for k,e in before.items()),'removed':removed,'added':added,'modified_geometry':changed,'new_routes':routes}
(ROOT/'artifacts/ch224a-migration/pcb-diff.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'unrelated_copper_geometry_preserved':True,'unchanged_trace_geometry_count':report['unchanged_trace_geometry_count'],'removed':len(removed),'added':len(added),'modified':len(changed)}))
