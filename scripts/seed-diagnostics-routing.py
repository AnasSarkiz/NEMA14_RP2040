"""Rebind reviewed copper to fresh source; remove obstructed segments for routing.

This is a geometry-preserving seed importer, not a routing algorithm. New copper
is produced by native tscircuit/official Freerouting or explicit manual edits.
"""
import json, pathlib, copy, hashlib
from shapely.geometry import Point, Polygon, LineString, box
from shapely.affinity import rotate

root = pathlib.Path(__file__).resolve().parents[1]
from diagnostics_baseline import BASELINE_COMMIT, baseline_bytes
old = json.loads(baseline_bytes('artifacts/board.circuit.json'))
fresh = json.loads((root / 'artifacts/final-source.circuit.json').read_text())
assert not any(e['type'].endswith('_error') for e in fresh), 'Fix source errors first'

def maps(j):
    components = {e['source_component_id']: e['name'] for e in j if e['type']=='source_component'}
    sourceports = {e['source_port_id']: (components[e['source_component_id']], e['pin_number']) for e in j if e['type']=='source_port'}
    ports = {e['pcb_port_id']: sourceports[e['source_port_id']] for e in j if e['type']=='pcb_port'}
    nets = {e['subcircuit_connectivity_map_key']: e['name'] for e in j if e['type']=='source_net'}
    signatures = {}
    for e in j:
        if e['type']=='source_port' and e.get('subcircuit_connectivity_map_key'):
            signatures.setdefault(e['subcircuit_connectivity_map_key'], []).append(sourceports[e['source_port_id']])
    for key, pins in signatures.items():
        if key not in nets: nets[key] = tuple(sorted(pins))
    return components, ports, nets

oc, op, on = maps(old); nc, np, nn = maps(fresh)
inverse = {name:key for key,name in nn.items()}
keys = {key:inverse[name] for key,name in on.items() if name in inverse}
newports = {signature:pid for pid,signature in np.items()}
portids = {pid:newports[signature] for pid,signature in op.items() if signature in newports}
netids = {e['subcircuit_connectivity_map_key']:e['source_net_id'] for e in fresh if e['type']=='source_net'}
traceids = {e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in fresh if e['type']=='source_trace'}
sp = {e['source_port_id']:e for e in fresh if e['type']=='source_port'}
pp = {e['pcb_port_id']:e for e in fresh if e['type']=='pcb_port'}

def geometry(p):
    if p.get('shape')=='polygon':return Polygon([(v['x'],v['y']) for v in p['points']]).buffer(0)
    x,y=p['x'],p['y'];w=p.get('width',p.get('outer_width',p.get('outer_diameter',p.get('radius',0)*2)));h=p.get('height',p.get('outer_height',p.get('outer_diameter',p.get('radius',0)*2)))
    if p.get('shape')=='circle':g=Point(x,y).buffer(w/2)
    elif p.get('shape') in ['pill','rotated_pill']:
        dx,dy=((w-h)/2,0) if w>=h else (0,(h-w)/2);g=LineString([(x-dx,y-dy),(x+dx,y+dy)]).buffer(min(w,h)/2)
    else:g=box(x-w/2,y-h/2,x+w/2,y+h/2)
    return rotate(g,p.get('ccw_rotation',0),origin=(x,y))

oldpads={op[e['pcb_port_id']]:e for e in old if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and e.get('pcb_port_id')}
newpads={np[e['pcb_port_id']]:e for e in fresh if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and e.get('pcb_port_id')}
changed={sig for sig,p in oldpads.items() if sig not in newpads or not geometry(p).equals_exact(geometry(newpads[sig]),1e-6)}
foreign=[(geometry(p),sp[pp[p['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key'),p.get('layers',[p.get('layer','top')])) for p in newpads.values()]
cuts=[(geometry(oldpads[s]),on.get(next((e.get('subcircuit_connectivity_map_key') for e in old if e['type']=='source_port' and (oc[e['source_component_id']],e['pin_number'])==s),'')),oldpads[s].get('layers',[oldpads[s].get('layer','top')])) for s in changed]

def rebind(e):
    key=keys.get(e.get('subcircuit_connectivity_map_key'))
    if key is None:return None
    e=copy.deepcopy(e);e['subcircuit_connectivity_map_key']=key
    for field,mapping in [('source_net_id',netids),('source_trace_id',traceids)]:
        e.pop(field,None)
        if key in mapping:e[field]=mapping[key]
    e['pcb_port_ids']=[portids[p] for p in e.get('pcb_port_ids',[]) if p in portids]
    return e

seeds=[];removed=[]
for original in old:
    if original['type'] not in ['pcb_trace','pcb_via']:continue
    e=rebind(original)
    if e is None:removed.append({'id':original.get(original['type']+'_id'),'reason':'removed net'});continue
    key=e['subcircuit_connectivity_map_key']
    protected={'A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','PD_VBUS','PD_CC1','PD_CC2','PD_LEGACY_DATA','DATA_CC1','DATA_CC2','PD_VDD','USB_DP','USB_DM','MCU_DP','MCU_DM'}
    if e['type']=='pcb_trace' and nn[key] not in protected:
        removed.append({'id':e['pcb_trace_id'],'reason':'released for official router to reconnect revised logic/diagnostic layout'});continue
    if e['type']=='pcb_via' and nn[key] not in protected and nn[key]!='GND':
        removed.append({'id':e['pcb_via_id'],'reason':'released revised signal via'});continue
    if e['type']=='pcb_via':
        geo=Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
        blocked=any(k!=key and any(l in e['layers'] for l in layers) and geo.distance(g)<.1499 for g,k,layers in foreign)
        # A relocated exposed pad requires a freshly specified barrel.
        oldpd=next(c for c in old if c['type']=='pcb_component' and oc[c['source_component_id']]=='U_PD')
        newpd=next(c for c in fresh if c['type']=='pcb_component' and nc[c['source_component_id']]=='U_PD')
        moved=oldpd['center']!=newpd['center'] and Point(e['x'],e['y']).distance(Point(oldpd['center']['x'],oldpd['center']['y']))<.5
        if blocked or moved:removed.append({'id':e['pcb_via_id'],'reason':'new foreign pad clearance or moved exposed pad'});continue
        seeds.append(e);continue
    for i,(a,b) in enumerate(zip(e['route'],e['route'][1:])):
        if a['route_type']!= 'wire' or b['route_type']!='wire' or a['layer']!=b['layer']:continue
        geo=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
        blocked=any(k!=key and a['layer'] in layers and geo.distance(g)<.1499 for g,k,layers in foreign)
        stale=any(name==nn[key] and a['layer'] in layers and geo.intersects(g) for g,name,layers in cuts)
        if blocked or stale:removed.append({'id':e['pcb_trace_id'],'segment':i,'reason':'new foreign pad clearance' if blocked else 'changed supplier land pattern'});continue
        segment=copy.deepcopy(e);segment['pcb_trace_id'] += '_seed_'+str(i);segment['route']=[copy.deepcopy(a),copy.deepcopy(b)];segment['pcb_port_ids']=[]
        for point in segment['route']:
            for field in ['start_pcb_port_id','end_pcb_port_id']:
                oldid=point.pop(field,None)
                if oldid in portids and op[oldid] not in changed:
                    point[field]=portids[oldid];segment['pcb_port_ids'].append(portids[oldid])
        seeds.append(segment)

# Preserve the existing correctly specified barrels; relocate only a moved PD EP.
for p in newpads.values():
    signature=np[p['pcb_port_id']]
    if signature[0]=='U_PD' and p.get('width',0)>1 and p.get('height',0)>1 and signature in changed:
        key=sp[pp[p['pcb_port_id']]['source_port_id']]['subcircuit_connectivity_map_key']
        seeds.append({'type':'pcb_via','pcb_via_id':'diagnostics_pd_ep_ground','x':p['x'],'y':p['y'],'outer_diameter':.5,'hole_diameter':.25,'layers':['top','inner1','inner2','bottom'] if next(e for e in fresh if e['type']=='pcb_board')['num_layers']==4 else ['top','bottom'],'from_layer':'top','to_layer':'bottom','source_net_id':netids[key],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0','tented_on_top':True,'tented_on_bottom':True})

result=[e for e in fresh if e['type'] not in ['pcb_trace','pcb_via','pcb_copper_pour']]+seeds
(root/'artifacts/board.circuit.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'artifacts/diagnostics').mkdir(exist_ok=True)
(root/'artifacts/diagnostics/seed-report.json').write_text(json.dumps({'baselineCommit':BASELINE_COMMIT,'baselineSha256':hashlib.sha256(baseline_bytes('artifacts/board.circuit.json')).hexdigest(),'freshSourceSha256':hashlib.sha256((root/'artifacts/final-source.circuit.json').read_bytes()).hexdigest(),'changedPads':[list(s) for s in sorted(changed)],'retainedCopperRecords':len(seeds),'removed':removed,'routingComplete':False},indent=2)+'\n')
print('Retained',len(seeds),'copper segments/barrels; removed',len(removed),'obstructed or changed segments. Routing still required.')
