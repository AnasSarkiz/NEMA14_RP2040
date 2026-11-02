"""Export/import an isolated V2 Freerouting trial with exact supplier geometry.

Inner1 is reserved for the eventual ground reference. No V1 seeds, routes,
manufacturing files or geometry overrides are loaded.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from shapely.geometry import Point
import verify_supplier_connectivity as geometry

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode',choices=['export','import'])
parser.add_argument('--source',type=Path,default=ROOT/'artifacts/v2/source.circuit.json')
parser.add_argument('--directory',type=Path,default=ROOT/'artifacts/v2/routing')
args=parser.parse_args()
out=args.directory;out.mkdir(parents=True,exist_ok=True)
data=json.loads(args.source.read_text())
assert not any(e['type'].endswith('_error') for e in data),'Fix source errors first'
board=next(e for e in data if e['type']=='pcb_board')
assert (board['width'],board['height'],board['num_layers'])==(34.5,34.5,4)
ports={e['pcb_port_id']:e for e in data if e['type']=='pcb_port'}
source_ports={e['source_port_id']:e for e in data if e['type']=='source_port'}
nets={e['subcircuit_connectivity_map_key']:e['name'] for e in data if e['type']=='source_net'}
for e in source_ports.values():
    key=e.get('subcircuit_connectivity_map_key')
    if key and key not in nets:nets[key]='DIRECT_'+key
net_keys={n:k for k,n in nets.items()}
net_ids={e['name']:e['source_net_id'] for e in data if e['type']=='source_net'}
trace_ids={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in data if e['type']=='source_trace'}
layers={'top':'F.Cu','inner2':'In2.Cu','bottom':'B.Cu'}
all_layers=['top','inner1','inner2','bottom']
pads=[e for e in data if e['type'] in ['pcb_smtpad','pcb_plated_hole']]
quote=lambda s:json.dumps(str(s))
um=lambda x:f'{x*1000:.6f}'

if args.mode=='export':
    padstacks=[];images=[];placements=[];pinmap={};netpins={};number=0
    for component in [e for e in data if e['type']=='pcb_component']:
        cid=component['pcb_component_id'];cx,cy=component['center']['x'],component['center']['y'];pins=[]
        for pad in [p for p in pads if p['pcb_component_id']==cid]:
            number+=1
            pid=pad.get('pcb_port_id');port=ports.get(pid,{})
            key=source_ports.get(port.get('source_port_id'),{}).get('subcircuit_connectivity_map_key')
            name=nets.get(key,'NC_'+str(number));pin='p'+str(number);stack='pad'+str(number)
            on_layers=[pad['layer']] if pad['type']=='pcb_smtpad' else layers
            # Export the actual rotated world-space contour relative to the pad.
            # A polygon is exact for rectangular pads. Rounded pad boundaries
            # use polygon approximations; final independent CAM checks remain
            # mandatory before manufacturing.
            shape=geometry.geometry(pad)
            x=port.get('x',pad['x']);y=port.get('y',pad['y'])
            coords=' '.join(um(v) for px,py in shape.exterior.coords for v in [px-x,py-y])
            descriptions=' '.join(f'(shape (polygon {layers[l]} 0 {coords}))' for l in on_layers)
            padstacks.append(f'(padstack {quote(stack)} {descriptions} (attach off))')
            pins.append(f'(pin {quote(stack)} {quote(pin)} {um(x-cx)} {um(y-cy)})')
            identity=cid+'-'+pin;netpins.setdefault(name,[]).append(identity)
            pinmap[identity]={'pcb_port_id':pid,'net':name,'key':key}
        images.append(f'(image {quote(cid)} '+ ' '.join(pins)+')')
        placements.append(f'(component {quote(cid)} (place {quote(cid)} {um(cx)} {um(cy)} front 0))')
    keepouts=[]
    for i,e in enumerate(data):
        if e['type']=='pcb_keepout':
            assert e['shape']=='circle'
            for l in layers:
                c=e['center'];keepouts.append(f'(keepout {quote("head"+str(i)+l)} (circle {layers[l]} {um(2*e["radius"])} {um(c["x"])} {um(c["y"])}))')
        elif e['type']=='pcb_hole':
            for l in layers:
                if e['hole_shape']=='circle':
                    shape=f'(circle {layers[l]} {um(e["hole_diameter"]+.2)} {um(e["x"])} {um(e["y"])})'
                else:
                    # Explicit rotated slot capsule, enlarged by 0.10 mm.
                    from shapely.affinity import rotate
                    from shapely.geometry import LineString
                    w,h=e['hole_width'],e['hole_height'];dx,dy=((w-h)/2,0) if w>=h else (0,(h-w)/2)
                    capsule=rotate(LineString([(e['x']-dx,e['y']-dy),(e['x']+dx,e['y']+dy)]).buffer(min(w,h)/2+.1,quad_segs=32),e.get('ccw_rotation',0),origin=(e['x'],e['y']))
                    shape=f'(polygon {layers[l]} 0 '+' '.join(um(v) for p in capsule.exterior.coords for v in p)+')'
                keepouts.append(f'(keepout {quote("npth"+str(i)+l)} {shape})')
    # 0.6/0.3 mm through vias meet the V2 board's actual drill minimum.
    via='(padstack "via600" '+' '.join(f'(shape (circle {l} 600))' for l in layers.values())+' (attach off))'
    power={'PD_VBUS','DATA_VBUS','LOGIC_IN','V3V3','V1V1','A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','BUCK_SW','BUZZER_SINK'}
    classes=[]
    for name,selected,width in [('signal',set(netpins)-power,160),('power',set(netpins)&power,300)]:
        classes.append(f'(class {quote(name)} '+' '.join(quote(n) for n in sorted(selected))+' (circuit (use_via "via600")) '+f'(rule (width {width}) (clearance 150)))')
    # Reserve an additional 0.10 mm inside the real outline so the router's
    # 0.15 mm clearance provides the required 0.25 mm copper-to-edge margin.
    limit=board['width']/2-.1
    outline=' '.join(um(v) for p in [(-limit,-limit),(limit,-limit),(limit,limit),(-limit,limit),(-limit,-limit)] for v in p)
    text='(pcb nema14_v2 (parser (string_quote ") (space_in_quoted_tokens on)) (resolution um 10) (unit um)'
    text+='(structure '+' '.join(f'(layer {l} (type signal) (property (index {i})))' for i,l in enumerate(layers.values()))
    text+=f' (boundary (path pcb 0 {outline})) (via "via600") (rule (width 160) (clearance 150)) '+' '.join(keepouts)+')'
    text+='(placement '+' '.join(placements)+')(library '+' '.join(images+padstacks+[via])+')'
    text+='(network '+' '.join(f'(net {quote(n)} (pins '+' '.join(pp)+'))' for n,pp in netpins.items())+' '+ ' '.join(classes)+')(wiring))\n'
    (out/'wago.dsn').write_text(text)
    (out/'freerouting-map.json').write_text(json.dumps({'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'dsn_sha256':hashlib.sha256(text.encode()).hexdigest(),'physical_pads':number,'net_groups':len(netpins),'pinmap':pinmap,'routed_layers':list(layers),'reserved_layer':'inner1','via_outer_mm':.6,'via_hole_mm':.3},indent=2)+'\n')
    print(json.dumps({'physical_pads':number,'net_groups':len(netpins),'layers':list(layers),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest()}))
else:
    def parse(text):
        tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text);stack=[];root=[]
        for token in tokens:
            if token=='(':stack.append([])
            elif token==')':
                node=stack.pop();(stack[-1] if stack else root).append(node)
            else:stack[-1].append(json.loads(token) if token.startswith('"') else token)
        if stack or len(root)!=1:raise ValueError('Malformed SES')
        return root[0]
    children=lambda node,tag:[v for v in node if isinstance(v,list) and v and v[0]==tag]
    metadata=json.loads((out/'freerouting-map.json').read_text())
    assert metadata['source_sha256']==hashlib.sha256(args.source.read_bytes()).hexdigest(),'Placement changed after DSN export'
    assert metadata['dsn_sha256']==hashlib.sha256((out/'wago.dsn').read_bytes()).hexdigest(),'DSN changed after export'
    routes=children(parse((out/'wago.ses').read_text()),'routes')[0]
    resolution=children(routes,'resolution')[0];assert resolution[1]=='um'
    scale=1000*float(resolution[2]);reverse={v:k for k,v in layers.items()}
    result=list(data);trace_count=0;via_count=0
    for net in children(children(routes,'network_out')[0],'net'):
        name=net[1]
        if name.startswith('NC_'):continue
        assert name in net_keys,'Unknown routed net: '+name
        key=net_keys[name];identity={'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0'}
        if name in net_ids:identity['source_net_id']=net_ids[name]
        if key in trace_ids:identity['source_trace_id']=trace_ids[key]
        for wire in children(net,'wire'):
            path=children(wire,'path')[0];layer=reverse[path[1]];width=float(path[2])/scale
            xy=list(map(float,path[3:]));assert len(xy)%2==0
            points=[{'route_type':'wire','x':xy[i]/scale,'y':xy[i+1]/scale,'width':width,'layer':layer} for i in range(0,len(xy),2)]
            if len(points)<2:continue
            contacts=[]
            for point,tag in [(points[0],'start_pcb_port_id'),(points[-1],'end_pcb_port_id')]:
                for pad in pads:
                    pid=pad.get('pcb_port_id');port=ports.get(pid,{})
                    if source_ports.get(port.get('source_port_id'),{}).get('subcircuit_connectivity_map_key')!=key:continue
                    if layer not in pad.get('layers',[pad.get('layer','top')]):continue
                    if geometry.geometry(pad).buffer(1e-6).covers(Point(point['x'],point['y'])):
                        point[tag]=pid;contacts.append(pid);break
            trace_count+=1
            result.append({'type':'pcb_trace','pcb_trace_id':f'v2_free_trace_{trace_count}','route':points,'pcb_port_ids':sorted(set(contacts)),**identity})
        for via in children(net,'via'):
            assert via[1]=='via600'
            via_count+=1
            result.append({'type':'pcb_via','pcb_via_id':f'v2_free_via_{via_count}','x':float(via[2])/scale,'y':float(via[3])/scale,'hole_diameter':.3,'outer_diameter':.6,'layers':all_layers,'from_layer':'top','to_layer':'bottom','tented_on_top':True,'tented_on_bottom':True,**identity})
    target=out/'freerouted.circuit.json';target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'traces':trace_count,'vias':via_count,'source_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
