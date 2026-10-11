"""Retain legal baseline copper and export it as fixed Freerouting seed geometry.

Supplier pads and source pin/net identities come from newly compiled source.
No old pad coordinates are replayed over relocated parts.
"""
import hashlib, importlib.util, json, pathlib, subprocess
from shapely.geometry import Point, LineString, Polygon, box
from shapely.strtree import STRtree

ROOT=pathlib.Path(__file__).resolve().parents[1]
source_bytes=(ROOT/'artifacts/final-source.circuit.json').read_bytes()
new=json.loads(source_bytes)
assert not any(e['type'].endswith('_error') for e in new), 'Source must pass before routing'
base_commit=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
proof_path=ROOT/'artifacts/same-side-routing-proof.json'
if proof_path.exists():base_commit=json.loads(proof_path.read_text())['baseline_github_commit']
old=json.loads(subprocess.check_output(['git','show',base_commit+':artifacts/board.circuit.json'],cwd=ROOT))
def by_type(j,t):return [e for e in j if e['type']==t]
def records(j,t):
    # These source records contain no PCB placement or routing coordinates.
    return sorted(json.dumps(e,sort_keys=True) for e in by_type(j,t))
for t in ['source_component','source_port','source_net','source_trace']:
    assert records(new,t)==records(old,t), f'Functional source record changed: {t}'
spec=importlib.util.spec_from_file_location('supplier_geometry',ROOT/'scripts/verify_supplier_connectivity.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sp={e['source_port_id']:e for e in by_type(new,'source_port')}
pp={e['pcb_port_id']:e for e in by_type(new,'pcb_port')}
pc={e['pcb_component_id']:e for e in by_type(new,'pcb_component')}
src={e['source_component_id']:e['name'] for e in by_type(new,'source_component')}
oldpc={e['pcb_component_id']:e for e in by_type(old,'pcb_component')}
moved={k for k,v in pc.items() if v['center']!=oldpc[k]['center'] or v['rotation']!=oldpc[k]['rotation']}
moved_ports={k for k,v in pp.items() if v['pcb_component_id'] in moved}
def key(e):
    if e['type'] in ['pcb_smtpad','pcb_plated_hole']:
        return sp.get(pp.get(e.get('pcb_port_id'),{}).get('source_port_id'),{}).get('subcircuit_connectivity_map_key')
    return e.get('subcircuit_connectivity_map_key')
layers=['top','inner1','inner2','bottom']
obstacles={l:[] for l in layers};owners={l:[] for l in layers}
def add(ls,shape,net=None):
    for l in ls:obstacles[l].append(shape);owners[l].append(net)
for e in new:
    if e['type'] in ['pcb_smtpad','pcb_plated_hole']:
        add(e.get('layers',[e.get('layer','top')]),g.geometry(e),key(e))
    elif e['type']=='pcb_keepout':
        c=e['center']
        assert e['shape']=='circle'
        add(e['layers'],Point(c['x'],c['y']).buffer(e['radius'],quad_segs=64))
    elif e['type']=='pcb_hole':
        add(layers,Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1,quad_segs=64))
trees={l:STRtree(obstacles[l]) for l in layers}
def legal(shape,ls,net,via=False):
    expanded=shape.buffer(.15-1e-6)
    for l in ls:
        for i in trees[l].query(expanded,predicate='intersects'):
            owner=owners[l][int(i)]
            if owner==net and owner is not None and not via:continue
            # Only the declared exposed-pad thermal vias may overlap pads.
            if via and owner==net and owner is not None:
                continue
            if expanded.intersection(obstacles[l][int(i)]).area>1e-9:return False
    return True
kept_vias=[];removed_via_centers=[]
thermal={(round(e['x'],4),round(e['y'],4)) for e in by_type(new,'pcb_smtpad')
         if e.get('width',0)>1 and e.get('height',0)>1 and src[pc[e['pcb_component_id']]['source_component_id']] in ['U_MCU','U_PD','U_DRV']}
for e in by_type(old,'pcb_via'):
    shape=Point(e['x'],e['y']).buffer(e['outer_diameter']/2,quad_segs=64)
    if legal(shape,e['layers'],key(e),via=True):kept_vias.append(e)
    else:removed_via_centers.append((e['x'],e['y']))
kept_traces=[];removed_traces=[]
for e in by_type(old,'pcb_trace'):
    connected=set(e.get('pcb_port_ids',[]))
    connected.update(p[k] for p in e['route'] for k in ['start_pcb_port_id','end_pcb_port_id'] if k in p)
    valid=not (connected&moved_ports)
    for a,b in zip(e['route'],e['route'][1:]):
        if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
            shape=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2,quad_segs=64)
            if not legal(shape,[a['layer']],key(e)):valid=False
    if any(p['route_type']=='wire' and any(abs(p['x']-x)<1e-5 and abs(p['y']-y)<1e-5 for x,y in removed_via_centers) for p in [e['route'][0],e['route'][-1]]):valid=False
    (kept_traces if valid else removed_traces).append(e)
seeds={'traces':kept_traces,'vias':kept_vias}
(ROOT/'artifacts/same-side-routing-seeds.json').write_text(json.dumps(seeds,indent=2)+'\n')
proof={'baseline_github_commit':base_commit,'new_source_sha256':hashlib.sha256(source_bytes).hexdigest(),
       'source_components_ports_nets_traces_identical':True,
       'moved_references':sorted(src[pc[k]['source_component_id']] for k in moved),
       'baseline_traces':len(by_type(old,'pcb_trace')),'retained_fixed_traces':len(kept_traces),'removed_affected_traces':len(removed_traces),
       'baseline_vias':len(by_type(old,'pcb_via')),'retained_vias':len(kept_vias),
       'retained_geometry_is_unmoved':True,'all_pours_will_be_regenerated':True}
(ROOT/'artifacts/same-side-routing-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
assert (ROOT/'artifacts/final-source.circuit.json').read_bytes()==source_bytes
print(json.dumps(proof,indent=2))
