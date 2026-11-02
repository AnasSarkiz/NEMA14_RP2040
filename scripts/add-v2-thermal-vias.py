"""Add one grounded thermal barrel inside each of the three exposed pads."""
import json
import hashlib
import verify_supplier_connectivity as g
from shapely.geometry import Point, LineString
from shapely.ops import unary_union

ground=next(e for e in g.j if e['type']=='source_net' and e['name']=='GND')
key=ground['subcircuit_connectivity_map_key']
sites=[]
for reference in ['U_MCU','U_PD','U_DRV']:
    candidates=[e for e in g.j if e['type']=='pcb_smtpad' and g.src[g.comp[e['pcb_component_id']]['source_component_id']]==reference and g.key(e)==key and g.geometry(e).area>1]
    assert len(candidates)==1,(reference,len(candidates))
    pad=candidates[0];shape=g.geometry(pad)
    obstacles=[]
    for e in g.j:
        if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and g.key(e)!=key:
            obstacles.append(g.geometry(e))
        elif e['type']=='pcb_via' and g.key(e)!=key:
            obstacles.append(Point(e['x'],e['y']).buffer(e['outer_diameter']/2))
        elif e['type']=='pcb_trace' and g.key(e)!=key:
            for a,b in zip(e['route'],e['route'][1:]):
                if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
                    obstacles.append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
    foreign=unary_union(obstacles)
    a,b,c,d=shape.bounds
    choices=[Point(a+.3+i*.05,b+.3+j*.05) for i in range(max(1,int((c-a-.6)/.05)+1)) for j in range(max(1,int((d-b-.6)/.05)+1))]
    choices.sort(key=lambda p:p.distance(shape.centroid))
    point=next((p for p in choices if shape.buffer(-.05).covers(p.buffer(.25)) and p.buffer(.25).distance(foreign)>=.15+.005),None)
    assert point is not None,('No legal exposed-pad thermal site',reference)
    uid='v2_thermal_'+reference
    if not any(e.get('pcb_via_id')==uid for e in g.j):
        g.j.append({'type':'pcb_via','pcb_via_id':uid,'x':point.x,'y':point.y,
                    'hole_diameter':.3,'outer_diameter':.5,
                    'layers':['top','inner1','inner2','bottom'],'from_layer':'top','to_layer':'bottom',
                    'source_net_id':ground['source_net_id'],'subcircuit_connectivity_map_key':key,
                    'subcircuit_id':'subcircuit_source_group_0','tented_on_top':False,'tented_on_bottom':True})
    sites.append({'reference':reference,'pcb_via_id':uid,'pcb_pad_id':pad['pcb_smtpad_id'],
                  'x':point.x,'y':point.y,'outer_diameter':.5,'hole_diameter':.3})
for e in g.j:
    if e['type']=='pcb_board':e['is_via_in_pad_allowed']=True
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
(g.ROOT/'artifacts/v2/routing/thermal-via-sites.json').write_text(json.dumps({'sites':sites,'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'policy':'Only these three grounded thermal vias are permitted in exposed pads; all other via-in-pad remains forbidden.'},indent=2)+'\n')
print(json.dumps(sites))
