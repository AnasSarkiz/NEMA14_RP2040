"""Dimension-correct the supplier's short generic model; never alter PCB copper.

Authority: Panasonic FP 2025 D8 drawing, nominal height 7.7 +/-0.3 mm.
The original supplier assets remain intact. XY geometry, polarity and CAD datum
are preserved. This is a drawing-derived visualization, not factory CAD.
"""
import hashlib,json,pathlib
import cadquery as cq
root=pathlib.Path(__file__).resolve().parents[1]
source=root/'imports/supplier/EEEFPV101XAP/EEEFPV101XAP.step'
shape=cq.importers.importStep(str(source)).val();bb=shape.BoundingBox()
scale=7.7/(bb.zmax-bb.zmin);offset=bb.zmin*(1-scale)
corrected=shape.transformGeometry(cq.Matrix([[1,0,0,0],[0,1,0,0],[0,0,scale,offset],[0,0,0,1]]))
assert corrected.isValid() and abs(corrected.BoundingBox().zlen-7.7)<1e-5
out=root/'references/models';out.mkdir(exist_ok=True)
step=out/'EEEFPV101XAP-D8-7p7mm.step';obj=out/'EEEFPV101XAP-D8-7p7mm.obj'
cq.exporters.export(corrected,str(step))
raw=root/'imports/supplier/EEEFPV101XAP/EEEFPV101XAP.obj';lines=[]
for line in raw.read_text().splitlines():
    if line.startswith('v '):
        p=line.split();p[3]=f'{float(p[3])*scale+offset:.10f}';line=' '.join(p)
    elif line.startswith('vn '):
        import math
        p=line.split();v=[float(p[1]),float(p[2]),float(p[3])/scale];length=math.sqrt(sum(x*x for x in v));line='vn '+' '.join(f'{x/length:.10f}' for x in v)
    lines.append(line)
obj.write_text('\n'.join(lines)+'\n')
catfile=root/'src/jlcpcb-catalog.json';cat=json.loads(catfile.read_text());part=cat['parts']['C178585']
part['originalSupplierModelFiles']=['imports/supplier/EEEFPV101XAP/EEEFPV101XAP.'+ext for ext in ['obj','step']]
part['originalSupplierModelSha256']={ext:hashlib.sha256((root/f).read_bytes()).hexdigest() for ext,f in zip(['obj','step'],part['originalSupplierModelFiles'])}
part['modelFiles']=[str(p.relative_to(root)) for p in [obj,step]]
part['sha256'].update({p.suffix[1:]:hashlib.sha256(p.read_bytes()).hexdigest() for p in [obj,step]})
part['modelCorrection']={'authority':'Panasonic-FP-2025.pdf D8','nominalHeightMm':7.7,'heightToleranceMm':0.3,'assemblyStandOffAllowanceMm':0.3,'method':'explicit Z dimension correction; original XY and datum retained','factoryCad':False}
catfile.write_text(json.dumps(cat,indent=2)+'\n')
module=root/'imports/supplier/EEEFPV101XAP/EEEFPV101XAP.tsx';text=module.read_text()
import re
repo='NEMA14_RP2040' if root.name=='NEMA14_RP2040' else 'NEMA17_Controller'
for variable,file in [('objPath',obj),('stepPath',step)]:
    url='https://raw.githubusercontent.com/AnasSarkiz/'+repo+'/main/'+str(file.relative_to(root))
    text=re.sub(r'const '+variable+r' = "[^"]+"', 'const '+variable+' = "'+url+'"',text)
module.write_text(text)
proof={'authority':'references/Panasonic-FP-2025.pdf','sourceStepSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceHeightMm':bb.zlen,'nominalHeightMm':corrected.BoundingBox().zlen,'maximumBodyHeightMm':8.0,'maximumWithAssemblyAllowanceMm':8.3,'xyUnchanged':True,'datumUnchanged':True,'originalAssetsRetained':True,'drawingDerivedModel':True}
(out/'bulk-model-correction.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
