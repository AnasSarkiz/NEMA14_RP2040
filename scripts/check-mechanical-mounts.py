import pathlib,json,hashlib,itertools,math,sys
import cadquery as cq
from shapely.geometry import Point,LineString,Polygon,box
from shapely import affinity
from shapely.ops import unary_union
root=pathlib.Path(__file__).resolve().parents[1];board_bytes=(root/'artifacts/board.circuit.json').read_bytes();j=json.loads(board_bytes);cat=json.loads((root/'src/jlcpcb-catalog.json').read_text());src={e['source_component_id']:e for e in j if e['type']=='source_component'};parts={};cache={};meta={}
bound_cache={}
def bounds(s):
 if id(s) in bound_cache:return bound_cache[id(s)]
 b=s.BoundingBox();bound_cache[id(s)]= [getattr(b,k) for k in ['xmin','ymin','zmin','xmax','ymax','zmax']]
 return bound_cache[id(s)]
def broad(a,b):
 x,y=bounds(a),bounds(b);return all(x[i+3]>=y[i] and y[i+3]>=x[i] for i in range(3))
def volume(a,b):return max(0,a.intersect(b).Volume()) if broad(a,b) else 0
for m in j:
 if m['type']!='cad_component' or not m.get('model_step_url'):continue
 name=src[m['source_component_id']]['name'];p=cat['parts'][cat['components'][name]];f=root/next(f for f in p['modelFiles'] if f.endswith('.step'));assert hashlib.sha256(f.read_bytes()).hexdigest()==p['sha256']['step']
 if str(f) not in cache:cache[str(f)]=cq.importers.importStep(str(f)).val()
 s=cache[str(f)];assert s.isValid() and len(s.Solids())>0
 o=m['model_origin_position'];s=s.translate(tuple(-o[k] for k in 'xyz'))
 for axis,vec in [('x',(1,0,0)),('y',(0,1,0)),('z',(0,0,1))]:
  if m['rotation'][axis]:s=s.rotate((0,0,0),vec,m['rotation'][axis])
 s=s.translate(tuple(m['position'][k] for k in 'xyz'));parts[name]=s;meta[name]=m
 print('Imported',name,flush=True)
assert set(parts)==set(cat['components']), 'Every fitted part requires its original STEP model'
heads={str((x,y)):cq.Workplane('XY').circle(2.7).extrude(3).val().translate((x,y,.8)) for x,y in itertools.product([-13,13],repeat=2)}
intersections=[];clearances=[]
for (a,s),(b,t) in itertools.combinations(parts.items(),2):
 if broad(s,t):
  print('Intersect',a,b,flush=True)
  v=volume(s,t)
  if v>1e-5:intersections.append({'a':a,'b':b,'volume_mm3':v})
for a,s in parts.items():
 for b,t in heads.items():
  x,y=bounds(s),bounds(t)
  lower=math.sqrt(sum(max(x[i]-y[i+3],y[i]-x[i+3],0)**2 for i in range(3)))
  if lower>=1:continue
  d=s.distance(t)
  if d<1:clearances.append({'reference':a,'mount':b,'distance_to_radius2p7_fastener_mm':d,'intersection_mm3':volume(s,t)})
plugs={};usb=[]
for name in ['J_PD','J_DATA']:
 m=meta[name];a=math.radians(m['rotation']['z']);mouth=[m['position']['x']-math.sin(a)*(2.6-m['model_origin_position']['y']),m['position']['y']+math.cos(a)*(2.6-m['model_origin_position']['y'])];direction=[-math.sin(a),math.cos(a)]
 # 12 mm wide, 7 mm tall, 30 mm long plug envelope, centred at mating plane +15 mm.
 plug=cq.Workplane('XY').box(12,30,7).val().rotate((0,0,0),(0,0,1),m['rotation']['z']).translate((mouth[0]+direction[0]*15,mouth[1]+direction[1]*15,2.45));plugs[name]=plug
 collisions=[]
 for n,s in list(parts.items())+list(heads.items()):
  if n!=name and broad(plug,s):
   v=volume(plug,s)
   if v>1e-5:collisions.append({'other':n,'volume_mm3':v})
 usb.append({'native_body_to_mount_envelope_mm':min(parts[name].distance(h) for h in heads.values()),'reference':name,'mouth_xy_mm':mouth,'outward_unit_vector':direction,'plug_12x30x7mm_intersections':collisions,'bbox_mm':bounds(parts[name])})
report={'board_sha256':hashlib.sha256(board_bytes).hexdigest(),'native_STEP_models':len(parts),'component_intersections':intersections,'fastener_clearances':clearances,'usb':usb,'mounts':[[x,y] for x,y in itertools.product([-13,13],repeat=2)],'rear_motor_compatibility_verified':False,'limitations':['Nominal PCB/model screen only; no verified mounting to rear motor endcap.','Cable envelope is a defined 12x30x7 mm procurement bound, not tested cable hardware.','PCB fastener envelope radius2.7 includes nominal head/play; actual hardware and placement tolerances remain unqualified.']}
out=root/'artifacts/mechanical';out.mkdir(exist_ok=True);assert (root/'artifacts/board.circuit.json').read_bytes()==board_bytes, 'Board changed during mechanical audit'
report['passed']=not intersections and all(e['intersection_mm3']<1e-5 for e in clearances) and all(not e['plug_12x30x7mm_intersections'] for e in usb)
(out/'mount-usb-screen.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

raise SystemExit(0 if report['passed'] else 1)
