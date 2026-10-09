"""Guard narrowly excluded USB courtyard rectangles with actual native metal.
No supplier footprint is altered; circular routing keepouts stay active.
"""
import sys,json,pathlib,hashlib,math
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
import verify_supplier_connectivity as native
root=pathlib.Path(__file__).resolve().parents[1];path=root/(sys.argv[1] if len(sys.argv)>1 else 'artifacts/board.circuit.json');j=json.loads(path.read_text());cat=json.loads((root/'src/jlcpcb-catalog.json').read_text())
src={e['source_component_id']:e for e in j if e['type']=='source_component'};pcs={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'}
circles=[e for e in j if e['type']=='pcb_keepout'];assert len(circles)==4
board_layers={'top','bottom'} if next(e for e in j if e['type']=='pcb_board')['num_layers']==2 else {'top','inner1','inner2','bottom'}
port_ids={e['pcb_component_id'] for e in pcs.values() if src[e['source_component_id']]['name'] in ['J_PD','J_DATA']}
for e in circles:
 assert e['shape']=='circle' and abs(e['radius']-2.7)<1e-6 and set(e['layers'])=={'top','inner1','inner2','bottom'}
 assert set(e.get('excluded_pcb_component_ids',[]))==port_ids,'Mounting keepout exclusions must target only the two independently checked USB native components'
records=[]
for name,x in [('J_PD',-7),('J_DATA',7)]:
 s=next(e for e in src.values() if e['name']==name);c=next(e for e in pcs.values() if e['source_component_id']==s['source_component_id']);m=next(e for e in j if e['type']=='cad_component' and e['source_component_id']==s['source_component_id']);part=cat['parts'][cat['components'][name]]
 assert abs(m['position']['x']-x)<1e-6 and abs(m['position']['y']-12.5499711)<1e-6
 a=math.radians(m['rotation']['z']);assert abs(math.sin(a))<1e-6 and math.cos(a)>.999999
 opening=m['position']['y']+math.cos(a)*(2.6-m['model_origin_position']['y']);assert abs(opening-17.9)<1e-6
 obj=root/next(p for p in part['modelFiles'] if p.endswith('.obj'));assert hashlib.sha256(obj.read_bytes()).hexdigest()==part['sha256']['obj']
 verts=[];faces=[]
 for line in obj.read_text().splitlines():
  if line.startswith('v '):
   p=list(map(float,line.split()[1:4]));u=p[0]-m['model_origin_position']['x'];v=p[1]-m['model_origin_position']['y'];verts.append((m['position']['x']+math.cos(a)*u-math.sin(a)*v,m['position']['y']+math.sin(a)*u+math.cos(a)*v))
  elif line.startswith('f '):
   ids=[int(i.split('/')[0])-1 for i in line.split()[1:]]
   for i in range(1,len(ids)-1):
    p=Polygon([verts[k] for k in [ids[0],ids[i],ids[i+1]]]);
    if p.area>1e-10:faces.append(p)
 body=unary_union(faces);assert body.area>10
 pads=[native.geometry(e) for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and e['pcb_component_id']==c['pcb_component_id']];assert len(pads)==16
 copper=unary_union(pads);mincu=99;minbody=99
 for e in circles:
  circle=Point(e['center']['x'],e['center']['y']).buffer(e['radius'],quad_segs=128);mincu=min(mincu,copper.distance(circle));minbody=min(minbody,body.distance(circle))
  assert copper.distance(circle)>=.15-1e-6,(name,'native outer copper violates mounting circle',copper.distance(circle))
  assert body.distance(circle)>=.15-1e-6,(name,'native OBJ body violates mounting circle',body.distance(circle))
 records.append({'reference':name,'nativePadCount':len(pads),'minimumCopperTo5p4mmCircleMm':mincu,'nativeObjProjectedBodyToCircleMm':minbody,'mouthYmm':opening,'cadAngleDeg':m['rotation']['z']})
report={'boardSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'input':str(path.relative_to(root)),'exactNativePadsChecked':True,'nativeObjHashVerified':True,'courtyardExclusionScope':'J_PD/J_DATA only; supplier rectangle preserved; actual pad and native projected-body checked independently','cableRequirement':'Tensility10-06137 PD /10-06139 data, maximum12.5mm overmolds at14mm pitch; qualify physical samples','nativeSTEPFinalMechanicalReviewRequired':True,'ports':records,'passed':True}
(root/'artifacts/usb-head-clearance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
