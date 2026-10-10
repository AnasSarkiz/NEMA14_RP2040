"""Convert the exact reviewed mounted STEP into a portable tscircuit assembly scene.
Run with the repository CAD venv. Manufacturing files are read-only inputs.
"""
from pathlib import Path
import base64,datetime,hashlib,json,struct,tempfile,zipfile
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/assembly';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((ROOT/'artifacts/mechanical/mechanical-review.json').read_text())
board=ROOT/'artifacts/board.circuit.json';assert sha(board)==report['board_sha256']
archive=ROOT/'artifacts/mechanical/mounted-front-carrier.step.zip'
binding=next(x for x in report['step_assembly_archives']if x['archive']==archive.name)
assert sha(archive)==binding['archive_sha256']
with tempfile.TemporaryDirectory(prefix='nema14-assembly-')as td:
 step=Path(td)/binding['member']
 with zipfile.ZipFile(archive)as z:
  assert z.testzip()is None;step.write_bytes(z.read(binding['member']))
 assert sha(step)==binding['uncompressed_step_sha256']
 print('Importing reviewed STEP',flush=True)
 cache=Path(tempfile.gettempdir())/('nema14-'+binding['uncompressed_step_sha256']+'.xbf')
 if cache.exists():mounted=cq.Assembly.load(str(cache))
 else:
  mounted=cq.Assembly.importStep(str(step))
  mounted.export(str(cache),exportType='XBF')
 groups={n:cq.Assembly(name=n)for n in ['CONTROLLER','MOTOR','CARRIER','MOTOR_HARNESS','INSULATION_AND_RESTRAINT','FASTENERS','PD_CABLE','DATA_CABLE']}
 members={n:[]for n in groups}
 for child in mounted.children:
  name=child.name
  if name=='Board':group='CONTROLLER'
  elif name=='Official_motor':group='MOTOR'
  elif name=='Separate_front_carrier':group='CARRIER'
  elif name.startswith('J_PD_'):group='PD_CABLE'
  elif name.startswith('J_DATA_'):group='DATA_CABLE'
  elif name.startswith(('Front_M3_','PCB_M2p5','Clamp_M2p5')):group='FASTENERS'
  elif name.startswith(('PHR4_','SPH002_','Insulated_solder_tail_','Splice_insulation_','Wire_','FactoryLead_')):group='MOTOR_HARNESS'
  elif name.startswith(('PEEK_','Nomex','Clamp_silicone_')):group='INSULATION_AND_RESTRAINT'
  else:raise AssertionError('Unclassified mounted STEP part '+name)
  groups[group].add(child);members[group].append(name)
 assert sum(map(len,members.values()))==len(mounted.children)
 # toCompound carries native child locations; imported grouping preserves colors.
 bounds=lambda s:[getattr(s.BoundingBox(),a)for a in ['xmin','ymin','zmin','xmax','ymax','zmax']]
 expected=bounds(mounted.toCompound())
 # STEP round-trip B-spline bounding boxes can shift slightly; this is a visual 0.05 mm screen, not a physical-fit requalification.
 for a,b in zip(expected,report['mounted_assembly_bbox_mm']):assert abs(a-b)<.05,(a,b)
 models={};data={}
 for name,assy in groups.items():
  assert members[name]
  glb=OUT/(name.lower()+'.glb')
  assy.export(str(glb),tolerance=.05,angularTolerance=.15)
  raw=glb.read_bytes();magic,version,length=struct.unpack_from('<III',raw)
  assert magic==0x46546c67 and version==2 and length==len(raw)
  length,jtype=struct.unpack_from('<II',raw,12);assert jtype==0x4e4f534a
  g=json.loads(raw[20:20+length]);assert g['meshes']and not any(x.get('uri')for x in g.get('buffers',[]))
  models[name]={'path':str(glb.relative_to(ROOT)),'sha256':sha(glb),'bytes':len(raw),'native_world_bbox_mm':bounds(assy.toCompound()),'mounted_step_children':members[name],'meshes':len(g['meshes'])}
  data[name]='data:model/gltf-binary;base64,'+base64.b64encode(raw).decode()
  print('Exported',name,len(raw),'bytes',flush=True)
 (OUT/'models.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
 evidence={'schema':'nema14-tscircuit-assembly-assets-v1','source_board_sha256':sha(board),'mechanical_review_sha256':sha(ROOT/'artifacts/mechanical/mechanical-review.json'),'mounted_step_archive_sha256':sha(archive),'mounted_step_member_sha256':binding['uncompressed_step_sha256'],'export_script_sha256':sha(Path(__file__)),'cadquery_version':cq.__version__,'coordinates':'CAD in mm: PCB midplane Z0; GLB maps native Z-up to Y-up (x,z,-y); no unit scaling, world transforms baked from reviewed STEP.','tessellation_mm':.05,'angular_tolerance_radians':.15,'all_step_children_classified':True,'reviewed_native_bbox_mm':report['mounted_assembly_bbox_mm'],'STEP_roundtrip_bbox_delta_mm':[a-b for a,b in zip(expected,report['mounted_assembly_bbox_mm'])],'native_mounted_bbox_mm':expected,'models':models,'portable_models_json_sha256':sha(OUT/'models.json'),'hardware_fit_verified':False,'limitations':report['limitations']+report['service_harness']['limitations']}
 (OUT/'asset-manifest.json').write_text(json.dumps(evidence,indent=2)+'\n')
 assert sha(board)==report['board_sha256']
 print('Portable scene assets complete',flush=True)
