"""Clear existing ground pours only around added/changed migration copper.

Unchanged pour records retain their bytes; changed polygons retain their original
boundaries except the local 0.20 mm clearances. No global refill or reroute.
"""
import hashlib,json,pathlib,subprocess
from shapely.geometry import Polygon,Point,LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
import verify_supplier_connectivity as g

root=g.ROOT
baseline_commit=subprocess.check_output(['git','rev-list','--max-parents=0','HEAD'],cwd=root,text=True).strip()
old=json.loads(subprocess.check_output(['git','show',baseline_commit+':index.circuit.json'],cwd=root))
oldids={e.get(e['type']+'_id'):e for e in old}
oldsp={e['source_port_id']:e for e in old if e['type']=='source_port'}
oldpp={e['pcb_port_id']:e for e in old if e['type']=='pcb_port'}
ground=next(k for k,v in g.nets.items() if v=='GND')
cuts={l:[] for l in ['top','inner1','inner2','bottom']}
for e in g.j:
    typ=e['type'];ident=e.get(typ+'_id')
    if g.key(e)==ground:continue
    if typ=='pcb_smtpad':
        prev=oldids.get(ident)
        oldkey=oldsp.get(oldpp.get(e.get('pcb_port_id'),{}).get('source_port_id'),{}).get('subcircuit_connectivity_map_key')
        if prev and oldkey==g.key(e):continue
        cuts[e.get('layer','top')].append(g.geometry(e).buffer(.20001,quad_segs=16))
    elif typ=='pcb_via' and (ident not in oldids or any(e.get(k)!=oldids[ident].get(k) for k in ['x','y','outer_diameter','hole_diameter','subcircuit_connectivity_map_key'])):
        for l in e['layers']:cuts[l].append(Point(e['x'],e['y']).buffer(e['outer_diameter']/2+.20001,quad_segs=16))
    elif typ=='pcb_trace' and (ident not in oldids or e.get('route')!=oldids[ident].get('route') or e.get('subcircuit_connectivity_map_key')!=oldids[ident].get('subcircuit_connectivity_map_key')):
        for a,b in zip(e['route'],e['route'][1:]):
            if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
                cuts[a['layer']].append(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2+.20001,quad_segs=16))
cuts={l:unary_union(v) for l,v in cuts.items()}
changes=[];out=[]
for e in g.j:
    if e['type']!='pcb_copper_pour' or g.key(e)!=ground:
        out.append(e);continue
    b=e['brep_shape'];points=lambda r:[(p['x'],p['y']) for p in r['vertices']]
    original=Polygon(points(b['outer_ring']),[points(r) for r in b.get('inner_rings',[])])
    modified=original.difference(cuts[e['layer']])
    if original.symmetric_difference(modified).area<1e-10:
        out.append(e);continue
    assert modified.difference(original).area<1e-10,'Migration must not add unrelated ground copper.'
    pieces=[modified] if modified.geom_type=='Polygon' else [p for p in modified.geoms if p.geom_type=='Polygon']
    vertices=lambda ring:[{'x':round(x,6),'y':round(y,6)} for x,y in list(ring.coords)[:-1]]
    for i,p in enumerate(pieces):
        if p.area<1e-8:continue
        p=orient(p,sign=-1)
        out.append({**e,'pcb_copper_pour_id':e['pcb_copper_pour_id']+('' if i==0 else '_ch224a_'+str(i)),
                    'brep_shape':{'outer_ring':{'vertices':vertices(p.exterior)},'inner_rings':[{'vertices':vertices(r)} for r in p.interiors]}})
    changes.append({'id':e['pcb_copper_pour_id'],'layer':e['layer'],'removed_area_mm2':original.difference(modified).area,'pieces':len(pieces)})
g.j[:]=out
# Clearance slots can split padless pieces from a formerly grounded polygon.
# Keep only pieces physically joined to a real GND terminal through copper/vias.
elements,roots=g.groups(ground)
grounded={r for e,r in zip(elements,roots) if e.get('pcb_port_id')}
orphans={e[e['type']+'_id'] for e,r in zip(elements,roots) if r not in grounded}
assert all(e['type']=='pcb_copper_pour' for e,r in zip(elements,roots) if r not in grounded),'Unexpected orphan ground trace/via requires explicit review.'
g.j[:]=[e for e in g.j if e.get(e['type']+'_id') not in orphans]
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
(root/'artifacts/ch224a-migration/ground-clearance.json').write_text(json.dumps({'clearance_mm':.20,'global_refill':False,'changes':changes,'padless_ground_polygons_removed':sorted(orphans),'board_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest()},indent=2)+'\n')
print('Cleared',len(changes),'existing ground polygons only at new migration copper.')
