"""Reproducible mechanical screen using unchanged official STEP and fitted supplier STEP.
Run with the project routing venv. Never edits circuit/source/manufacturing outputs.
The generated carrier is a separate unqualified engineering prototype, not motor CAD.
"""
import argparse,hashlib,itertools,json,math,pathlib,sys,zipfile,shutil
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle,Rectangle
from shapely.geometry import Point,Polygon,LineString,box as planar_box
from shapely import affinity
ROOT=pathlib.Path(__file__).resolve().parents[1]
TITLE=json.loads((ROOT/'package.json').read_text())['name']
OUT=ROOT/'artifacts/mechanical';OUT.mkdir(parents=True,exist_ok=True)
script_bytes=pathlib.Path(__file__).read_bytes();script_sha=hashlib.sha256(script_bytes).hexdigest()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
STEP_EXPORTS=[]
def compress_step(path):
 path=pathlib.Path(path);dest=path.with_suffix(path.suffix+'.zip');raw_hash=sha(path);raw_size=path.stat().st_size
 with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  info=zipfile.ZipInfo(path.name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
  with path.open('rb') as inp,z.open(info,'w') as target:shutil.copyfileobj(inp,target)
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
 STEP_EXPORTS.append({'archive':dest.name,'member':path.name,'uncompressed_step_sha256':raw_hash,'uncompressed_bytes':raw_size,'archive_sha256':sha(dest),'archive_crc_verified':True})
 path.unlink()
 return dest
parser=argparse.ArgumentParser();parser.add_argument('--input',default='artifacts/board.circuit.json',help='Saved board or frozen fresh-source physical geometry; routing is outside this mechanical review');args=parser.parse_args();boardpath=(ROOT/args.input).resolve();board_bytes=boardpath.read_bytes();input_sha=hashlib.sha256(board_bytes).hexdigest();j=json.loads(board_bytes);catpath=ROOT/'src/jlcpcb-catalog.json';cat_bytes=catpath.read_bytes();cat=json.loads(cat_bytes)
source={e['source_component_id']:e for e in j if e['type']=='source_component'}
BOUND_CACHE={}
def bounds(s):
 key=id(s)
 if key not in BOUND_CACHE:
  b=s.BoundingBox();BOUND_CACHE[key]=(s,[getattr(b,a) for a in ['xmin','ymin','zmin','xmax','ymax','zmax']])
 return BOUND_CACHE[key][1]
def box(w,h,d,x=0,y=0,z=0):return cq.Workplane('XY').box(w,h,d).val().translate((x,y,z))
def cyl(r,h,x,y,z):return cq.Workplane('XY').circle(r).extrude(h).val().translate((x,y,z))
def broad(a,b,margin=0):
 x=bounds(a);y=bounds(b);return all(x[i+3]+margin>=y[i] and y[i+3]+margin>=x[i] for i in range(3))
def volume(a,b):return max(0,a.intersect(b).Volume()) if broad(a,b) else 0
b=next(e for e in j if e['type']=='pcb_board');th=b['thickness'];assert abs(th-1.6)<1e-8
pcb=box(b['width'],b['height'],th,b['center']['x'],b['center']['y'])
holes=[e for e in j if e['type']=='pcb_hole' and e.get('pcb_component_id') is None]
for e in j:
 if e['type']=='pcb_hole':
  tool=cyl(e['hole_diameter']/2,th+2,e['x'],e['y'],-th/2-1)
 elif e['type']=='pcb_plated_hole':
  w,h=e.get('hole_width'),e.get('hole_height')
  if w and h:
   angle=(90 if h>w else 0)+e.get('ccw_rotation',0)
   tool=cq.Workplane('XY').slot2D(max(w,h),min(w,h),angle).extrude(th+2).val().translate((e['x'],e['y'],-th/2-1))
  else:tool=cyl(e['hole_diameter']/2,th+2,e['x'],e['y'],-th/2-1)
 else:continue
 pcb=pcb.cut(tool)
parts={};models=[];cache={};meshes={}
for m in [e for e in j if e['type']=='cad_component' and e.get('model_step_url')]:
 name=source[m['source_component_id']]['name'];cid=cat['components'][name];p=cat['parts'][cid]
 f=ROOT/next(f for f in p['modelFiles'] if f.endswith('.step'))
 assert sha(f)==p['sha256']['step'],name+' STEP checksum mismatch'
 assert (m['model_step_url']==p['activeModelUrls']['step'] if 'activeModelUrls' in p else m['model_step_url'].endswith('/'+str(f.relative_to(ROOT)))),name+' active CAD STEP URL differs from supplier catalog'
 assert source[m['source_component_id']]['manufacturer_part_number']==p['manufacturerPartNumber'],name+' saved manufacturer identity mismatch'
 if cid not in cache:
  cache[cid]=cq.importers.importStep(str(f)).val()
  assert cache[cid].isValid(),name+' invalid supplier STEP BREP'
  assert len(cache[cid].Solids())>0,name+' supplier STEP has no closed solid for volumetric collision proof'
 s=cache[cid];o=m['model_origin_position'];s=s.translate(tuple(-o[a] for a in 'xyz'))
 for a,axis in [('x',(1,0,0)),('y',(0,1,0)),('z',(0,0,1))]:
  if m['rotation'].get(a):s=s.rotate((0,0,0),axis,m['rotation'][a])
 s=s.translate(tuple(m['position'][a] for a in 'xyz'));parts[name]=s
 models.append({'reference':name,'jlcpcb':cid,'step':str(f.relative_to(ROOT)),'sha256':sha(f),'valid_brep':True,'native_solid_count':len(cache[cid].Solids()),'world_bbox_mm':bounds(s),'cad_record':m})
 print('Imported',name,flush=True)
assert set(parts)==set(cat['components']),'every fitted catalog component must have a native STEP assembly model'
assert len(holes)==4 and {(e['x'],e['y']) for e in holes}=={(-13,-13),(13,-13),(-14.8,13),(14.8,13)},'carrier requires saved service revision four-hole pattern'
(OUT/'input-review-mechanical.py').write_bytes(script_bytes);(OUT/'input-board.circuit.json').write_bytes(board_bytes);(OUT/'input-jlcpcb-catalog.json').write_bytes(cat_bytes)
ref=ROOT/'references/motor/14hm11-0404s';motorfile=ref/'14HM11-0404S.STEP'
assert sha(motorfile)=='959f43e95b7840beae5ffbd56e997e23c5004a1b09e16b7caa40400296e46281'
motor_native=cq.importers.importStep(str(motorfile)).val();assert motor_native.isValid()
motor_cylinders=[];seen_cylinders=set()
for face in motor_native.Faces():
 if face.geomType()!='CYLINDER':continue
 cylinder=BRepAdaptor_Surface(face.wrapped).Cylinder();axis=cylinder.Axis();loc=axis.Location();direction=axis.Direction()
 if abs(direction.Z())<.999:continue
 fb=bounds(face);record={'axis_x_mm':loc.X(),'axis_y_mm':loc.Y(),'radius_mm':cylinder.Radius(),'native_z_range_mm':[fb[2],fb[5]]};key=tuple(round(record[k],4) for k in ['axis_x_mm','axis_y_mm','radius_mm'])+tuple(round(v,4) for v in record['native_z_range_mm'])
 if key not in seen_cylinders:motor_cylinders.append(record);seen_cylinders.add(key)
rear=-8.;front=rear-28.2;motor=motor_native.translate((0,0,front))
# A monolithic machined carrier: front flange, four outside rails, rear returns, bosses.
print('Building separate carrier',flush=True)
plate=box(49.2,36.4,4,z=front-2).cut(cyl(11.075,6,0,0,front-5))
# Root-fillet relief retains the documented22mm locating section below0.4mm.
plate=plate.cut(cyl(11.7,.4,0,0,front-.4))
for x,y in itertools.product([-13,13],repeat=2):plate=plate.cut(cyl(2.05,6,x,y,front-5))
carrier=plate
for e in holes:
 x,y=e['x'],e['y']
 railx=math.copysign(21.6,x);lo=front-4;hi=-2.8
 rail=box(6,5,hi-lo,x=railx,y=y,z=(hi+lo)/2)
 ret=box(13.85,5,4,x=math.copysign(17.675,x),y=y,z=-4.8)
 boss=cyl(2.25,2,x,y,-2.8)
 carrier=carrier.fuse(rail,ret,boss)
 # M2.5 nominal tapping bore, no helical thread geometry. 6 mm through-tapped available thickness.
 carrier=carrier.cut(cyl(1.025,6.0,x,y,-6.8))
carrier=carrier.clean();assert carrier.isValid()
hardware={};heads={}
for i,e in enumerate(holes):
 x,y=e['x'],e['y'];h=cyl(2.25,2.5,x,y,.8)
 heads[f'PCB_M2p5_head_{i}']=h
 hardware[f'PCB_M2p5_envelope_{i}']=h.fuse(cyl(1.25,6,x,y,-5.2))
for i,(x,y) in enumerate(itertools.product([-13,13],repeat=2)):
 h=cyl(2.75,3,x,y,front-7.5);washer=cyl(3.5,.5,x,y,front-4.5).cut(cyl(1.6,.6,x,y,front-4.55))
 hardware[f'Front_M3_envelope_{i}']=h.fuse(washer,cyl(1.5,8,x,y,front-4.5))
# HAR-001 positive restraint, actual connector and installation envelopes.
import importlib.util
service_spec=importlib.util.spec_from_file_location('service_harness',ROOT/'scripts/service-harness.py');service=importlib.util.module_from_spec(service_spec);service_spec.loader.exec_module(service)
carrier,service_parts,service_colors,pcb_hardware,new_heads,motor_access,service_report=service.build(carrier,parts,j,front)
hardware={k:v for k,v in hardware.items() if not k.startswith('PCB_')};hardware.update(pcb_hardware);heads=new_heads

# Same-edge ports: +Y mouths, separate PD/data connector, compact cable procurement.
usb_models={e['reference']:e for e in models if e['reference'] in ['J_PD','J_DATA']}
assert set(usb_models)=={'J_PD','J_DATA'}
usb_mouths={}
for name,m in usb_models.items():
 assert abs(m['cad_record']['rotation']['z']%360)<1e-8,name+' must have native CAD0, face +Y'
 bb=m['world_bbox_mm'];mouth=[(bb[0]+bb[3])/2,bb[4]]
 assert abs(mouth[1]-17.9)<1e-6,name+' mouth must lie on +Y17.9, 0.4mm outward of PCB edge'
 usb_mouths[name]=mouth
plug={name:box(12.5,32.5,7.6,x=mouth[0],y=mouth[1]+16.25,z=2.45) for name,mouth in usb_mouths.items()}
plug12=plug.copy()
cable_parts={}
for name,mpn in [('J_PD','USB-PD-Tensility-10-06137'),('J_DATA','USB-data-Tensility-10-06139')]:
    x,y=usb_mouths[name];native=cq.importers.importStep(str(ROOT/'references/models'/(mpn+'-C-end.step'))).val()
    cable_parts[name+'_selected_cable']=native.translate((x,y,2.45))
    start=cq.Vector(x,y+32.5,2.45);a=cq.Vector(x,y+37.5,2.45);b=cq.Vector(x,y+67.5,32.45)
    for i,e in enumerate([cq.Edge.makeLine(start,a),cq.Edge.makeThreePointArc(a,cq.Vector(x,y+37.5+30/math.sqrt(2),32.45-30/math.sqrt(2)),b)]):
        cable_parts[name+'_cable_bend_'+str(i)]=cq.Workplane(cq.Plane(origin=e.startPoint(),normal=e.tangentAt(0))).circle(1.975).sweep(cq.Wire.assembleEdges([e]),isFrenet=True).val()

b=next(e for e in j if e['type']=='pcb_board')
# Physical intersections use actual imported BREP. No blanketing of touching parts.
print('Checking exact component and mechanical intersections',flush=True)
pair=[];near=[]
for (a,sa),(c,sc) in itertools.combinations(parts.items(),2):
 if broad(sa,sc,.2):
  print('Checking component pair',a,c,flush=True)
  d=sa.distance(sc);v=volume(sa,sc)
  if v>1e-5:pair.append({'a':a,'b':c,'intersection_mm3':v})
  if d<.2:near.append({'a':a,'b':c,'minimum_distance_mm':d})
mount=[]
for name,s in parts.items():
 for h,hs in heads.items():
  if broad(s,hs,.5):mount.append({'reference':name,'hardware':h,'distance_mm':s.distance(hs),'remaining_distance_lower_bound_after_0p35mm_pcb_hole_play':max(0,s.distance(hs)-.35),'intersection_mm3':volume(s,hs)})
def bbox_distance(a,b):
 x=bounds(a);y=bounds(b);return math.sqrt(sum(max(x[i]-y[i+3],y[i]-x[i+3],0)**2 for i in range(3)))
head_bounds=[]
for h,hs in heads.items():
 nearest=min(parts.items(),key=lambda item:bbox_distance(hs,item[1]));lower=bbox_distance(hs,nearest[1]);head_bounds.append({'hardware':h,'controlling_model_bbox':nearest[0],'minimum_all_component_distance_lower_bound_mm':lower,'remaining_lower_bound_after_0p35mm_hole_play':max(0,lower-.35)})
penetrations=[]
for name,s in parts.items():
 if bounds(s)[2]<.8-1e-4:
  penetrations.append({'reference':name,'distance_below_top_mm':.8-bounds(s)[2],'intersection_with_drilled_substrate_mm3':volume(s,pcb),'interpretation':'supplier STEP/tab versus native plated-slot fit; physical connector fit needs confirmation' if name.startswith('J_') else 'model body penetration requiring review'})
print('Motor/carrier exact intersection',flush=True)
carrier_checks=[{'item':'official_motor','distance_mm':carrier.distance(motor),'intersection_mm3':volume(carrier,motor),'intentional_contact':'motor front flange and carrier front plate mating plane'}]
for name,s in parts.items():
 zclear=bounds(s)[2]-bounds(carrier)[5]
 carrier_checks.append({'item':name,'minimum_distance_lower_bound_mm':max(0,zclear),'method':'actual BREP Z-extrema prove separation' if zclear>0 else 'exact solid common','intersection_mm3':0 if zclear>0 else volume(carrier,s)})
plug_checks=[{'port':'J_PD','other':'J_DATA_compact_plug','distance_mm':plug['J_PD'].distance(plug['J_DATA']),'intersection_mm3':volume(plug['J_PD'],plug['J_DATA'])}]
for name,s in plug.items():
 for label,shape in [('carrier',carrier),('motor',motor)]+[(n,v) for n,v in parts.items() if n!=name]+list(heads.items()):
  if broad(s,shape,2):plug_checks.append({'port':name,'other':label,'distance_mm':s.distance(shape),'intersection_mm3':volume(s,shape)})
# Native pad copper versus actual circular fastener keepout, preserving each import.
# Threads, solder fillets and full routed copper are reviewed separately.
pad_head_screen=[]
for e in j:
 if e['type'] not in ['pcb_smtpad','pcb_plated_hole']:continue
 shape=e.get('shape')
 if shape=='polygon':g=Polygon([(p['x'],p['y']) for p in e['points']])
 elif shape=='rect':
  w,h=e['width'],e['height'];g=planar_box(-w/2,-h/2,w/2,h/2);g=affinity.rotate(g,e.get('ccw_rotation',0),origin=(0,0));g=affinity.translate(g,e['x'],e['y'])
 elif shape in ['pill','rotated_pill','circle']:
  w=e.get('outer_width',e.get('outer_diameter',e.get('width',e.get('radius',0)*2)));h=e.get('outer_height',e.get('height',w));assert w>0 and h>0,'invalid native pad envelope';r=min(w,h)/2;half=(max(w,h)-min(w,h))/2
  g=(Point(0,0) if half<1e-10 else LineString([(0,-half),(0,half)] if h>w else [(-half,0),(half,0)])).buffer(r,resolution=256);g=affinity.rotate(g,e.get('ccw_rotation',0),origin=(0,0));g=affinity.translate(g,e['x'],e['y'])
 else:raise AssertionError('Unsupported native pad shape for fastener clearance: '+str(shape))
 pc=next(c for c in j if c['type']=='pcb_component' and c['pcb_component_id']==e['pcb_component_id']);name=source[pc['source_component_id']]['name']
 for hole in holes:
  d=g.distance(Point(hole['x'],hole['y']));gap=d-2.7
  if gap<1:pad_head_screen.append({'reference':name,'native_pad_id':e.get('pcb_smtpad_id',e.get('pcb_plated_hole_id')),'mount_xy_mm':[hole['x'],hole['y']],'outer_copper_to_5p4mm_circle_mm':gap,'outer_copper_to_5p2mm_swept_head_mm':d-2.6,'interpretation':'native pad copper, actual circle; 0.35mm hole play included in swept head, solder/placement tolerance excluded'})

# Bare interfaces remain real PCB features; check bounded straight top tool access.
pcbcomponents={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'}
access=[]
for e in j:
 if e['type']!='pcb_port':continue
 pc=pcbcomponents.get(e.get('pcb_component_id'));name=source[pc['source_component_id']]['name'] if pc else ''
 if name not in ['J_BOOT','J_DEBUG']:continue
 radius=.25 if name=='J_BOOT' else .5
 tool=cyl(radius,10,e['x'],e['y'],.8)
 collisions=[{'reference':n,'intersection_mm3':volume(tool,s)} for n,s in parts.items() if broad(tool,s)]
 collisions=[c for c in collisions if c['intersection_mm3']>1e-5]
 access.append({'interface':name,'pcb_port_id':e['pcb_port_id'],'xy_mm':[e['x'],e['y']],'tool_diameter_mm':radius*2,'straight_top_access_collisions':collisions})
manufacturer_pkg=None
if cat['components']['C_BULK']=='C178585':
 bulk_m=next(e['cad_record'] for e in models if e['reference']=='C_BULK');a=math.radians(bulk_m['rotation']['z']);r=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]);c=np.array([bulk_m['position']['x'],bulk_m['position']['y']])-r@np.array([bulk_m['model_origin_position']['x'],bulk_m['model_origin_position']['y']])
 manufacturer_pkg=box(7.8,6.8,8.3,z=4.15).rotate((0,0,0),(0,0,1),bulk_m['rotation']['z']).translate((c[0],c[1],.8));cq.exporters.export(manufacturer_pkg,str(OUT/'bulk-manufacturer-maximum-envelope.step'))
# Export actual supplier model assembly and separate exact motor/carrier context.
print('Exporting native STEP assemblies',flush=True)
colors={'PCB':(.06,.30,.16),'Official_motor':(.48,.50,.53),'Separate_front_carrier':(.66,.71,.78)}
assembly=cq.Assembly(name='NEMA14_board')
assembly.add(pcb,name='PCB',color=cq.Color(*colors['PCB']))
for name,s in parts.items():assembly.add(s,name=name,color=cq.Color(*((.68,.7,.73) if name.startswith('J_') else (.12,.14,.17) if name.startswith(('U_','D_','R_','Y_')) else (.72,.61,.37))))
assembly.save(str(OUT/'board-fitted-components.step'));compress_step(OUT/'board-fitted-components.step')
mounted=cq.Assembly(name='NEMA14_front_carrier_mounted')
mounted.add(assembly,name='Board');mounted.add(motor,name='Official_motor',color=cq.Color(*colors['Official_motor']));mounted.add(carrier,name='Separate_front_carrier',color=cq.Color(*colors['Separate_front_carrier']))
for name,s in cable_parts.items():mounted.add(s,name=name,color=cq.Color(.12,.12,.13))
for name,s in hardware.items():mounted.add(s,name=name,color=cq.Color(.78,.78,.8))
for name,s in service_parts.items():mounted.add(s,name=name,color=cq.Color(*service_colors.get(name,(.85,.8,.61))))
mounted.save(str(OUT/'mounted-front-carrier.step'));compress_step(OUT/'mounted-front-carrier.step');cq.exporters.export(carrier,str(OUT/'separate-front-carrier.step'))
cq.exporters.export(cq.Compound.makeCompound(list(hardware.values())),str(OUT/'fastener-clearance-envelopes.step'))
# Software-rasterized triangles from actual imported CAD. Projection uses one mm scale.
items=[('PCB',pcb,colors['PCB'])]+[(n,s,(.66,.68,.72) if n.startswith('J_') else (.14,.16,.20) if n.startswith(('U_','D_','R_','Y_')) else (.70,.59,.34)) for n,s in parts.items()]
context=items+[('Official_motor',motor,colors['Official_motor']),('Separate_front_carrier',carrier,colors['Separate_front_carrier'])]+[(n,s,(.74,.76,.80)) for n,s in hardware.items()]
context += [(n,s,(.15,.15,.17)) for n,s in cable_parts.items()]
context += [(n,s,service_colors.get(n,(.85,.8,.61))) for n,s in service_parts.items()]
meshcache={}
def mesh(s):
 k=id(s)
 if k not in meshcache:
  v,f=s.tessellate(.16,.15);meshcache[k]=np.array([x.toTuple() for x in v])[np.array(f)]
 return meshcache[k]
def render(label,entities,view,extent=None):
 # True orthographic software Z buffer; centroid painter order cannot prove fit.
 eye=np.array(view,dtype=float);eye/=np.linalg.norm(eye);up=np.array([0,1,0]) if abs(eye[2])>.95 else np.array([0,0,1]);u=np.cross(up,eye);u/=np.linalg.norm(u);v=np.cross(eye,u)
 limits={'board-top':(-20,20,-20,20),'board-bottom':(-20,20,-20,20),'board-isometric':(-28,28,-22,30),'mounted-top':(-30,30,-45,24),'mounted-bottom':(-30,30,-45,24),'mounted-isometric':(-48,48,-68,50),'mounted-side':(-45,24,-68,28),'motor-rear-detail':(-21,21,-21,21),'motor-front-detail':(-21,21,-21,21),'bulk-capacitor-height-review':(-28,28,-22,30)};lim=limits[label]
 if label.startswith('mounted'):lim=(-85,85,-90,110)
 W=1400;H=int(W*(lim[3]-lim[2])/(lim[1]-lim[0]));rgb=np.full((H,W,3),.965,dtype=np.float32);zbuf=np.full((H,W),-np.inf,dtype=np.float32)
 light=np.array([-.3,-.4,.85]);light/=np.linalg.norm(light)
 for name,s,color in entities:
  t=mesh(s);n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);nn=np.linalg.norm(n,axis=1);n/=np.maximum(nn[:,None],1e-12)
  valid=n@eye>-.001;t=t[valid];n=n[valid];shade=.65+.35*np.maximum(n@light,0);colors=np.array(color)[None,:]*shade[:,None]
  px=(t@u-lim[0])/(lim[1]-lim[0])*W;py=(t@v-lim[2])/(lim[3]-lim[2])*H;dz=t@eye
  for xs,ys,zs,c in zip(px,py,dz,colors):
   xlo=max(0,int(np.floor(xs.min())));xhi=min(W-1,int(np.ceil(xs.max())));ylo=max(0,int(np.floor(ys.min())));yhi=min(H-1,int(np.ceil(ys.max())))
   if xhi<xlo or yhi<ylo:continue
   den=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
   if abs(den)<1e-9:continue
   xx=np.arange(xlo,xhi+1)[None,:]+.5;yy=np.arange(ylo,yhi+1)[:,None]+.5
   w0=((ys[1]-ys[2])*(xx-xs[2])+(xs[2]-xs[1])*(yy-ys[2]))/den
   w1=((ys[2]-ys[0])*(xx-xs[2])+(xs[0]-xs[2])*(yy-ys[2]))/den;w2=1-w0-w1
   depth=w0*zs[0]+w1*zs[1]+w2*zs[2];zb=zbuf[ylo:yhi+1,xlo:xhi+1]
   mask=(w0>=-1e-8)&(w1>=-1e-8)&(w2>=-1e-8)&(depth>zb)
   zb[mask]=depth[mask];rgb[ylo:yhi+1,xlo:xhi+1][mask]=c
 fig,ax=plt.subplots(figsize=(12,9));ax.imshow(rgb,extent=lim,origin='lower',interpolation='nearest');ax.set_aspect('equal');ax.set_title(TITLE+' — '+label.replace('-',' '),fontsize=15);ax.set_xlabel('orthographic mm');ax.set_ylabel('orthographic mm')
 if label=='bulk-capacitor-height-review' and manufacturer_pkg is not None:
  for edge in manufacturer_pkg.Edges():
   points=np.array([edge.startPoint().toTuple(),edge.endPoint().toTuple()]);ax.plot(points@u,points@v,color='#1967d2',ls='--',lw=1)
  ax.text(0,27,'Blue: manufacturer maximum envelope; corrected nominal body + maximum assembly envelope',ha='center',fontsize=9,color='#1967d2')
 if label=='motor-rear-detail':
  for x,y in itertools.product([-13,13],repeat=2):ax.add_patch(Circle((x,y),2.8,fill=False,color='red',lw=1))
  ax.text(0,19,'Endcap fasteners circled; no qualified rear mounting threads',ha='center',fontsize=8,color='red')
 if label=='motor-front-detail':
  for x,y in itertools.product([-13,13],repeat=2):ax.add_patch(Circle((x,y),1.6,fill=False,color='blue',lw=1))
  ax.text(0,19,'Drawing: 4 × M3, 26 ±0.2 square, depth ≥4 mm',ha='center',fontsize=9,color='blue')
 fig.tight_layout();fig.savefig(OUT/(label+'.png'),dpi=150);plt.close(fig)
print('Rendering native STEP triangles',flush=True)
for label,view in [('board-top',(0,0,1)),('board-bottom',(0,0,-1)),('board-isometric',(1,-1,1.4))]:render(label,items,view)
for label,view in [('mounted-top',(0,0,1)),('mounted-bottom',(0,0,-1)),('mounted-isometric',(1,-1,.9)),('mounted-side',(1,0,0))]:render(label,context,view)
if manufacturer_pkg is not None:render('bulk-capacitor-height-review',items,(1,-1,1.4))
render('motor-rear-detail',[('Official_motor',motor,colors['Official_motor'])],(0,0,1))
render('motor-front-detail',[('Official_motor',motor,colors['Official_motor'])],(0,0,-1))
# Dimension drawing: independent drawing/engineering datums; native STEP views separate.
fig,axes=plt.subplots(1,2,figsize=(15,9));ax=axes[0]
ax.add_patch(Rectangle((-17.6,-17.6),35.2,35.2,fill=False,lw=2,label='motor drawing max body'))
ax.add_patch(Rectangle((-17.5,-17.5),35,35,fill=False,lw=1.5,color='green',label='PCB 35 × 35'))
for e in holes:
 x,y=e['x'],e['y'];ax.add_patch(Circle((x,y),1.6,fill=False,color='green'));ax.add_patch(Circle((x,y),2.25,fill=False,color='gray',ls='--'))
ax.annotate('',(-13,20),(13,20),arrowprops={'arrowstyle':'<->'});ax.text(0,21,'PCB: lower26 / upper29.6 mm pitch',ha='center');ax.text(0,-22,'Ø3.2 PCB holes; M2.5 heads ≤Ø4.5',ha='center')
for name,mouth in usb_mouths.items():ax.add_patch(Rectangle((mouth[0]-5,mouth[1]),10,30,fill=False,color='blue',ls='--'));ax.text(mouth[0],mouth[1]+18,name.replace('J_',''),ha='center')
ax.set_xlim(-30,30);ax.set_ylim(-28,51);ax.set_aspect('equal');ax.set_title('Rear/top view — drawing-derived + proposed dimensions');ax.legend(loc='lower left',fontsize=8);ax.set_xlabel('X mm');ax.set_ylabel('Y mm')
ax=axes[1];ax.add_patch(Rectangle((-17.6,front),35.2,28.2,fill=False,lw=2));ax.add_patch(Rectangle((-2.5,front-24),5,24,fill=False));ax.add_patch(Rectangle((-17.5,-.8),35,1.6,color='green',alpha=.5));ax.add_patch(Rectangle((18.6,front-3),6,-2.8-(front-3),fill=False,color='gray'));ax.add_patch(Rectangle((10.75,-6.8),13.85,4,fill=False,color='gray'))
for z,label in [(front,'front motor datum −36.2'),(-8,'rear datum −8.0'),(-6.8,'return bottom −6.8'),(-.8,'PCB underside −0.8'),(.8,'PCB top +0.8')]:ax.plot([-26,26],[z,z],ls=':',color='gray');ax.annotate(label,xy=(-26,z),xytext=(-28,z+({'rear datum −8.0':-1.8,'return bottom −6.8':1.6,'PCB underside −0.8':-1.2,'PCB top +0.8':1.2}.get(label,0))),ha='right',fontsize=9,arrowprops={'arrowstyle':'-','color':'gray'})
ax.annotate('',(28,-8),(28,-.8),arrowprops={'arrowstyle':'<->'});ax.text(29,-4.4,'7.2 mm\nrear/PCB gap',fontsize=9);ax.text(0,6,'35 × 35 × 1.6 PCB; components face away from motor',ha='center',fontsize=10);ax.set_xlim(-57,48);ax.set_ylim(front-28,13);ax.set_aspect('equal');ax.set_title('Side stack — front carrier, no rear screw attachment');ax.set_xlabel('X mm');ax.set_ylabel('Z mm')
fig.suptitle('Mechanical dimensions in mm — carrier is an unqualified machined prototype',fontsize=16);fig.tight_layout();fig.savefig(OUT/'dimensions.png',dpi=150);fig.savefig(OUT/'dimensions.svg');plt.close(fig)
report={'input_file':str(boardpath.relative_to(ROOT)),'mechanical_frame_kind':'saved board' if boardpath.name=='board.circuit.json' else 'fresh source physical geometry; final routed-board equivalence proof pending','copper_review_scope':'None; this script checks mechanical geometry only','project':TITLE,'script_sha256':script_sha,'script_current_at_finish':sha(pathlib.Path(__file__))==script_sha,'cadquery_version':cq.__version__,'matplotlib_version':matplotlib.__version__,'numpy_version':np.__version__,'renderer':'native STEP tessellation, true orthographic software Z-buffer, fixed same-scale views','board_sha256':input_sha,'input_current_at_finish':sha(boardpath)==input_sha,'catalog_sha256':hashlib.sha256(cat_bytes).hexdigest(),'board_cad_model_count':len(parts),'step_assembly_archives':STEP_EXPORTS,'exact_supplier_steps_hash_verified':True,'model_exceptions':'C_BULK drawing-corrected nominal height7.7; originals retained. J_MOTOR installed tails trimmed to documented assembly envelope.','component_models':models,'board_dimensions_mm':[b['width'],b['height'],th],'assembly_side':'top only; faces away from motor','motor':{'model':'14HM11-0404S','step_sha256':sha(motorfile),'pdf_sha256':sha(ref/'14HM11-0404S_Full_Datasheet.pdf'),'native_bbox_mm':bounds(motor_native),'drawing_max_body_mm':[35.2,35.2,28.2],'front_datum_native_z_mm':0,'rear_datum_native_z_mm':28.2,'shaft_projection_mm':24,'native_vertical_cylindrical_features':motor_cylinders,'front_mount':'4 × M3, 26 ±0.2 square, depth ≥4.0; official drawing','rear_mount':'BLOCKED: model shows existing endcap fastener recesses, not qualified separate rear mounting threads','leads':{'A+':'black','A-':'green','B+':'red','B-':'blue'},'drawing_revision_compatibility':'STEP header 2018; PDF dated 2025; confirm supplied motor revision'},'adapter':{'carrier_solid_count':len(carrier.Solids()),'type':'Separate front-M3 machined carrier; no drilling motor or removing endcap screws','proposed_material':'6061-T6/T651 aluminium; strength/heat/preload qualification pending','front_plate_mm':[49.2,36.4,4],'pilot_clearance_diameter_mm':22.15,'pilot_bore_tolerance_mm':.05,'pilot_root_relief_mm':{'diameter':23.4,'depth':.4,'tolerance':.05,'reason':'native STEP pilot root fillet reachesR11.5/depth0.23661; retaining22.15locating bore beyond relief'},'documented_motor_pilot_mm':[21.948,22.0],'maximum_motor_radial_play_in_pilot_mm':.126,'front_hole_diameter_mm':4.1,'front_pitch_mm':26,'rails_mm':[6,5],'rail_center_x_mm':[-21.6,21.6],'rear_return_mm':[13.85,5,4],'return_z_mm':[-6.8,-2.8],'pcb_boss_outer_diameter_mm':4.5,'pcb_boss_top_z_mm':-.8,'pcb_m2p5_through_thread_available_depth_mm':6,'motor_front_z_mm':front,'motor_rear_z_mm':rear,'rear_to_pcb_underside_mm':7.2,'intended_machining_tolerance_mm':.05,'hardware_envelopes':'PCB M2.5x8 with PEEK top washer0.5/lower support1.0; frontM3x8 with metalwasher0.5/plate4.0. See documented engagement/tolerance bounds. Nominal thread cylinders represent intentional engagement, not helical threads.','qualified':False},'component_intersections':pair,'component_clearances_under_0p2_mm':near,'pcb_fastener_clearances':mount,'pcb_fastener_all_component_lower_bounds':head_bounds,'substrate_penetrations':penetrations,'carrier_clearances':carrier_checks,'usb_access':{'envelope':'Selected Tensility maximum body12.5x32.5x7.6mm, +Ymouths17.9, native C-end STEP and reservedR30 bend; seeusb_same_edge_cable_fit.','checks':plug_checks,'physical_cable_sample_required':True},'bare_interface_top_probe_access':access,'motor_wire_access':'Native STEP leads exit towards −Y at native z≈24.25; mounted world z≈−11.95. Four side rails at X±21.6 keep central −Y harness corridor open. STEP lead stub is ~20 mm, PDF actual lead length 300±10 mm. Route motor wires outward −Y then to accessible board motor pads; harness shape/strain relief needs prototype.','intentional_contacts':['Carrier/front motor mounting plane','Support boss/PCB underside','Simplified screw nominal shanks versus minor-diameter thread pilot bores; intended threaded engagement, not helical-thread collision proof'],'limitations':['STEP solid collision tests are nominal supplier-model screens, not physical tolerance proof.','Copper detailed BREP and helical threads are outside mechanical STEP; solder tails, insulation and harness are bounded installation envelopes.','Support strength, thermal transfer, host front-shaft installation, screw procurement and torque/preload need prototype qualification.','No direct rear mounting thread pattern is verified; carrier is a separate candidate.'],'mechanical_release':'BLOCKED_PENDING_PROTOTYPE_AND_MODEL_FINDING_REVIEW','manufacturing_ready':False}
load=20.;E=69000.;L=-2.8-(front-4);Irail=6*5**3/12;Iarm=5*4**3/12;rail_delta=load*L**3/(3*E*Irail);arm_delta=load*13.85**3/(3*E*Iarm)
report['carrier_provisional_cantilever_screen']={'assumption':'20 N lateral load assigned to one rail and one return; unqualified procurement allowance, not a tested cable force','elastic_modulus_mpa':E,'assumed_room_temperature_yield_mpa':240,'rail_length_mm':L,'rail_inertia_mm4':Irail,'rail_tip_deflection_mm':rail_delta,'return_tip_deflection_mm':arm_delta,'combined_deflection_mm':rail_delta+arm_delta,'rail_bending_stress_mpa':load*L*2.5/Irail,'return_bending_stress_mpa':load*13.85*2/Iarm,'scope':'Euler-Bernoulli simple beam screen only. Excludes front plate/joints, torsion, PCB flex, notch effects, screw preload/fatigue, thermal strength and dynamic motor vibration; does not qualify carrier.'}
bulk_record=next(e for e in models if e['reference']=='C_BULK')
bulk_cid=cat['components']['C_BULK'];matched_bulk=bulk_cid=='C178585';native_bulk_height=bounds(parts['C_BULK'])[5]-bounds(parts['C_BULK'])[2];bulk_model_height_matches=matched_bulk and 7.4<=native_bulk_height<=8.1
report['supplier_cad_dimensional_review']=[{'reference':'C_BULK','supplier':bulk_cid,'mpn':cat['parts'][bulk_cid]['manufacturerPartNumber'],'native_step_height_mm':bounds(parts['C_BULK'])[5]-bounds(parts['C_BULK'])[2],'world_top_z_mm':bounds(parts['C_BULK'])[5],'manufacturer_nominal_diameter_height_mm':[6.3,7.7] if matched_bulk else [6.3,5.4],'height_tolerance_mm':.3 if matched_bulk else None,'status':'NOMINAL_MANUFACTURER_MODEL_MATCH' if bulk_model_height_matches else 'USER_REVIEW','interpretation':'C178585 Panasonic100uF35V has manufacturer7.7±0.3mm body but native supplier STEP measures5.82mm. Preserved short supplier model is not mechanically exact; use independent maximum manufacturer envelope and physical sample for clearance. This remains USER_REVIEW.' if matched_bulk and not bulk_model_height_matches else 'Nominal supplier STEP height agrees with known manufacturer range; physical tolerance/sample qualification remains necessary.' if matched_bulk else 'Original supplier model provides a conservative taller envelope; manufacturer drawing/sample must resolve native model versus catalog height discrepancy.'}]
if matched_bulk:
 m=bulk_record['cad_record'];angle=math.radians(m['rotation']['z']);localxy=np.array([m['model_origin_position']['x'],m['model_origin_position']['y']]);rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);center=np.array([m['position']['x'],m['position']['y']])-rot@localxy
 # Panasonic D8: D6.3±0.5, A/B6.6±0.2,H7.8max,L7.7±0.3; add0.3max stand-off vertically.
 package_max=box(7.8,6.8,8.3,z=4.15).rotate((0,0,0),(0,0,1),m['rotation']['z']).translate((center[0],center[1],.8));bulk_box=bounds(package_max);edge=min(b['width']/2-max(abs(bulk_box[0]),abs(bulk_box[3])),b['height']/2-max(abs(bulk_box[1]),abs(bulk_box[4])))
 report['bulk_capacitor_manufacturer_maximum_envelope_screen']={'manufacturer_d8_nominal_dimensions_mm':{'diameter':6.3,'length':7.7,'A_B':6.6},'manufacturer_tolerances_mm':{'diameter_plus_minus':.5,'A_B_plus_minus':.2,'length_plus_minus':.3,'stand_off_max':.3,'H_max':7.8},'conservative_maximum_package_bbox_dimensions_mm':[7.8,6.8,8.3],'world_maximum_envelope_bbox_mm':bulk_box,'purpose':'Package7.8×6.8×8.3 includes maximum base/body diameter and an additional0.3mm vertical stand-off allowance; bodyoversizing mustnotapply heighttolerance laterally','body_to_board_nominal_edge_lower_bound_mm':edge,'body_to_board_edge_after_0p2mm_outline_tolerance_mm':edge-.2,'placement_tolerance_not_included':True,'maximum_envelope_potential_intersections':[{'reference':n,'intersection_mm3':volume(package_max,s),'interpretation':'conservative rectangular maximum-package screening, not a substituted component model'} for n,s in parts.items() if n!='C_BULK' and broad(package_max,s) and volume(package_max,s)>1e-5],'pcb_head_distance_lower_bounds_after_0p35mm_hole_play':[{'hardware':h,'remaining_mm':max(0,bbox_distance(hs,package_max)-.35)} for h,hs in heads.items()]}
report['native_pad_to_fastener_keepout_screen']=pad_head_screen
report['usb_same_edge_cable_fit']={'cables':{'PD':'Tensility10-06137 C-C3m 20V3A','DATA':'Tensility10-06139 A-C1m USB2'},'maximum_body_mm':[12.5,32.5,7.6],'port_center_pitch_mm':14,'maximum_envelope_pair_clearance_mm':plug['J_PD'].distance(plug['J_DATA']),'after_0p1mm_placement_per_port_mm':plug['J_PD'].distance(plug['J_DATA'])-.2,'native_cable_pair_distance_mm':cable_parts['J_PD_selected_cable'].distance(cable_parts['J_DATA_selected_cable']),'bend_reserved_radius_mm':30,'bend_radius_is_manufacturer_verified':False,'cable_maximum_od_mm':3.95,'host_keepout_bbox_mm':bounds(cq.Compound.makeCompound(list(plug.values())+list(cable_parts.values()))),'body_height_envelope_note':'Factory CAD7.378mm exceeds PDF7.3mm maximum; reserve7.6mm and resolve with supplier/sample.','status':'Nominal CAD/max-envelope screen; simultaneous physical insertion, shoulder registration and bend-life qualification unperformed.'}

report['mounted_assembly_bbox_mm']=bounds(cq.Compound.makeCompound([pcb,motor,carrier]+list(parts.values())+list(hardware.values())))
report['nominal_no_component_intersections']=not pair
report['nominal_no_fastener_intersections']=all(e['intersection_mm3']<1e-5 for e in mount)
report['nominal_no_carrier_intersections']=all(e['intersection_mm3']<1e-5 for e in carrier_checks)
report['nominal_no_plug_envelope_intersections']=all(e['intersection_mm3']<1e-5 for e in plug_checks)
report['usb_coordinate_datums']=[{'reference':e['reference'],'step_body_bbox_center_mm':[(e['world_bbox_mm'][i]+e['world_bbox_mm'][i+3])/2 for i in range(3)],'native_pcb_component_center_mm':pcbcomponents[e['cad_record']['pcb_component_id']]['center'],'cad_anchor_mm':e['cad_record']['position'],'cad_model_origin_mm':e['cad_record']['model_origin_position'],'rotation_deg':e['cad_record']['rotation'],'mouth_xy_mm':usb_mouths[e['reference']], 'outward_direction':'+Y','pickup_and_pin1_status':'USER_REVIEW: bodybbox/CADanchor/nativePCBbbox are distinct. No verified JLCmachine pickup/pin1 convention; actual assemblyplacementpreview required.'} for e in models if e['reference'] in ['J_PD','J_DATA']]
service_wire_checks=[]
for n,w in service_parts.items():
 if not n.startswith(('Wire_','FactoryLead_')):continue
 for label,target in [('carrier',carrier),('motor',motor),('PCB',pcb)]+list(parts.items()):
  if label=='J_MOTOR':continue
  if broad(w,target):
   v=volume(w,target);service_wire_checks.append({'wire':n,'other':label,'intersection_mm3':v,'distance_mm':w.distance(target)})
for (n,w),(m,t) in itertools.combinations([(n,w)for n,w in service_parts.items()if n.startswith(('Wire_','FactoryLead_'))],2):
 if broad(w,t):
  common=w.intersect(t);v=max(0,common.Volume());same_pin=n.rsplit('_',1)[-1]==m.rsplit('_',1)[-1] and n.startswith('FactoryLead_')!=m.startswith('FactoryLead_');allowed=0
  if same_pin and v>1e-5:allowed=max(0,common.intersect(service_parts['Splice_insulation_'+n.rsplit('_',1)[-1]]).Volume())
  service_wire_checks.append({'wire':n,'other':m,'intersection_mm3':max(0,v-allowed),'intentional_corresponding_splice_envelope_contact_mm3':allowed,'distance_mm':w.distance(t)})
service_report['wire_clearance_checks']=service_wire_checks
service_report['nominal_wire_collision_free']=all(v['intersection_mm3']<1e-5 for v in service_wire_checks)
service_report['native_header_model_post_review']={'supplier_model_square_post_mm':.6,'manufacturer_recommended_finished_bore_mm':[.7,.8],'supplier_model_post_diagonal_mm':math.sqrt(2)*.6,'native_model_substrate_intersection_mm3':next((e['intersection_with_drilled_substrate_mm3']for e in penetrations if e['reference']=='J_MOTOR'),None),'status':'UNRESOLVED_MODEL_DISCREPANCY: generic supplier solid has oversized square posts relative to manufacturer recommended holes. Do not infer actual post dimensions from this model. Manufacturer drawing governs drilling; obtain exact manufacturer post CAD or inspect actual header/coupon before fit qualification. Native STEP intentionally retained; no collision hidden by trimming cross-section.'}
service_report['plug_removal_envelope_collisions']=[{'part':n,'intersection_mm3':volume(motor_access,s)} for n,s in parts.items() if n!='J_MOTOR' and broad(motor_access,s) and volume(motor_access,s)>1e-5]
service_report['barrier_to_trimmed_header_clearance_mm']=parts['J_MOTOR'].distance(service_parts['Nomex410_INS001'])
service_report['carrier_with_harness_bbox_mm']=bounds(cq.Compound.makeCompound([carrier]+list(service_parts.values())+list(cable_parts.values())))
service_report['nominal_connector_to_neighbours']=[{'part':n,'distance_mm':parts['J_MOTOR'].distance(s),'after_0p1mm_placement_per_part_mm':parts['J_MOTOR'].distance(s)-.2} for n,s in parts.items() if n!='J_MOTOR' and broad(parts['J_MOTOR'],s,1)]
header_bounds=bounds(parts['J_MOTOR']); housing_bounds=bounds(service_parts['PHR4_mating_housing_envelope'])
inside_screen=[]
for label,bb in [('native_header',header_bounds),('PHR4_mating_housing',housing_bounds)]:
 margin=min(bb[0]+b['width']/2,bb[1]+b['height']/2,b['width']/2-bb[3],b['height']/2-bb[4])
 inside_screen.append({'part':label,'bbox_mm':bb,'nominal_edge_margin_mm':margin,'after_0p2_outline_0p1_placement_mm':margin-.3})
 assert margin-.3>0,('JST body edge clearance',label,margin)
service_report['full_connector_inside_board_screen']=inside_screen
report['service_harness']=service_report
report['adapter'].update({'front_hardware':'M3x8 ISO4762 with0.5mm washer; plate4.00+/-0.05mm; bounded thread engagement3.2..3.8mm below documented4mm minimum depth','front_hole_pattern_tolerance_mm':.05,'front_hole_min_radial_clearance_mm':.525,'required_diagonal_pattern_misalignment_mm':.354,'host_front_face_z_mm':front-8,'pcb_boss_top_z_mm':-1.8,'pcb_hardware':'M2.5x8 ISO4762 bounded head diameter4.5, PEEK top washer0.5, PEEK lower support1mm; nominal metal engagement4.9mm','nominal_metal_engagement_mm':4.9,'host_front_threads':'4xM3 at X+/-21.6,Y+/-13, 6mm available, 4.5..5.5mm engagement'})
report['mounted_assembly_bbox_mm']=bounds(cq.Compound.makeCompound([pcb,motor,carrier]+list(parts.values())+list(hardware.values())+list(service_parts.values())+list(cable_parts.values())))
(OUT/'service-harness-review.json').write_text(json.dumps(service_report,indent=2)+'\n')
cq.exporters.export(cq.Compound.makeCompound(list(service_parts.values())),str(OUT/'harness-and-insulation.step'));compress_step(OUT/'harness-and-insulation.step')

report['artifact_hashes']={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='mechanical-review.json'}
(OUT/'mechanical-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['board_cad_model_count','component_intersections','component_clearances_under_0p2_mm','pcb_fastener_clearances','substrate_penetrations','nominal_no_carrier_intersections','nominal_no_plug_envelope_intersections']},indent=2),flush=True)

assert not pair and all(e["intersection_mm3"]<1e-5 for e in mount),"Actual component/head collision"
assert report["nominal_no_carrier_intersections"],"Carrier collision; correct geometry"
assert service_report["nominal_wire_collision_free"],"Harness wire collision; correct geometry"
assert not service_report["plug_removal_envelope_collisions"],"Motor plug access collision"
assert all(e["intersection_mm3"]<1e-5 for e in plug_checks),"Selected USB body envelope collision"
