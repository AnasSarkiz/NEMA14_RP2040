"""Check the actual assembly path and proposed hardware against supplier geometry.

This nominal CAD check does not qualify the motor rear attachment or hardware.
"""
import hashlib,itertools,json,math,pathlib
import cadquery as cq
root=pathlib.Path.cwd();j=json.loads((root/'assembly.circuit.json').read_text());native=(root/'artifacts/board.circuit.json').read_bytes();names={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'};dnp={e['source_component_id'] for e in j if e['type']=='pcb_component' and e.get('do_not_place')};parts={};cache={};bounds={};conservative=[]
assert native==(root/'index.circuit.json').read_bytes(), 'Saved routed board differs from the published baseline'
harness=json.loads((root/'artifacts/top-assembly/harness-definition.json').read_text())
assert harness['board_sha256']==hashlib.sha256(native).hexdigest()
catalog=json.loads((root/'src/jlcpcb-catalog.json').read_text())['parts']
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def broad(a,b):return all(a[i+3]>=b[i] and b[i+3]>=a[i] for i in range(3))
def lower(a,b):return math.sqrt(sum(max(a[i]-b[i+3],b[i]-a[i+3],0)**2 for i in range(3)))
def add(name,s):parts[name]=s;bounds[name]=bb(s)
for e in j:
 if e['type']!='cad_component' or not e.get('model_step_url') or e.get('source_component_id') in dnp:continue
 name=names[e['source_component_id']];url=e['model_step_url'];p=root/'imports/supplier'/url.split('/imports/supplier/')[-1]
 expected=next(q['sha256']['step'] for q in catalog.values() if str(p.relative_to(root)) in q['modelFiles'])
 assert hashlib.sha256(p.read_bytes()).hexdigest()==expected, 'Supplier model changed: '+name
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
 if t=='rotate':
  shape=from_plan(plan['shape'])
  for angle,axis in zip(plan['angles'],[(1,0,0),(0,1,0),(0,0,1)]):
   if angle:shape=shape.rotate((0,0,0),axis,math.degrees(angle))
  return shape
 if t=='sphere':return cq.Workplane('XY').sphere(plan['radius']).val()
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
m={'mounts':[[x,y] for x,y in itertools.product([-13,13],repeat=2)]}
for name in ['J_PD','J_DATA']:
 b=bounds[name];x,y,z=(b[0]+b[3])/2,(b[1]+b[4])/2,b[5]
 add(name+'_PLUG_ENVELOPE',cq.Workplane('XY').box(10,7,30).val().translate((x,y,z+14.5)))
plug=next(e for e in j if e['type']=='cad_component' and names.get(e.get('source_component_id'))=='JST_SHR_04V_S_PLUG')
shape=from_plan(plug['model_jscad'])
for angle,axis in zip([plug['rotation'][k] for k in 'xyz'],[(1,0,0),(0,1,0),(0,0,1)]):
 if angle:shape=shape.rotate((0,0,0),axis,angle)
shape=shape.translate(tuple(plug['position'][k] for k in 'xyz'))
add('JST_MATING_HOUSING',shape)
checks=[];collisions=[]
for name in head_names+spacer_names+['JST_MATING_HOUSING']:
 for other in parts:
  if name==other or (name=='JST_MATING_HOUSING' and other=='J_MOTOR'):continue
  if name.startswith('PROPOSED_SPACER') and other=='MOTOR_BODY_ENVELOPE':continue # intended contact; retention explicitly unverified
  if name.startswith('PROPOSED_M3_SCREW') and other.startswith('DRIVER'):continue
  if broad(bounds[name],bounds[other]):
   v=max(0,parts[name].intersect(parts[other]).Volume())
   if v>1e-5:collisions.append({'part':name,'other':other,'intersection_mm3':v})
minimum=math.inf;segments=[]
for wire in harness['wires']:
 for index,(a,b) in enumerate(zip(wire['path'],wire['path'][1:])):
  radius=wire['segment_radii_mm'][index]
  aa=[a[k] for k in 'xyz'];ab=[b[k] for k in 'xyz'];edge=cq.Edge.makeLine(cq.Vector(*aa),cq.Vector(*ab));eb=bb(edge)
  segments.append((wire['pin'],index,edge,eb,radius))
  for other,s in parts.items():
   # Only the short factory feedthrough enters the simplified case envelope.
   if other=='MOTOR_BODY_ENVELOPE' and index==0:
    assert abs(aa[0])<3 and 17<aa[1]<18 and ab[1]>18
    continue
   lo=lower(eb,bounds[other])
   if lo>radius+1:continue
   d=edge.distance(s);assert d+1e-5>=lo,'OCCT distance contradicts bounding-box lower bound'
   minimum=min(minimum,d-radius)
   if d<radius-1e-5:collisions.append({'pin':wire['pin'],'wire_segment':index,'other':other,'centreline_distance_mm':d,'wire_radius_mm':radius})
 splice=wire['splice'];a,b=splice['from'],splice['to'];edge=cq.Edge.makeLine(cq.Vector(*(a[k] for k in 'xyz')),cq.Vector(*(b[k] for k in 'xyz')))
 segments.append((wire['pin'],'splice',edge,bb(edge),splice['radius']))
 for other,s in parts.items():
  if lower(bb(edge),bounds[other])>splice['radius']+1:continue
  if edge.distance(s)<splice['radius']-1e-5:collisions.append({'splice_pin':wire['pin'],'other':other})
for (pin,i,a,ab,ar),(pin2,i2,b,bb2,br) in itertools.combinations(segments,2):
 if pin==pin2 or lower(ab,bb2)>=ar+br:continue
 if a.distance(b)<ar+br-1e-5:collisions.append({'wire_to_wire':[pin,i,pin2,i2]})
report={'passed':not collisions,'board_sha256':hashlib.sha256(native).hexdigest(),'assembly_sha256':hashlib.sha256((root/'assembly.circuit.json').read_bytes()).hexdigest(),'fitted_supplier_STEP_parts':len([e for e in j if e['type']=='cad_component' and e.get('model_step_url') and e.get('source_component_id') not in dnp]),'conservative_USB_STEP_envelopes':conservative,'wire_entry_holes_checked_against_actual_exposed_housing':True,'wire_segments':len(segments),'nearby_wire_envelope_min_clearance_mm':None if minimum==math.inf else minimum,'collisions':collisions,'PCB_records_preserved':j[:len(json.loads(native))]==json.loads(native),'actual_hardware_JSCAD_geometry_and_placements_checked':True,'screw_centres_mm':m['mounts'],'screw_shaft_to_spacer_bore_radial_clearance_mm':.1,'spacer_to_PCB_surface_gap_mm':0,'spacer_to_model_motor_surface_gap_mm':0,'motor_rear_attachment_verified':False,'physical_assembly_tested':False,'limitations':['Rear retention/thread engagement, rear shaft and encoder magnet/airgap remain unverified.','Factory wire diameter and actual splice procurement require a sample; the drawing specifies bare 300 +/-10 mm leads but no gauge.','Only the exposed stock housing outline is rendered; the concealed inserted stem and contact/latch tolerances are not modeled.','Defined plug/tool/head dimensions are procurement bounds; real parts require qualification.','Bottom encoder and its capacitors are DNP and excluded from fitted-part collision checks.']}
(root/'artifacts/top-assembly/assembly-fit-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(collisions))
