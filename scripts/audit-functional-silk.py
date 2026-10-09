"""Check finished CAM preserves full functional text strokes from raw CLI ink."""
import importlib.util,pathlib,json,zipfile,tempfile,hashlib
from shapely.geometry import box
root=pathlib.Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('cam',root/'scripts/audit-manufacturing.py');cam=importlib.util.module_from_spec(spec);spec.loader.exec_module(cam);j=json.loads((root/'artifacts/board.circuit.json').read_text());rows=[]
with tempfile.TemporaryDirectory()as tmp:
 with zipfile.ZipFile(root/'artifacts/manufacturing-raw.zip')as z:
  for layer,name in [('top','F_SilkScreen.gbr'),('bottom','B_SilkScreen.gbr')]:
   entry=next(e for e in z.namelist()if e.endswith('/'+name)or e==name);p=pathlib.Path(tmp)/name;p.write_bytes(z.read(entry));raw=cam.gerber(p)[0];final=cam.gerber(root/'artifacts/manufacturing'/name)[0]
   for e in j:
    if e['type']!='pcb_silkscreen_text'or e['layer']!=layer:continue
    c=e['anchor_position'];font=e['font_size'];w=len(e['text'])*font*.7+.2;region=box(c['x']-w/2,c['y']-font*.6,c['x']+w/2,c['y']+font*.6);ink=raw.intersection(region);lost=ink.difference(final.buffer(.000002)).area;rows.append({'text':e['text'],'layer':layer,'center_mm':c,'font_mm':font,'raw_ink_mm2_in_label_region':ink.area,'clipped_ink_mm2':lost})
errors=[e for e in rows if e['clipped_ink_mm2']>1e-5 or e['raw_ink_mm2_in_label_region']<.01];r={'source_sha256':hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest(),'functional_texts':rows,'errors':errors,'scope':'Raw CLI versus finished Gerber stroke conservation within generous isolated functional-label regions; does not prove physical legibility or manufacturer body marking.'};(root/'artifacts/validation/service-silkscreen.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'labels':len(rows),'errors':errors},indent=2));raise SystemExit(bool(errors))
