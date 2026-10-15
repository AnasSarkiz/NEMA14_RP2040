"""Check the actual assembly path and proposed hardware against supplier geometry.

This nominal CAD check does not qualify the motor rear attachment or hardware.
"""
import hashlib,itertools,json,math,pathlib
import cadquery as cq
root=pathlib.Path.cwd();j=json.loads((root/'assembly.circuit.json').read_text());native=(root/'artifacts/board.circuit.json').read_bytes();names={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'};dnp={e['source_component_id'] for e in j if e['type']=='pcb_component' and e.get('do_not_place')};parts={};cache={};bounds={};conservative=[]
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def broad(a,b):return all(a[i+3]>=b[i] and b[i+3]>=a[i] for i in range(3))
def lower(a,b):return math.sqrt(sum(max(a[i]-b[i+3],b[i]-a[i+3],0)**2 for i in range(3)))
def add(name,s):parts[name]=s;bounds[name]=bb(s)
for e in j:
 if e['type']!='cad_component' or not e.get('model_step_url') or e.get('source_component_id') in dnp:continue
 name=names[e['source_component_id']];url=e['model_step_url'];p=root/'imports/supplier'/url.split('/imports/supplier/')[-1]
 if str(p) not in cache:cache[str(p)]=cq.importers.importStep(str(p)).val()
 s=cache[str(p)]
 if not s.isValid():
  assert name in ['J_PD','J_DATA'];b=bb(s);s=cq.Workplane('XY').box(*(b[i+3]-b[i] for i in range(3))).val().translate(tuple((b[i+3]+b[i])/2 for i in range(3)));conservative.append(name)
 o=e.get('model_origin_position',dict(x=0,y=0,z=0));s=s.translate(tuple(-o[k] for k in 'xyz'))
 for a,v in [('x',(1,0,0)),('y',(0,1,0)),('z',(0,0,1))]:
  if e['rotation'][a]:s=s.rotate((0,0,0),v,e['rotation'][a])
 s=s.translate(tuple(e['position'][k] for k in 'xyz'));add(name,s)
def from_plan(plan):
 t=plan['type']
 if t=='colorize':return from_plan(plan['shape'])
 if t=='translate':return from_plan(plan['shape']).translate(tuple(plan['vector']))
 if t=='cylinder':return cq.Workplane('XY').circle(plan['radius']).extrude(plan['height']).val().translate((0,0,-plan['height']/2))
 if t=='cuboid':return cq.Workplane('XY').box(*plan['size']).val()
 if t in ['union','subtract']:
  shapes=[from_plan(q) for q in plan['shapes']];shape=shapes[0]
  for other in shapes[1:]:shape=shape.fuse(other) if t=='union' else shape.cut(other)
  return shape
 raise AssertionError('Unreviewed mechanical CAD operation: '+t)
head_names=[];spacer_names=[]
for e in j:
 if e['type']!='cad_component':continue
 name=names.get(e.get('source_component_id'),'')
 if not name.startswith('PROPOSED_'):continue
 assert e['rotation']==dict(x=0,y=0,z=0) and e['model_unit_to_mm_scale_factor']==1
 x,y,z=(e['position'][a] for a in 'xyz');assert (x,y) in set(itertools.product([-13,13],repeat=2)) and z==0
 shape=from_plan(e['model_jscad']).translate((x,y,z))
 if name.startswith('PROPOSED_M3_SCREW'):
  head_names.append(name);expected=[x-2,y-2,-5.2,x+2,y+2,3.8]
 else:
  assert name.startswith('PROPOSED_SPACER');spacer_names.append(name);expected=[x-2.5,y-2.5,-6.8,x+2.5,y+2.5,-.8]
 assert all(abs(a-b)<1e-5 for a,b in zip(bb(shape),expected)), 'Actual assembly hardware envelope changed'
 add(name,shape)
assert len(head_names)==len(spacer_names)==4
for x,y in itertools.product([-13,13],repeat=2):
 add(f'DRIVER_{x}_{y}',cq.Workplane('XY').circle(3).extrude(25).val().translate((x,y,3.8)))
# Body envelopes are over-approximations, not a rear-endcap drawing.
add('MOTOR_BODY_ENVELOPE',cq.Workplane('XY').box(35.2,35.2,28.2).val().translate((0,0,-20.9)))
pcb=cq.Workplane('XY').box(35,35,1.6).val()
for x,y in itertools.product([-13,13],repeat=2):pcb=pcb.cut(cq.Workplane('XY').circle(1.6).extrude(3,both=True).val().translate((x,y,0)))
add('PCB',pcb)
m=json.loads((root/'artifacts/mechanical/mount-usb-screen.json').read_text());assert m['board_sha256']==hashlib.sha256(native).hexdigest() and m['passed']
for u in m['usb']:
 x,y,z=u['mouth_xyz_mm'];add(u['reference']+'_PLUG_ENVELOPE',cq.Workplane('XY').box(10,7,30).val().translate((x,y,z+14.5)))
# The generated cable's native housing is 5 x 2.8 x 5 mm, top entry.
c=next(e for e in j if e['type']=='cad_cable');p=c['path'][-1]
add('JST_MATING_HOUSING',cq.Workplane('XY').box(2.8,5,5).val().translate((p['x'],p['y'],p['z']-2.5)))
checks=[];collisions=[]
for name in head_names+spacer_names+['JST_MATING_HOUSING']:
 for other in parts:
  if name==other or (name=='JST_MATING_HOUSING' and other=='J_MOTOR'):continue
  if name.startswith('PROPOSED_SPACER') and other=='MOTOR_BODY_ENVELOPE':continue # intended contact; retention explicitly unverified
  if name.startswith('PROPOSED_M3_SCREW') and other.startswith('DRIVER'):continue
  if broad(bounds[name],bounds[other]):
   v=max(0,parts[name].intersect(parts[other]).Volume())
   if v>1e-5:collisions.append({'part':name,'other':other,'intersection_mm3':v})
# Four parallel 0.6 mm wires at 1 mm pitch fit inside a radius 1.8 mm tube.
# Checking each segment edge against exact solids conservatively encloses all
# bundle orientations, including the renderer's polyline joints.
radius=1.8;minimum=math.inf
for index,(a,b) in enumerate(zip(c['path'],c['path'][1:])):
 aa=[a[k] for k in 'xyz'];ab=[b[k] for k in 'xyz'];edge=cq.Edge.makeLine(cq.Vector(*aa),cq.Vector(*ab));eb=bb(edge)
 for other,s in parts.items():
  if other=='JST_MATING_HOUSING':continue # wire and its own termination are one physical cable; intentional contact
  lo=lower(eb,bounds[other])
  if lo>radius+1:continue
  d=edge.distance(s)
  assert d+1e-5>=lo,'OCCT distance contradicts bounding-box lower bound'
  minimum=min(minimum,d-radius)
  if d<radius-1e-5:collisions.append({'wire_segment':index,'other':other,'centreline_distance_mm':d,'bundle_radius_mm':radius})
# The board-end wires approach their own housing from above. The 1.8 mm
# circumscribed tube intentionally overestimates the wire bundle's vertical
# thickness and is not a cable self-collision criterion.
assert all(q['z']>=p['z']-1e-5 for q in c['path'] if abs(q['x']-p['x'])<3.2 and abs(q['y']-p['y'])<4.3), 'Cable must enter its own top-entry housing from above'
report={'passed':not collisions,'board_sha256':hashlib.sha256(native).hexdigest(),'assembly_sha256':hashlib.sha256((root/'assembly.circuit.json').read_bytes()).hexdigest(),'fitted_supplier_STEP_parts':len([e for e in j if e['type']=='cad_component' and e.get('model_step_url') and e.get('source_component_id') not in dnp]),'conservative_USB_STEP_envelopes':conservative,'intentional_terminal_wire_entry_into_own_housing_excluded':True,'wire_bundle_radius_mm':radius,'wire_segments':len(c['path'])-1,'nearby_wire_envelope_min_clearance_mm':None if minimum==math.inf else minimum,'collisions':collisions,'PCB_records_preserved':j[:len(json.loads(native))]==json.loads(native),'actual_hardware_JSCAD_geometry_and_placements_checked':True,'screw_centres_mm':m['mounts'],'screw_shaft_to_spacer_bore_radial_clearance_mm':.1,'spacer_to_PCB_surface_gap_mm':0,'spacer_to_model_motor_surface_gap_mm':0,'motor_rear_attachment_verified':False,'physical_assembly_tested':False,'limitations':['Rear retention/thread engagement, rear shaft and encoder magnet/airgap remain unverified.','Motor-side JST termination is proposed; actual supplier motor has bare leads.','Native JST landing regions do not establish stock housing latch, crimp and tolerance fit.','Defined plug/tool/head dimensions are procurement bounds; real parts require qualification.','Bottom encoder and its capacitors are DNP and excluded from fitted-part collision checks.']}
(root/'artifacts/top-assembly/assembly-fit-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(collisions))
