"""Explicit hand-chosen fanouts; audit candidate coordinates, never search routes."""
import json, pathlib, copy, math
from shapely.geometry import Point, LineString
import verify_supplier_connectivity as g

def port(ref,pin):
    return next(p for p in g.ports.values() if g.src[g.comp[p['pcb_component_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['pin_number']==pin)

# These explicit coordinates are reviewed edits to the official-router result.
edits=[
 ('TEMP_ALERT_N','U_MCU',6,[(1.7751,.6001),(1.1,.6001),(.925,.425),(.925,.325)]),
 ('DIR','U_MCU',9,[(1.7751,-.6001),(1.3,-.6001),(1.1,-.55)]),
 ('V3V3','U_MCU',10,[(1.7751,-.9999),(.9719,-.9999),(.9,-1.2)]),
 ('PD_GOOD','U_MCU',13,[(1.7751,-2.2),(1.05,-2.2)]),
 ('QSPI_SCLK','U_MCU',52,[(4.200002,3.425063),(4.200002,4.15)]),
 ('QSPI_SD0','U_MCU',53,[(3.8,3.4251),(3.8,2.98),(3.875,2.905),(3.875,2.1)]),
 ('QSPI_SD2','U_MCU',54,[(3.3999,3.4251),(3.3999,2.75)]),
 ('QSPI_SD1','U_MCU',55,[(2.9999,3.4251),(2.9999,2.98),(2.925,2.905),(2.925,2.1)]),
 ('ENABLE_N','U_DRV',2,[(-3.2,-7.8491),(-3.8817,-7.8491),(-3.8817,-8.0735),(-4.01,-8.37)]),
 ('VCP','U_DRV',6,[(-3.1999950000000004, -9.850632999999998), (-3.299999999999999, -9.95), (-3.625, -9.95), (-3.6499999999999986, -9.975), (-3.6999999999999993, -9.975), (-3.75, -10.024999999999999), (-3.7749999999999986, -10.024999999999999), (-3.924999999999999, -10.175), (-3.924999999999999, -13.975), (-3.9499999999999993, -14), (-3.9499999999999993, -14.075), (-4, -14.125), (-4, -14.15), (-4.199999999999999, -14.35), (-4.199976, -15)]),
]
sourceids={e['name']:e['source_net_id'] for e in g.j if e['type']=='source_net'}
keys={v:k for k,v in g.nets.items()}
records=[];findings=[]
for net,ref,pin,coords in edits:
    p=port(ref,pin);assert math.dist(coords[0],(p['x'],p['y']))<.0001,(ref,pin,p,coords[0])
    coords[0]=(p['x'],p['y']);key=keys[net];identity=f'diagnostics_manual_{ref}_{pin}'
    own={e['pcb_smtpad_id'] for e in g.j if e['type']=='pcb_smtpad' and e.get('pcb_port_id')==p['pcb_port_id']}
    samples=[('trace','top',LineString(coords).buffer(.08))]+([] if (ref,pin)==('U_DRV',6) else [('via',layer,Point(coords[-1]).buffer(.2))for layer in ['top','inner2','bottom']])
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
    records.extend([{'type':'pcb_trace','pcb_trace_id':identity,'route':[{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'top',**({'start_pcb_port_id':p['pcb_port_id']}if i==0 else{})}for i,(x,y) in enumerate(coords)],'pcb_port_ids':[p['pcb_port_id']],**common}, {'type':'pcb_via','pcb_via_id':identity+'_via','x':coords[-1][0],'y':coords[-1][1],'hole_diameter':.2,'outer_diameter':.4,'layers':['top','inner1','inner2','bottom'],'from_layer':'top','to_layer':'bottom','tented_on_top':True,'tented_on_bottom':True,**common}])
records=[e for e in records if e.get('pcb_via_id')!='diagnostics_manual_U_DRV_6_via']
(g.ROOT/'artifacts/diagnostics/manual-fanout-candidate.json').write_text(json.dumps({'coordinates':edits,'findings':findings},indent=2)+'\n')
print(json.dumps(findings,indent=2))
hard=[f for f in findings if f['kind']=='via-in-pad' or f.get('foreign','').startswith(('pcb_smtpad','pcb_plated_hole','diagnostics_manual'))]
assert not hard,'Manually adjust coordinates before applying: '+str(hard)
protected={'A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','PD_VBUS','PD_CC1','PD_CC2','PD_LEGACY_DATA','DATA_CC1','DATA_CC2','PD_VDD','USB_DP','USB_DM','MCU_DP','MCU_DM','GND'}
release={f['net'] for f in findings if f.get('net') is not None}
assert not release&protected,'Do not rip up reviewed power/USB/ground copper'
removed=[e for e in g.j if e['type'] in ['pcb_trace','pcb_via'] and g.nets.get(g.key(e)) in release]
(g.ROOT/'artifacts/diagnostics/manual-fanout-ripup.json').write_text(json.dumps({'releasedNets':sorted(release),'removedCopper':removed,'reason':'Explicit manually chosen fanouts require rerouting obstructing signal copper with the official router; no connectivity acceptance is claimed.'},indent=2)+'\n')
g.j=[e for e in g.j if e['type']!='pcb_copper_pour' and e not in removed]+records
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
print('Applied',len(edits),'explicit reviewed fanouts; official router must complete their other ends.')
