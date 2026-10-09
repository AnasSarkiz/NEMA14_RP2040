"""Extract exact manufacturer USB-C termination from illustrative cable STEP.
Full native assemblies are retained; factory CAD cable length is illustrative.
The manufacturer PDF governs ordered cable lengths and envelope tolerances.
"""
import cadquery as cq,json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1];out=root/'references/models';proof=[]
for name,origin in [('USB-PD-Tensility-10-06137',(-120.80696362211745,-1.500756340721473,19.85747612343181)),('USB-data-Tensility-10-06139',(-184.62621196549375,62.83296096322162,19.80846235225407))]:
 path=out/(name+'.step');native=cq.importers.importStep(str(path)).val();x,y,z=origin
 clip=cq.Workplane('XY').box(42,50,50).val().translate((x+14,y,z));pieces=[]
 for solid in native.Solids():
  b=solid.BoundingBox()
  if b.xmin>x+35 or b.xmax<x-7:continue
  cut=solid.intersect(clip)
  if cut.Volume()>1e-7:pieces.extend(cut.Solids())
 end=cq.Compound.makeCompound(pieces).translate((-x,-y,-z)).rotate((0,0,0),(1,1,1),120);assert end.isValid()
 target=out/(name+'-C-end.step');cq.exporters.export(end,str(target));b=end.BoundingBox()
 proof.append({'MPN':name,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'native_shoulder_datum_xyz_mm':origin,'transform':'subtract shoulder datum; rotate120deg about(1,1,1): nativeX->worldY, nativeY->worldZ, nativeZ->worldX','termination_bbox_mm':[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax],'unchangedFullManufacturerStepRetained':True,'orderedCableLengthMustUsePDF':True})
(out/'USB-cable-model-provenance.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
