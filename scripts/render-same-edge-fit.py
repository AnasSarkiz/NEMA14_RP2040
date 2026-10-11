import json,pathlib,sys,math
import cadquery as cq
from shapely.geometry import Polygon
from shapely.ops import unary_union
root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1];j=json.loads((root/'artifacts/board.circuit.json').read_text());cat=json.loads((root/'src/jlcpcb-catalog.json').read_text());src={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'}
scale=20;ox=425;oy=520
xy=lambda x,y:(ox+x*scale,oy-y*scale)
items=[]
def path(coords):return ' '.join(('M' if k==0 else 'L')+f'{xy(x,y)[0]:.3f},{xy(x,y)[1]:.3f}' for k,(x,y) in enumerate(coords))+' Z'
def circle(x,y,r,fill,stroke,dash=''):
 a,b=xy(x,y);items.append(f'<circle cx="{a}" cy="{b}" r="{r*scale}" fill="{fill}" stroke="{stroke}" stroke-width="2" {dash}/>')
def label(x,y,s,size=17,color='#17324d'):
 a,b=xy(x,y);items.append(f'<text x="{a}" y="{b}" text-anchor="middle" font-size="{size}" fill="{color}">{s}</text>')
items.append(f'<path d="{path([(-17.5,-17.5),(17.5,-17.5),(17.5,17.5),(-17.5,17.5)])}" fill="#eef7f1" stroke="#245943" stroke-width="3"/>')
for x in [-13,13]:
 for y in [-13,13]:
  circle(x,y,2.2,'none','#d18a00','stroke-dasharray="5 4"');circle(x,y,2,'#dbe3ea','#3b536a');circle(x,y,1.6,'white','#17324d')
for name,x in [('J_PD',-6.2),('J_DATA',6.2)]:
 m=next(e for e in j if e['type']=='cad_component' and src[e['source_component_id']]==name);part=cat['parts'][cat['components'][name]];f=root/next(f for f in part['modelFiles'] if f.endswith('.step'));s=cq.importers.importStep(str(f)).val();o=m['model_origin_position'];s=s.translate(tuple(-o[k] for k in 'xyz'))
 for axis,v in [('x',(1,0,0)),('y',(0,1,0)),('z',(0,0,1))]:
  if m['rotation'][axis]:s=s.rotate((0,0,0),v,m['rotation'][axis])
 s=s.translate(tuple(m['position'][k] for k in 'xyz'));slab=cq.Workplane('XY').box(100,100,3,centered=(True,True,False)).val().translate((0,0,.8));s=s.intersect(slab);verts,faces=s.tessellate(.02,.08);polys=[]
 for tri in faces:
  p=Polygon([(verts[k].x,verts[k].y) for k in tri])
  if p.area>1e-10:polys.append(p)
 shape=unary_union(polys)
 for q in list(shape.geoms) if hasattr(shape,'geoms') else [shape]:items.append(f'<path d="{path(q.exterior.coords)}" fill="#bac4cf" stroke="#334a62" stroke-width="1.5"/>')
 # Only the near segment is drawn; full 30 mm envelope is in the native audit.
 items.append(f'<path d="{path([(x-6,17.5),(x+6,17.5),(x+6,23),(x-6,23)])}" fill="#addcff" fill-opacity="0.7" stroke="#2877af" stroke-width="2"/>');label(x,20,name.replace('J_','')+' plug',16);label(x,18.4,'12 mm max',14)
label(0,24,'Same-edge USB-C fit · actual PCB and native STEP geometry',23)
label(0,22,'0.4 mm gap between 12 mm plug envelopes',16)
label(0,5,'35 × 35 mm PCB · no extension',21)
label(0,3.5,'Four holes at (±13, ±13), Ø3.2 mm',18)
label(0,1.8,'M3 DIN 920 heads ≤Ø4 mm required',18)
label(0,-.1,'Dashed circle: Ø4.4 mm screening envelope',16,'#9b6700')
label(0,-2,'USB body/head envelope minimum gap: 0.13 mm',16)
label(0,-4,'Native 3D collisions: zero · physical samples untested',15)
label(0,-19.4,'Top projection of USB solids between z=0.8 and 3.8 mm, matching the head screen.',14)
label(0,-20.6,'Rear motor fit is unverified. Drawing does not qualify complete assembly tolerances.',14)
svg='<svg xmlns="http://www.w3.org/2000/svg" width="850" height="980" viewBox="0 0 850 980"><rect width="850" height="980" fill="white"/><g font-family="Arial,sans-serif">'+''.join(items)+'</g></svg>';out=root/'artifacts/mechanical/same-edge-fit.svg';out.write_text(svg)
import cairosvg
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(out.with_suffix('.png')),output_width=1275,output_height=1470)
print(out.with_suffix('.png'))
