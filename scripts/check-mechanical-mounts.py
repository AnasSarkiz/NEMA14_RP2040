import pathlib,json,hashlib,itertools,math,sys
import cadquery as cq
from shapely.geometry import Point,LineString,Polygon,box
from shapely import affinity
from shapely.ops import unary_union
root=pathlib.Path(__file__).resolve().parents[1];source=root/(sys.argv[1] if len(sys.argv)>1 else 'artifacts/board.circuit.json');board_bytes=source.read_bytes();j=json.loads(board_bytes);cat=json.loads((root/'src/jlcpcb-catalog.json').read_text());src={e['source_component_id']:e for e in j if e['type']=='source_component'};parts={};cache={};meta={}
bound_cache={}
def bounds(s):
 if id(s) in bound_cache:return bound_cache[id(s)]
 b=s.BoundingBox();bound_cache[id(s)]= [getattr(b,k) for k in ['xmin','ymin','zmin','xmax','ymax','zmax']]
 return bound_cache[id(s)]
def broad(a,b):
 x,y=bounds(a),bounds(b);return all(x[i+3]>=y[i] and y[i+3]>=x[i] for i in range(3))
def bbox_distance(a,b):
 x,y=bounds(a),bounds(b)
 return math.sqrt(sum(max(x[i]-y[i+3],y[i]-x[i+3],0)**2 for i in range(3)))
def nearest_distance(a,others):
 # A far compound-distance query can return an invalid zero in this OCCT
 # build. Bounding-box lower bounds safely exclude distant candidates.
 best=float('inf')
 for b in sorted(others,key=lambda q:bbox_distance(a,q)):
  lower=bbox_distance(a,b)
  if lower>=best:continue
  d=a.distance(b)
  assert d+1e-5>=lower, 'Native STEP distance contradicts its geometric lower bound'
  best=min(best,d)
 return best
def volume(a,b):return max(0,a.copy().intersect(b.copy()).Volume()) if broad(a,b) else 0

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
heads={str((x,y)):cq.Workplane('XY').circle(2.2).extrude(3).val().translate((x,y,.8)) for x,y in itertools.product([-13,13],repeat=2)}
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
  if d<1:clearances.append({'reference':a,'mount':b,'distance_to_radius2p2_fastener_mm':d,'intersection_mm3':volume(s,t)})
plugs={};usb=[]
for name in ['J_PD','J_DATA']:
 m=meta[name];a=math.radians(m['rotation']['z']);mouth=[m['position']['x']-math.sin(a)*(2.6-m['model_origin_position']['y']),m['position']['y']+math.cos(a)*(2.6-m['model_origin_position']['y'])];direction=[-math.sin(a),math.cos(a)]
 # 10 mm wide, 7 mm tall, 30 mm long plug envelope, centred at mating plane +15 mm.
 plug=cq.Workplane('XY').box(10,30,7).val().rotate((0,0,0),(0,0,1),m['rotation']['z']).translate((mouth[0]+direction[0]*15,mouth[1]+direction[1]*15,2.45));plugs[name]=plug
 collisions=[]
 for n,s in list(parts.items())+list(heads.items()):
  if n!=name and broad(plug,s):
   v=volume(plug,s)
   if v>1e-5:collisions.append({'other':n,'volume_mm3':v})
 usb.append({'native_body_to_mount_envelope_mm':nearest_distance(parts[name],heads.values()),'reference':name,'mouth_xy_mm':mouth,'outward_unit_vector':direction,'plug_10x30x7mm_intersections':collisions,'bbox_mm':bounds(parts[name])})
plug_intersections=[]
for (a,s),(b,t) in itertools.combinations(plugs.items(),2):
 v=volume(s,t)
 if v>1e-5:plug_intersections.append({'a':a,'b':b,'volume_mm3':v})
plug_gap=plugs['J_PD'].distance(plugs['J_DATA'])
assert plug_gap >= 2.39999, 'Two simultaneous 10 mm housings need the reviewed 2.4 mm nominal gap'
# PH is a top-entry connector. Verify actual STEP leads, PCB envelope, and an unobstructed vertical insertion region.
motor=parts['J_MOTOR'];motor_meta=meta['J_MOTOR'];motor_pcb=next(e for e in j if e['type']=='pcb_component' and e['source_component_id']==motor_meta['source_component_id'])
motor_pads=[e for e in j if e['type']=='pcb_smtpad' and e['pcb_component_id']==motor_pcb['pcb_component_id']]
assert len(motor_pads)==6 and not any(e['type']=='pcb_plated_hole' and e['pcb_component_id']==motor_pcb['pcb_component_id'] for e in j)
# The supplier STEP fuses contacts/plastic into one solid; it cannot prove
# separate metal-terminal centers. Verify occupied STEP landing regions for
# all six native pads, the absence of underside tails, and body/access clearance.
lead_alignment=[]
for pad in motor_pads:
 region=cq.Workplane('XY').box(pad['width'],pad['height'],.1).val().translate((pad['x'],pad['y'],.85))
 overlap=volume(motor,region)
 assert overlap>1e-5, 'Native JST STEP has no landing geometry over a copper pad'
 lead_alignment.append({'native_pad_xy_mm':[pad['x'],pad['y']],'STEP_landing_region_volume_mm3':overlap,'individual_metal_terminal_center_verified':False})
assert bounds(motor)[2]>=.79999, 'SMT JST must not project below the top PCB surface'
mb=bounds(motor);assert all(-17.5<=mb[i]<=17.5 for i in [0,1,3,4]), 'JST body exceeds the fixed PCB outline'
# This screen adds 0.3 mm around the actual header's XY bounds. It proves free space above the header, not a qualified cable or finger/grip envelope.
mx=(mb[0]+mb[3])/2;my=(mb[1]+mb[4])/2
access=cq.Workplane('XY').box(mb[3]-mb[0]+.6,mb[4]-mb[1]+.6,20).val().translate((mx,my,mb[5]+10))
access_collisions=[]
for name,other in list(parts.items())+list(heads.items())+list(plugs.items()):
 if name=='J_MOTOR':continue
 v=volume(access,other)
 if v>1e-5:access_collisions.append({'other':name,'volume_mm3':v})
motor_report={'reference':'J_MOTOR','manufacturer_part_number':'BM04B-SRSS-TB(LF)(SN)','supplier_id':'C160390','mating_housing':'SHR-04V-S','insertion_direction':'+Z (from above)','body_and_lead_bbox_mm':mb,'body_within_35mm_outline':True,'native_SMT_pad_centres_mm':[[p['x'],p['y']] for p in motor_pads],'native_JST_drills':0,'STEP_landing_regions':lead_alignment,'individual_STEP_metal_terminal_centers_verified':False,'vertical_access_envelope_bbox_mm':bounds(access),'vertical_access_intersections':access_collisions,'tail_projection_below_PCB_mm':max(0,-.8-mb[2]),'cable_and_finger_clearance_hardware_tested':False}
report={'source_path':str(source),'fastener_requirement':{'standard':'DIN 920','thread':'M3','maximum_head_diameter_mm':4,'model_envelope_diameter_mm':4.4,'conservative_model_height_mm':3,'radial_screen_allowance_mm':.2},'plug_pair_intersections':plug_intersections,'minimum_simultaneous_plug_gap_mm':plug_gap,'board_sha256':hashlib.sha256(board_bytes).hexdigest(),'native_STEP_models':len(parts),'component_intersections':intersections,'fastener_clearances':clearances,'usb':usb,'mounts':[[x,y] for x,y in itertools.product([-13,13],repeat=2)],'motor_connector':motor_report,'rear_motor_compatibility_verified':False,'limitations':['Supplier JST STEP fuses plastic and contacts; six landing-region overlaps are checked, individual metal-terminal centers require datasheet/assembler confirmation.','Nominal PCB/model screen only; no verified mounting to rear motor endcap.','Cable envelope is a defined 10x30x7 mm procurement bound, not tested cable hardware.','Ø4.4 mm fastener envelope is a defined screen budget around Ø4 mm DIN 920 heads; complete assembly tolerance, torque, thread engagement and any washer/spacer are unqualified.']}
out=root/'artifacts/mechanical';out.mkdir(exist_ok=True);assert source.read_bytes()==board_bytes, 'Board changed during mechanical audit'
report['passed']=not access_collisions and not intersections and not plug_intersections and all(e['intersection_mm3']<1e-5 for e in clearances) and all(not e['plug_10x30x7mm_intersections'] for e in usb)
(out/('source-mount-usb-screen.json' if len(sys.argv)>1 else 'mount-usb-screen.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

raise SystemExit(0 if report['passed'] else 1)
