"""Check actual rendered endpoints against the native header and JST catalog.

Checks the 4 electrical contacts separately from the 2 solder hold-downs.
It does not certify crimp workmanship, latch tolerances or physical assembly.
"""
import hashlib,json,math,pathlib
import cadquery as cq
import numpy as np

root=pathlib.Path(__file__).resolve().parents[1]
board_bytes=(root/'index.circuit.json').read_bytes();board=json.loads(board_bytes)
assembly=json.loads((root/'assembly.circuit.json').read_text())
assert assembly[:len(board)]==board
assert (root/'artifacts/board.circuit.json').read_bytes()==board_bytes
names={e['source_component_id']:e['name'] for e in assembly if e['type']=='source_component'}
def cad(name):return next(e for e in assembly if e['type']=='cad_component' and names.get(e.get('source_component_id'))==name)
header=cad('J_MOTOR');motor=cad('MOTOR_REFERENCE_CONCEPT');plug=cad('JST_SHR_04V_S_PLUG')
assert '_nowires_' in motor['model_glb_url'] and 'jst' not in motor['model_glb_url'].lower()
assert not any(e['type']=='cad_cable' for e in assembly), 'An inferred two-ended connector cable would restore the fake motor socket'
assert header['rotation']['x']==header['rotation']['y']==0
theta=math.radians(header['rotation']['z']);ct,st=math.cos(theta),math.sin(theta)
def header_world(x,y,z):
 o=header['model_origin_position'];p=header['position'];x-=o['x'];y-=o['y']
 return np.array([p['x']+ct*x-st*y,p['y']+st*x+ct*y,p['z']+z-o['z']])
def near(a,b,tol=1e-7):assert np.linalg.norm(np.array(a)-np.array(b))<tol,(a,b)

sid=header['source_component_id'];sp={e['source_port_id']:e for e in board if e['type']=='source_port'}
ports={sp[e['source_port_id']]['pin_number']:e for e in board if e['type']=='pcb_port' and sp[e['source_port_id']]['source_component_id']==sid}
roles=['A_PLUS','A_MINUS','B_PLUS','B_MINUS'];colors=['black','green','red','blue']
for pin in range(1,5):
 assert sp[ports[pin]['source_port_id']]['name']==roles[pin-1]
 if pin<4:assert abs(math.hypot(ports[pin+1]['x']-ports[pin]['x'],ports[pin+1]['y']-ports[pin]['y'])-1)<1e-5
for pin in [5,6]:assert sp[ports[pin]['source_port_id']].get('do_not_connect')

# Native STEP occupancy at each pin, and empty space halfway between pins,
# corroborates the contact-row landing. Contacts/plastic share a STEP solid.
step=root/'imports/supplier'/header['model_step_url'].split('/imports/supplier/')[1]
shape=cq.importers.importStep(str(step)).val()
for pin in range(4):assert shape.isInside(cq.Vector(pin,.35,2),1e-6)
for pin in range(3):assert not shape.isInside(cq.Vector(pin+.5,.35,2),1e-6)

plan=plug['model_jscad']['shape'];assert plan['type']=='subtract'
box=plan['shapes'][0];size=box['shape']['size'];center=box['vector']
near(size[:2],[5,2.8]);assert abs(plug['rotation']['z']-header['rotation']['z'])<1e-8
near([plug['position']['x'],plug['position']['y']],header_world(1.5,0,0)[:2])
board_surface=next(e for e in board if e['type']=='pcb_board')['thickness']/2
top=center[2]+size[2]/2;bottom=center[2]-size[2]/2
assert abs(top-board_surface-6.3)<1e-8, 'JST catalog mated height is 6.3 mm'
assert abs(bottom-header_world(1.5,0,4.25)[2])<1e-8, 'Exposed plug must touch the native header rim'
assert abs(top-5-(board_surface+1.3))<1e-8, 'The full 5 mm housing inserts below the header mouth'

# Check the native motor transform, rather than merely moving the wire drawing.
orientation=np.eye(3)
for axis in 'xyz':
 angle=math.radians(motor['rotation'][axis]);c,s=math.cos(angle),math.sin(angle)
 rotation={'x':[[1,0,0],[0,c,-s],[0,s,c]],'y':[[c,0,s],[0,1,0],[-s,0,c]],'z':[[c,-s,0],[s,c,0],[0,0,1]]}[axis]
 orientation=np.array(rotation)@orientation
near(orientation@np.array([0,-1,0]),[0,1,0])
assert header['position']['y']>0

definition=json.loads((root/'artifacts/top-assembly/harness-definition.json').read_text())
rows=[]
for i,wire in enumerate(definition['wires']):
 wire_cad=cad('MOTOR_LEAD_PIN_'+str(i+1))
 assert wire_cad['position']==dict(x=0,y=0,z=0) and wire_cad['rotation']==dict(x=0,y=0,z=0)
 assert wire['pin']==i+1 and wire['net']==roles[i] and wire['color']==colors[i]
 colored=wire_cad['model_jscad'];near(colored['color'],wire['rgb'])
 cylinders=[s for s in colored['shape']['shapes'] if s['type']=='translate' and s['shape']['type']=='rotate']
 actual=cylinders[-1];rotation=actual['shape'];assert rotation['shape']['type']=='cylinder'
 polar,azimuth=rotation['angles'][1:];axis=np.array([math.sin(polar)*math.cos(azimuth),math.sin(polar)*math.sin(azimuth),math.cos(polar)])
 mid=np.array(actual['vector']);length=rotation['shape']['height'];end=mid+axis*length/2
 expected=header_world(i,.35,2)
 near(end[:2],expected[:2]);assert abs(end[2]-(top-.7))<1e-8
 near([wire['path'][-1][k] for k in 'xyz'],end)
 near([wire['header_contact'][k] for k in 'xyz'],expected)
 hole=plan['shapes'][i+1]
 near(hole['vector'][:2],[i-1.5,.35]);assert hole['shape']['radius']>rotation['shape']['radius']
 # Verify the first *rendered* conductor starts at the case feedthrough.
 first=cylinders[0];a=np.array(first['vector']);r=first['shape'];pol,az=r['angles'][1:];direction=np.array([math.sin(pol)*math.cos(az),math.sin(pol)*math.sin(az),math.cos(pol)])
 start=a-direction*r['shape']['height']/2
 near(start,[wire['path'][0][k] for k in 'xyz']);assert 17.4<start[1]<17.7 and abs(start[0])<3
 rows.append({'pin':i+1,'coil':roles[i],'factory_color':colors[i],'rendered_wire_endpoint_xyz_mm':end.tolist(),'native_header_contact_xy_mm':expected[:2].tolist(),'aligned':True})

report={'passed':True,'board_sha256':hashlib.sha256(board_bytes).hexdigest(),
 'assembly_sha256':hashlib.sha256((root/'assembly.circuit.json').read_bytes()).hexdigest(),
 'motor_wire_outlet_faces_JST_board_edge':True,'motor_exit_board_side':'+Y','motor_has_no_JST_socket':True,'factory_leads_and_insulated_pigtail_splices':True,
 'board_header':'BM04B-SRSS-TB(LF)(SN)','mating_housing':'SHR-04V-S','crimp_contact':'SSH-003T-P0.2-H',
 'electrical_contact_pitch_mm':1,'mounting_tabs_excluded_from_pin_axis':True,
 'catalog_mated_height_mm':6.3,'rendered_mated_height_mm':top-board_surface,
 'full_housing_insertion_depth_mm':bottom-(top-5),
 'native_STEP_contact_region_occupancy_verified':True,'pin_mapping':rows,
 'pigtail':{'awg':28,'insulation_OD_mm':.6,'JST_approved_awg':[32,28],'JST_approved_insulation_OD_mm':[.4,.8]},
 'manufacturer_document':{'path':'references/jst/SH-connector.pdf','url':'https://www.jst-mfg.com/product/pdf/eng/eSH.pdf','sha256':hashlib.sha256((root/'references/jst/SH-connector.pdf').read_bytes()).hexdigest()},
 'physical_crimp_and_latch_tested':False,'concealed_housing_stem_and_contact_geometry_not_rendered':True}
(root/'artifacts/top-assembly/harness-connection-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
