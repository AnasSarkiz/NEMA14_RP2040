"""Compare terminal rotations against the unchanged V2 placement.

Continuous rectangle exclusion proves the fixed-layout 90/270-degree no-fit
result. The 0.25 mm grid only selects an illustrative outward-facing candidate;
it does not prove a redesigned layout impossible. No main board file is edited.
"""
import hashlib, html
import json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box,Point
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
r=Path(__file__).resolve().parents[1];d=json.loads((r/'artifacts/v2/source.circuit.json').read_text());ns={e['source_component_id']:e['name'] for e in d if e['type']=='source_component'};pcs={e['pcb_component_id']:e for e in d if e['type']=='pcb_component'};courts={ns[pcs[e['pcb_component_id']]['source_component_id']]:Polygon([(p['x'],p['y']) for p in e['outline']]) for e in d if e['type']=='pcb_courtyard_outline' and e['layer']=='top'};motor=next(e for e in pcs.values() if ns[e['source_component_id']]=='J_MOTOR');orig=courts.pop('J_MOTOR');local=translate(orig,xoff=-motor['center']['x'],yoff=-motor['center']['y']);boundary=box(-17.25,-17.25,17.25,17.25);result=[]
for rot in [90,180,270]:
 poly=rotate(local,rot,origin=(0,0));a,b,c,dd=poly.bounds;cx=(a+c)/2;cy=(b+dd)/2;w=c-a;h=dd-b
 possible=box(-17.25-a,-17.25-b,17.25-c,17.25-dd);forbidden=[]
 for n,p in courts.items():
  l,bt,rr,t=p.bounds;assert abs(p.area-box(l,bt,rr,t).area)<1e-6
  forbidden.append(box(l-c,bt-dd,rr-a,t-b))
 free=possible.difference(unary_union(forbidden))
 xx=np.arange(math.ceil((-17.25-a)*4),math.floor((17.25-c)*4)+1)/4;yy=np.arange(math.ceil((-17.25-b)*4),math.floor((17.25-dd)*4)+1)/4;x,y=np.meshgrid(xx,yy);x=x.ravel();y=y.ravel();l=x+a;bt=y+b;rr=x+c;t=y+dd;legal=np.ones(len(x),bool)
 for hx in [-13,13]:
  for hy in [-13,13]:
   dx=np.maximum(np.maximum(l-hx,hx-rr),0);dy=np.maximum(np.maximum(bt-hy,hy-t),0);legal&=dx*dx+dy*dy>=3.2**2
 count=np.zeros(len(x),int);area=np.zeros(len(x))
 for n,p in courts.items():
  pl,pb,pr,pt=p.bounds;ar=np.maximum(0,np.minimum(rr,pr)-np.maximum(l,pl))*np.maximum(0,np.minimum(t,pt)-np.maximum(bt,pb));count+=ar>1e-7;area+=ar
 # Keep wire entry within 1mm of the corresponding edge, pointing outward.
 outward=rr>=16.25 if rot==90 else l<=-16.25 if rot==270 else t>=16.25
 legal&=outward
 inds=np.flatnonzero(legal);best=inds[np.lexsort((area[inds],count[inds]))[0]]
 p=translate(poly,xoff=float(x[best]),yoff=float(y[best]));collisions=sorted(n for n,o in courts.items() if p.intersection(o).area>1e-7)
 candidate={'rotation_deg':rot,'pcbX':float(x[best]),'pcbY':float(y[best]),'courtyard_bounds_mm':list(p.bounds),'colliding_components':collisions,'collision_count':len(collisions),'overlap_area_mm2':float(area[best]),'free_centre_region_area_mm2_before_screw_checks':free.area,'continuous_zero_overlap_location_exists':not free.is_empty,'minimization_grid_mm':.25,'wire_entry':'right' if rot==90 else 'left' if rot==270 else 'top'};result.append(candidate)


def fit(p):
 return {'board_outline_passed':boundary.buffer(1e-6).covers(p),
         'colliding_components':sorted(n for n,o in courts.items() if p.intersection(o).area>1e-7),
         'minimum_screw_head_clearance_mm':min(p.distance(Point(x,y))-3.2 for x in [-13,13] for y in [-13,13])}
centre=orig.centroid
old_centre=local.centroid
halfturn={'pcbX':centre.x+old_centre.x,'pcbY':centre.y+old_centre.y,'pcbRotation':180}
halfpoly=translate(rotate(local,180,origin=(0,0)),xoff=halfturn['pcbX'],yoff=halfturn['pcbY'])
halfturn.update(fit(halfpoly))
assert not halfturn['colliding_components'] and halfturn['board_outline_passed']
assert halfpoly.symmetric_difference(orig).area<1e-6
side=next(q for q in result if q['rotation_deg']==270)
sidepoly=translate(rotate(local,270,origin=(0,0)),xoff=side['pcbX'],yoff=side['pcbY'])
report={'baseline_source_sha256':hashlib.sha256((r/'artifacts/v2/source.circuit.json').read_bytes()).hexdigest(),
        'board_mm':[34.5,34.5],'courtyard_mm':[local.bounds[2]-local.bounds[0],local.bounds[3]-local.bounds[1]],
        'fixed_layout_rotation_screens':result,'half_turn_same_occupied_area':halfturn,
        'main_layout_changed':False,
        'scope':'2D fixed-layout rotation study, not a new routing or mechanical qualification. No free sideways location with all other parts fixed; this does not rule out a complete re-layout. The half-turn faces wires inward.'}
out=r/'artifacts/v2/rotation-study';out.mkdir(exist_ok=True,parents=True)
native=out/'half-turn.circuit.json'
if native.exists():
 native_data=json.loads(native.read_text())
 report['half_turn_native_source_sha256']=hashlib.sha256(native.read_bytes()).hexdigest()
 report['half_turn_native_access_warnings']=[e for e in native_data if e['type']=='pcb_connector_not_in_accessible_orientation_warning']
(out/'rotation-screen.json').write_text(json.dumps(report,indent=2)+'\n')
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 122 49" width="1830" height="735"><rect width="122" height="49" fill="#f8fafc"/><style>text{font-family:Arial,sans-serif}</style><text x="61" y="2.7" text-anchor="middle" font-size="1.35" fill="#18343b">WAGO 250-204 rotation study — unchanged surrounding placement</text>']
for i,(title,p,entry,desc) in enumerate([('Current — 0°',orig,'bottom','Wires face the board edge'),('180° — same occupied area',halfpoly,'top','Fits courtyards; wires face components'),('270° — sideways example',sidepoly,'left',str(side['collision_count'])+' component courtyards overlap')]):
 cx=21+i*40
 svg.append(f'<text x="{cx}" y="6" text-anchor="middle" font-size="1.1">{html.escape(title)}</text><g transform="translate({cx},25) scale(1,-1)"><rect x="-17.25" y="-17.25" width="34.5" height="34.5" fill="#e8f1eb" stroke="#214b39" stroke-width=".15"/>')
 for n,o in courts.items():
  clash=p.intersection(o).area>1e-7
  svg.append('<g><title>'+html.escape(n)+'</title><polygon points="'+' '.join(f'{x},{y}' for x,y in o.exterior.coords)+'" fill="'+('#efa4a4' if clash else '#ccd4db')+'" stroke="'+('#a21d25' if clash else '#53636e')+'" stroke-width=".05"/></g>')
 for hx in [-13,13]:
  for hy in [-13,13]:svg.append(f'<circle cx="{hx}" cy="{hy}" r="3.2" fill="none" stroke="#946444" stroke-width=".1" stroke-dasharray=".3,.2"/><circle cx="{hx}" cy="{hy}" r="1.6" fill="#f8fafc"/>')
 svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in p.exterior.coords)+'" fill="#55c7b9" fill-opacity=".65" stroke="#12695e" stroke-width=".18"/>')
 pc=p.centroid;svg.append(f'<g transform="translate({pc.x},{pc.y}) scale(1,-1)"><text text-anchor="middle" font-size="1.3" fill="#06493f">WAGO</text></g>')
 dx,dy={'bottom':(0,-1),'top':(0,1),'left':(-1,0)}[entry];sx=pc.x+dx*3;sy=pc.y+dy*3;ex=sx+dx*3;ey=sy+dy*3
 svg.append(f'<path d="M{sx},{sy} L{ex},{ey} M{ex-dx+dy*.7},{ey-dy-dx*.7} L{ex},{ey} L{ex-dx-dy*.7},{ey-dy+dx*.7}" fill="none" stroke="#06493f" stroke-width=".28"/></g><text x="{cx}" y="44.6" text-anchor="middle" font-size=".92">{html.escape(desc)}</text>')
svg.append('<text x="61" y="47.5" text-anchor="middle" font-size=".85" fill="#8a4600">34.5 × 34.5 mm · Full supplier courtyards · Sideways layout requires repositioning parts · Unrouted</text></svg>')
(out/'comparison.svg').write_text('\n'.join(svg)+'\n')
print(json.dumps({'half_turn':halfturn,'sideways_overlap_count':side['collision_count'],'sideways_fixed_layout_possible':False,'main_layout_changed':False}))
