"""Explicit hand-chosen fanouts; audit candidate coordinates, never search routes."""
import json, pathlib, copy, math
from shapely.geometry import Point, LineString
import verify_supplier_connectivity as g

def port(ref,pin):
    return next(p for p in g.ports.values() if g.src[g.comp[p['pcb_component_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['pin_number']==pin)

# These explicit coordinates are reviewed edits to the official-router result.
edits=[
 ('BUZZER_PWM','U_MCU',4,[(1.775064,1.399921),(1.775064,1.45),(3.2,1.45)]),
 ('BUZZER_PWM','R_BUZZER_GATE',1,[(-8.067184,-4.3),(-8.4,-3.65)]),
]

sourceids={e['name']:e['source_net_id'] for e in g.j if e['type']=='source_net'}
keys={v:k for k,v in g.nets.items()}
records=[];findings=[]
for net,ref,pin,coords in edits:
    p=port(ref,pin);assert math.dist(coords[0],(p['x'],p['y']))<.0001,(ref,pin,p,coords[0])
    coords[0]=(p['x'],p['y']);key=keys[net];identity=f'diagnostics_manual_{ref}_{pin}';width=.30 if net=='V3V3' and ref!='U_MCU' else .16
    own={e['pcb_smtpad_id'] for e in g.j if e['type']=='pcb_smtpad' and e.get('pcb_port_id')==p['pcb_port_id']}
    samples=[('trace','top',LineString(coords).buffer(width/2))]+([('via',layer,Point(coords[-1]).buffer(.2))for layer in ['top','inner2','bottom']])
    for kind,layer,shape in samples:
        for e in g.j+records:
            typ=e['type'];geo=None
            if typ in ['pcb_smtpad','pcb_plated_hole'] and layer in e.get('layers',[e.get('layer','top')]):
                if g.key(e)==key:
                    if kind=='via' and shape.intersects(g.geometry(e)):findings.append({'edit':identity,'kind':'via-in-pad','pad':e.get('pcb_smtpad_id')})
                    continue
                geo=g.geometry(e)
            elif typ=='pcb_via' and layer in e['layers'] and g.key(e)!=key:geo=Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
            elif typ=='pcb_trace' and g.key(e)!=key:
                geos=[LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)for a,b in zip(e['route'],e['route'][1:])if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']==layer]
                if geos:
                    from shapely.ops import unary_union
                    geo=unary_union(geos)
            if geo is not None and shape.distance(geo)<.1499:findings.append({'edit':identity,'kind':kind,'layer':layer,'foreign':e.get(typ+'_id'),'net':g.nets.get(g.key(e)),'gapMm':shape.distance(geo)})
    common={'source_net_id':sourceids[net],'subcircuit_connectivity_map_key':key,'subcircuit_id':'subcircuit_source_group_0'}
    records.extend([{'type':'pcb_trace','pcb_trace_id':identity,'route':[{'route_type':'wire','x':x,'y':y,'width':width,'layer':'top',**({'start_pcb_port_id':p['pcb_port_id']}if i==0 else{})}for i,(x,y) in enumerate(coords)],'pcb_port_ids':[p['pcb_port_id']],**common}, {'type':'pcb_via','pcb_via_id':identity+'_via','x':coords[-1][0],'y':coords[-1][1],'hole_diameter':.2,'outer_diameter':.4,'layers':['top','inner1','inner2','bottom'],'from_layer':'top','to_layer':'bottom','tented_on_top':True,'tented_on_bottom':True,**common}])
(g.ROOT/'artifacts/diagnostics/manual-fanout-candidate.json').write_text(json.dumps({'coordinates':edits,'findings':findings},indent=2)+'\n')
print(json.dumps(findings,indent=2))
hard=[f for f in findings if f['kind']=='via-in-pad' or f.get('foreign','').startswith(('pcb_smtpad','pcb_plated_hole','diagnostics_manual'))]
assert not hard,'Manually adjust coordinates before applying: '+str(hard)
protected={'A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','PD_VBUS','PD_CC1','PD_CC2','PD_LEGACY_DATA','DATA_CC1','DATA_CC2','PD_VDD','USB_DP','USB_DM','MCU_DP','MCU_DM','GND'}
ground_ids={f['foreign'] for f in findings if f.get('net')=='GND'}
assert all(i.startswith('diagnostics_') for i in ground_ids), 'Preserve reviewed ground barrels and legacy copper'
release={f['net'] for f in findings if f.get('net') is not None and f['net']!='GND'}
assert not release&protected,'Do not rip up reviewed power/USB/ground copper'
colliders={f.get('foreign')for f in findings}
removed=[e for e in g.j if e['type'] in ['pcb_trace','pcb_via'] and e.get(e['type']+'_id')in colliders]
(g.ROOT/'artifacts/diagnostics/manual-fanout-ripup.json').write_text(json.dumps({'releasedNets':sorted(release),'removedCopper':removed,'reason':'Explicit manually chosen fanouts require rerouting obstructing signal copper with the official router; no connectivity acceptance is claimed.'},indent=2)+'\n')
g.j=[e for e in g.j if e['type']!='pcb_copper_pour' and e not in removed]+records
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
print('Applied',len(edits),'explicit reviewed fanouts; official router must complete their other ends.')
