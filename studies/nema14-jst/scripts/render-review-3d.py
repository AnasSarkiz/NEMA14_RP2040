"""NEMA14 JST review views from native CAD transforms and supplier OBJ geometry.
These are engineering views, not proof of cable handling or routed copper.
"""
from pathlib import Path
import json,math,hashlib
import numpy as np
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'artifacts/final-source.circuit.json'; data=p.read_bytes(); b=json.loads(data)
cat=json.loads((ROOT/'src/jlcpcb-catalog.json').read_text())
plug=json.loads((ROOT/'artifacts/side-entry-plug.json').read_text())
assert plug['board_sha256']==hashlib.sha256(data).hexdigest()
src={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'}
pcs={src[e['source_component_id']]:e for e in b if e['type']=='pcb_component'}
cache={};models=[]
def rot(axis,degrees):
 a=math.radians(degrees);c,s=math.cos(a),math.sin(a)
 return [np.array([[1,0,0],[0,c,-s],[0,s,c]]),np.array([[c,0,s],[0,1,0],[-s,0,c]]),np.array([[c,-s,0],[s,c,0],[0,0,1]])][axis]
for e in b:
 if e['type']!='cad_component' or not e.get('model_obj_url'):continue
 name=src[e['source_component_id']]
 if pcs[name].get('do_not_place'):continue
 part=cat['parts'][cat['components'][name]]; path=ROOT/next(q for q in part['modelFiles'] if q.endswith('.obj'))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==part['sha256']['obj']
 key=str(path)
 if key not in cache:
  vs=[];fs=[]
  for line in path.read_text().splitlines():
   if line.startswith('v '):vs.append([float(x) for x in line.split()[1:4]])
   elif line.startswith('f '):
    ids=[int(x.split('/')[0])-1 for x in line.split()[1:]]
    for i in range(1,len(ids)-1):fs.append([ids[0],ids[i],ids[i+1]])
  cache[key]=(np.array(vs),np.array(fs))
 vs,fs=cache[key];vs=vs-np.array([e['model_origin_position'][q] for q in 'xyz'])
 for i,q in enumerate('xyz'):vs=vs@rot(i,e['rotation'][q]).T
 vs+=np.array([e['position'][q] for q in 'xyz'])
 color='#353a44' if name.startswith(('U_','Q_')) else '#a88b5e' if name.startswith('C_') else '#c1c8cb' if name.startswith('J_') else '#535c63'
 models.append((vs[fs],color,name))
board=next(e for e in b if e['type']=='pcb_board')
holes=[e for e in b if e['type']=='pcb_hole' and not e.get('pcb_component_id')]
slab=cq.Workplane('XY').box(board['width'],board['height'],board['thickness'])
for h in holes:slab=slab.cut(cq.Workplane('XY').circle(h['hole_diameter']/2).extrude(board['thickness']+2,both=True).translate((h['x'],h['y'],0)))
verts,tri=slab.val().tessellate(.1);board_faces=np.array([[v.x,v.y,v.z] for v in verts])[np.array(tri)]
# Use Blender's depth buffer rather than painter-sorted plotting collections.
import subprocess,sys
payload={'board_sha256':hashlib.sha256(data).hexdigest(),'plug':plug,'models':[],'parts':pcs}
for triangles,color,name in [(board_faces,'#176859','PCB')]+models:
 payload['models'].append({'name':name,'color':color,'vertices':triangles.reshape(-1,3).tolist(),'faces':np.arange(triangles.size//3).reshape(-1,3).tolist()})
for pad in b:
 if pad['type']!='pcb_smtpad' or pad.get('layer')!='bottom':continue
 w,h=pad['width'],pad['height'];r=math.radians(pad.get('ccw_rotation',0));c,s=math.cos(r),math.sin(r);radius=min(w,h)/2;offset=abs(w-h)/2;points=[]
 for a in np.linspace(0,2*np.pi,48,endpoint=False):
  dx,dy=radius*np.cos(a),radius*np.sin(a)
  if w>=h:dx+=offset*(1 if dx>=0 else -1)
  else:dy+=offset*(1 if dy>=0 else -1)
  points.append([pad['x']+c*dx-s*dy,pad['y']+s*dx+c*dy,-.815])
 payload['models'].append({'name':pad['pcb_smtpad_id'],'color':'#e5bf65','vertices':points,'faces':[list(range(len(points)))]})
mesh_path=ROOT/'.config/review-meshes.json';mesh_path.parent.mkdir(exist_ok=True);mesh_path.write_text(json.dumps(payload,separators=(',',':')))
subprocess.run(['blender','--background','--threads','4','--python',str(ROOT/'scripts/blender-review.py'),'--',str(ROOT),str(mesh_path)],check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/label-review.py')],check=True)
print('NEMA14 JST 3D review images generated from',payload['board_sha256'])
