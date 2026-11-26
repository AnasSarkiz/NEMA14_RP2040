"""Blender 4.3 background renderer for NEMA14 JST; called by render-review-3d.py."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
args=sys.argv[sys.argv.index('--')+1:];root=Path(args[0]);p=json.loads(Path(args[1]).read_text());out=root/'review';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False
scene.render.resolution_x=1500;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.color=(.8,.8,.8);scene.view_settings.view_transform='Standard'
def rgb(h):return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
mats={}
def mat(color):
 if color not in mats:
  m=bpy.data.materials.new(color);m.diffuse_color=(*rgb(color),1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*rgb(color),1);n.inputs['Roughness'].default_value=.5;mats[color]=m
 return mats[color]
for item in p['models']:
 mesh=bpy.data.meshes.new(item['name']);mesh.from_pydata(item['vertices'],[],item['faces']);mesh.update();o=bpy.data.objects.new(item['name'],mesh);scene.collection.objects.link(o);o.data.materials.append(mat(item['color']))
def line(name,points,color,width=.04):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=width;curve.bevel_resolution=2;poly=curve.splines.new('POLY');poly.points.add(len(points)-1)
 for q,point in zip(poly.points,points):q.co=(*point,1)
 ob=bpy.data.objects.new(name,curve);scene.collection.objects.link(ob);ob.data.materials.append(mat(color));return ob
for x in [-13,13]:
 for y in [-13,13]:
  for z in [-.83,.83,3.8]:
   for i in range(12):
    a=i*2*math.pi/12;pts=[(x+3.2*math.cos(a+t),y+3.2*math.sin(a+t),z) for t in [0,.15,.3]];line('Screw reserve',pts,'#d8473d',.035)
for key,color in [('housing','#0c9aaf'),('withdrawal_sweep','#0c9aaf'),('service_grip_envelope','#9462b3')]:
 q=p['plug'][key];a,z=q['min'],q['max'];vs=[(x,y,zv) for x in [a[0],z[0]] for y in [a[1],z[1]] for zv in [a[2],z[2]]]
 for i,j in [(0,1),(0,2),(0,4),(1,3),(1,5),(2,3),(2,6),(3,7),(4,5),(4,6),(5,7),(6,7)]:line(key,[vs[i],vs[j]],color,.035)
bpy.ops.object.camera_add(location=(42,-62,95));camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=52
for location,power,size in [((0,0,65),80000,55),((-45,-25,35),40000,40),((0,0,-65),80000,55)]:
 bpy.ops.object.light_add(type='AREA',location=location);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
for side,loc in [('top',(42,-62,95)),('bottom',(42,-62,-95))]:
 camera.location=loc;camera.rotation_euler=(Vector((2,0,0))-camera.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
 scene.render.filepath=str(out/f'{side}-3d-raw.png');bpy.ops.render.render(write_still=True)
 labels=[]
 if side=='top':
  for name in ['U_MCU','U_DRV','U_IA','U_IB','R_SHUNT_A','R_SHUNT_B','J_MOTOR','J_PD','J_DATA']:
   pc=p['parts'][name];q=world_to_camera_view(scene,camera,Vector((pc['center']['x'],pc['center']['y'],3.5)));labels.append({'name':name,'x':q.x*1500,'y':(1-q.y)*1300})
 else:
  q=world_to_camera_view(scene,camera,Vector((0,0,-.82)));labels=[{'name':'U_ENCODER · DNP · axis (0, 0)','x':q.x*1500,'y':(1-q.y)*1300}]
 (out/f'{side}-labels.json').write_text(json.dumps(labels))
