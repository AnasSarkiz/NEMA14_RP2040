"""NEMA14 JST conservative mating/sweep screen against imported supplier solids.
The housing is a catalog envelope. Physical assembly/handling is never claimed.
"""
from pathlib import Path
import hashlib,json,math,sys
import cadquery as cq
board_path,plug_path,out_path=map(Path,sys.argv[1:4]);data=board_path.read_bytes();b=json.loads(data);plug=json.loads(plug_path.read_text());assert plug['board_sha256']==hashlib.sha256(data).hexdigest()
ROOT=Path(__file__).resolve().parents[1];catalog=json.loads((ROOT/'src/jlcpcb-catalog.json').read_text())
src={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'}
dnp={e['source_component_id'] for e in b if e['type']=='pcb_component' and e.get('do_not_place')}
def bb(shape):
 q=shape.BoundingBox();return [q.xmin,q.ymin,q.zmin,q.xmax,q.ymax,q.zmax]
def lower(a,z):return math.sqrt(sum(max(a[k]-z[k+3],z[k]-a[k+3],0)**2 for k in range(3)))
def overlaps(a,z):return all(a[k+3]>z[k]+1e-7 and z[k+3]>a[k]+1e-7 for k in range(3))
def solid_box(q):
 a,z=q['min'],q['max'];return cq.Workplane('XY').box(*(z[k]-a[k] for k in range(3))).val().translate(tuple((a[k]+z[k])/2 for k in range(3)))
shapes={};cache={};fallback=[];model_hashes={}
for e in b:
 if e['type']!='cad_component' or e.get('source_component_id') in dnp or not e.get('model_step_url'):continue
 name=src[e['source_component_id']]
 if name=='J_MOTOR':continue # Intended socket overlap is not interference with another component.
 part=catalog['parts'][catalog['components'][name]]
 path=ROOT/next(p for p in part['modelFiles'] if p.endswith('.step'))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==part['sha256']['step'],name
 key=str(path.resolve())
 if key not in cache:
  try:
   shape=cq.importers.importStep(str(path)).val()
  except Exception as exc:
   obj=ROOT/next(p for p in part['modelFiles'] if p.endswith('.obj'));points=[]
   assert hashlib.sha256(obj.read_bytes()).hexdigest()==part['sha256']['obj'],name
   if obj.is_file():
    for line in obj.read_text(errors='replace').splitlines():
     if line.startswith('v '):points.append(tuple(map(float,line.split()[1:4])))
   if not points:raise RuntimeError(f'{name}: unreadable STEP and no valid OBJ bounds: {path}') from exc
   q={'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)]}
   shape=solid_box(q);fallback.append(name+': unreadable STEP; conservative supplier OBJ bounds')
  cache[key]=shape;model_hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
 shape=cache[key].copy();o=e['model_origin_position'];shape=shape.translate(tuple(-o[k] for k in 'xyz'))
 for axis,vector in [('x',(1,0,0)),('y',(0,1,0)),('z',(0,0,1))]:
  if e['rotation'][axis]:shape=shape.rotate((0,0,0),vector,e['rotation'][axis])
 shape=shape.translate(tuple(e['position'][k] for k in 'xyz'))
 if not shape.isValid():
  a=bb(shape);shape=solid_box({'min':a[:3],'max':a[3:]});fallback.append(name)
 shapes[name]=shape
# Reserve the full head envelope above the PCB; actual fasteners remain unspecified.
for x in [-13,13]:
 for y in [-13,13]:shapes[f'SCREW_RESERVE_{x}_{y}']=cq.Workplane('XY').circle(3.2).extrude(3).val().translate((x,y,.8))
rows={}
for label in ['seated_envelope','withdrawal_sweep','service_grip_envelope']:
 envelope=solid_box(plug[label]);bounds=bb(envelope);bad=[];distances=[]
 for name,shape in shapes.items():
  sb=bb(shape);lb=lower(bounds,sb);distances.append((lb,name))
  if not overlaps(bounds,sb):continue
  volume=envelope.intersect(shape).Volume()
  if volume>1e-6:bad.append({'part':name,'intersection_volume_mm3':volume})
 rows[label]={'intersections':bad,'nearest_bounding_box_clearance_mm':min(distances)[0],'nearest_bounding_box_part':min(distances)[1]}
report={'board_sha256':plug['board_sha256'],'envelope_clearance_pass':all(not r['intersections'] for r in rows.values()),'physical_fit_verified':False,'actual_cable_handling_verified':False,'exposed_housing_length_mm':plug['exposed_housing_length_mm'],'screens':rows,'supplier_solids_checked':len(shapes)-4,'invalid_supplier_solids_using_conservative_bounds':fallback,'model_sha256':model_hashes,'assumptions':plug['assumptions']}
out_path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='model_sha256'},indent=2));raise SystemExit(0 if report['envelope_clearance_pass'] else 1)
