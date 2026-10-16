"""Independently inspect the exported GLB mesh, its units and wire materials."""
import hashlib,json,pathlib,struct
import numpy as np

root=pathlib.Path(__file__).resolve().parents[1]
data=(root/'artifacts/top-assembly/assembled.glb').read_bytes()
assert data[:4]==b'glTF'
json_size=struct.unpack_from('<I',data,12)[0]
gltf=json.loads(data[20:20+json_size]);binary=data[28+json_size:]
nodes=gltf['nodes'];world={}
def matrix(node):
 if 'matrix' in node:return np.array(node['matrix']).reshape((4,4),order='F')
 x,y,z,w=node.get('rotation',[0,0,0,1]);rotation=np.array([
  [1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
  [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
  [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 m=np.eye(4);m[:3,:3]=rotation@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m
def visit(index,parent):
 world[index]=parent@matrix(nodes[index])
 for child in nodes[index].get('children',[]):visit(child,world[index])
for index in gltf['scenes'][gltf.get('scene',0)]['nodes']:visit(index,np.eye(4))
def geometry(name):
 matches=[i for i,n in enumerate(nodes) if n.get('name')==name];assert len(matches)==1,(name,matches)
 positions=[];colors=[]
 def collect(i):
  node=nodes[i]
  if 'mesh' in node:
   for primitive in gltf['meshes'][node['mesh']]['primitives']:
    accessor=gltf['accessors'][primitive['attributes']['POSITION']];assert accessor['type']=='VEC3' and accessor['componentType']==5126
    view=gltf['bufferViews'][accessor['bufferView']];offset=view.get('byteOffset',0)+accessor.get('byteOffset',0)
    p=np.ndarray((accessor['count'],3),dtype='<f4',buffer=binary,offset=offset,strides=(view.get('byteStride',12),4)).astype(float)
    p=np.column_stack([p,np.ones(len(p))])@world[i].T
    # The native exporter uses (x,y,z)->(-x,z,y), also visible in the
    # unchanged PCB connector node translations. Undo that proper rotation.
    positions.append(np.column_stack([-p[:,0],p[:,2],p[:,1]]))
    material=gltf['materials'][primitive['material']]
    colors.append(material['pbrMetallicRoughness']['baseColorFactor'][:3])
  for child in node.get('children',[]):collect(child)
 collect(matches[0]);assert positions,name
 return np.vstack(positions),colors

harness=json.loads((root/'artifacts/top-assembly/harness-definition.json').read_text())
rows=[]
for wire in harness['wires']:
 pin=wire['pin'];points,colors=geometry('MOTOR_LEAD_PIN_'+str(pin))
 assert all(np.linalg.norm(np.array(c)-wire['rgb'])<1e-6 for c in colors),(pin,colors,wire['rgb'])
 gaps=[]
 for i,(a,b) in enumerate(zip(wire['path'],wire['path'][1:])):
  aa=np.array([a[k] for k in 'xyz']);ab=np.array([b[k] for k in 'xyz']);delta=ab-aa
  t=np.clip(((points-aa)@delta)/np.dot(delta,delta),0,1)
  distances=np.linalg.norm(points-aa-t[:,None]*delta,axis=1)
  radius=wire['segment_radii_mm'][i]
  gaps.append(distances-radius)
 maximum=float(np.min(np.vstack(gaps),axis=0).max())
 assert maximum<5e-5,('Exported wire escapes its checked path; check rotation units or origin',pin,maximum)
 endpoint=np.array([wire['path'][-1][k] for k in 'xyz'])
 cap=np.logical_and(np.abs(points[:,2]-endpoint[2])<5e-5,np.abs(np.linalg.norm(points[:,:2]-endpoint[:2],axis=1)-wire['pigtail_radius_mm'])<5e-5)
 assert int(cap.sum())>=8,('No rendered terminal ring at its verified PCB contact',pin)
 rows.append({'pin':pin,'color':wire['color'],'material_matches_factory_color':True,
  'rendered_terminal_ring_vertices':int(cap.sum()),'maximum_mesh_excursion_beyond_checked_wire_mm':maximum})
 splice_points,splice_colors=geometry('MOTOR_SPLICE_PIN_'+str(pin))
 assert all(np.linalg.norm(np.array(c)-[.06,.06,.06])<1e-6 for c in splice_colors)
 splice=wire['splice'];a=np.array([splice['from'][k] for k in 'xyz']);b=np.array([splice['to'][k] for k in 'xyz']);delta=b-a
 t=np.clip(((splice_points-a)@delta)/np.dot(delta,delta),0,1)
 assert (np.linalg.norm(splice_points-a-t[:,None]*delta,axis=1)-splice['radius']).max()<5e-5

plug,_=geometry('JST_SHR_04V_S_PLUG')
assert abs(float(plug[:,2].min())-harness['header_top_z_mm'])<5e-5
assert abs(float(plug[:,2].max())-harness['housing_top_z_mm'])<5e-5
assert abs(float(plug[:,2].max())-harness['board_surface_z_mm']-6.3)<5e-5
report={'passed':True,'glb_sha256':hashlib.sha256(data).hexdigest(),
 'rendered_meshes_follow_verified_conductor_paths':True,'actual_mesh_contact_rings_match_board_pins':True,
 'actual_mesh_materials_match_factory_colors':True,'actual_exported_housing_is_seated':True,
 'pin_checks':rows,'physical_assembly_tested':False}
(root/'artifacts/top-assembly/harness-mesh-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
