"""Route and freeze critical local connections before general Freerouting.

Uses source-native polygon/pill/rotated pad geometry; never changes footprints.
Records actual paths and includes them as fixed DSN wires. Run after
export-supplier-router.py, then import-supplier-session.py supplier.
"""
import json, math, heapq, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw
import verify_supplier_connectivity as g

ROOT=pathlib.Path(__file__).resolve().parents[1]
g.j=json.loads((ROOT/'artifacts/final-source.circuit.json').read_text())
j=g.j
initial_seeds=json.loads((ROOT/'artifacts/supplier-seeds.circuit.json').read_text()) if (ROOT/'artifacts/supplier-seeds.circuit.json').exists() else []
j.extend(initial_seeds)
g.sp={e['source_port_id']:e for e in j if e['type']=='source_port'}
g.ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'}
g.comp={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'}
g.src={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'}
netrecords={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}
source_traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
STEP=.025;LOW=-17.5;N=1401
xy=lambda x,y:(round((x-LOW)/STEP),round((y-LOW)/STEP))
world=lambda p:(LOW+p[0]*STEP,LOW+p[1]*STEP)

def port(selector):
    ref,pin=selector.split('.')
    return next(e for e in g.ports.values() if g.src[g.comp[e['pcb_component_id']]['source_component_id']]==ref and g.sp[e['source_port_id']]['name']==pin)

def blocked(net,width):
    im=Image.new('L',(N,N));d=ImageDraw.Draw(im)
    def add(shape):
        shape=shape.buffer(.15+width/2+.008)
        for p in ([shape] if shape.geom_type=='Polygon' else shape.geoms):
            d.polygon([xy(x,y) for x,y in p.exterior.coords],fill=1)
    for e in j:
        typ=e['type']
        if typ in ['pcb_smtpad','pcb_plated_hole'] and g.key(e)!=net: add(g.geometry(e))
        elif typ=='pcb_trace' and g.key(e)!=net:
            for a,b in zip(e['route'],e['route'][1:]):
                if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='top': add(g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
        elif typ=='pcb_via' and g.key(e)!=net: add(g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
        elif typ=='pcb_hole':add(g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1))
        elif typ=='pcb_keepout':
            add(g.keepout_geometry(e))
    border=math.ceil((.3+width/2)/STEP)
    d.rectangle([0,0,N-1,border],fill=1);d.rectangle([0,N-1-border,N-1,N-1],fill=1)
    d.rectangle([0,0,border,N-1],fill=1);d.rectangle([N-1-border,0,N-1,N-1],fill=1)
    return np.asarray(im,dtype=np.bool_)

connections=[
 ('U_DRV.CP1','C_CP.pin1',.16),('U_DRV.CP2','C_CP.pin2',.16),
 ('U_DRV.VCP','C_VCP.pin1',.16),('U_DRV.VREG','C_VREG.pin1',.16),
 ('U_DRV.SENSE1','R_SA.pin1',.30),('U_DRV.SENSE2','R_SB.pin1',.30),
 ('U_DRV.VBB2','C_VM.pin1',.30),
 ('U_DRV.VDD','C_DRV_LOGIC.pin1',.16),('U_MCU.IOVDD10','C_IO10.pin1',.16),
 ('U_BUCK.VIN','C_BUCK_IN.pin1',.30),
 ('U_BUCK.BST','C_BOOTSTRAP.pin1',.16),('U_BUCK.SW','C_BOOTSTRAP.pin2',.30),
 ('U_BUCK.SW','L_BUCK.pin1',.30),
 ('L_BUCK.pin2','C_BUCK_OUT1.pin1',.30),('L_BUCK.pin2','C_BUCK_OUT2.pin1',.30),
 ('U_BUCK.FB','C_BUCK_OUT1.pin1',.16),
]
seeds=initial_seeds[:];report=[]
for first,second,width in connections:
    p,q=port(first),port(second);net=g.sp[p['source_port_id']]['subcircuit_connectivity_map_key']
    assert net==g.sp[q['source_port_id']]['subcircuit_connectivity_map_key']
    mask=blocked(net,width);start=xy(p['x'],p['y']);goal=xy(q['x'],q['y'])
    if mask[start[1],start[0]] or mask[goal[1],goal[0]]:
        raise ValueError(f'No legal {width}mm escape for {first}/{second}')
    h=lambda s:math.hypot(s[0]-goal[0],s[1]-goal[1])
    heap=[(h(start),0,start)];best={start:0};prev={};end=None;expanded=0
    while heap:
        _,cost,s=heapq.heappop(heap)
        if cost!=best.get(s):continue
        if s==goal:end=s;break
        expanded+=1
        if expanded>1000000:break
        x,y=s
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nx,ny=x+dx,y+dy
            if not(0<=nx<N and 0<=ny<N) or mask[ny,nx]:continue
            if dx and dy and (mask[y,nx] or mask[ny,x]):continue
            t=(nx,ny);nc=cost+(math.sqrt(2) if dx and dy else 1)
            if nc<best.get(t,float('inf'))-1e-8:best[t]=nc;prev[t]=s;heapq.heappush(heap,(nc+h(t),nc,t))
    assert end is not None,f'No local path for {first}/{second}'
    nodes=[end]
    while nodes[-1]!=start:nodes.append(prev[nodes[-1]])
    nodes.reverse();slim=[nodes[0]]
    for i in range(1,len(nodes)-1):
        a,b,c=nodes[i-1:i+2]
        if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):slim.append(b)
    slim.append(nodes[-1]);coords=[world(n) for n in slim];coords[0]=(p['x'],p['y']);coords[-1]=(q['x'],q['y'])
    route=[{'route_type':'wire','x':x,'y':y,'width':width,'layer':'top'} for x,y in coords]
    route[0]['start_pcb_port_id']=p['pcb_port_id'];route[-1]['end_pcb_port_id']=q['pcb_port_id']
    e={'type':'pcb_trace','pcb_trace_id':'engineering_local_'+str(len(seeds)+1),'route':route,'source_net_id':netrecords[net]['source_net_id'],'source_trace_id':source_traces[net],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[p['pcb_port_id'],q['pcb_port_id']]}
    j.append(e);seeds.append(e)
    length=sum(math.dist(a,b) for a,b in zip(coords,coords[1:]))
    report.append({'from':first,'to':second,'net':netrecords[net]['name'],'widthMm':width,'lengthMm':length,'layer':'top','viaCount':0,'expandedNodes':expanded})
    print(first,second,round(length,3),'mm',flush=True)

# Fixed DSN geometry prevents subsequent global optimization from lengthening
# charge-pump, sense and immediate decoupling paths. Original SES is retained.
dsn=ROOT/'artifacts/supplier-input.dsn';text=dsn.read_text();wires=[]
for e in seeds:
    if e['type']!='pcb_trace' or not e['pcb_trace_id'].startswith('engineering_local_'):continue
    name=netrecords[g.key(e)]['name'];r=e['route']
    wires.append('(wire (path F.Cu '+f'{r[0]["width"]*1000:.4f} '+' '.join(f'{p[k]*1000:.4f}' for p in r for k in ['x','y'])+') (net '+json.dumps(name)+') (type fix))')
assert '(wiring ' in text
dsn.write_text(text.replace('(wiring ','(wiring '+' '.join(wires)+' ',1))
(ROOT/'artifacts/supplier-seeds.circuit.json').write_text(json.dumps(seeds,indent=2)+'\n')
(ROOT/'artifacts/engineering-local-routes.json').write_text(json.dumps({'gridMm':STEP,'minimumClearanceMm':.15,'roundingGuardMm':.008,'routes':report},indent=2)+'\n')
