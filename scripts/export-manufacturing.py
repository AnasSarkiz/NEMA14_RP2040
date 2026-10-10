#!/usr/bin/env python3
"""Official CLI export followed by documented assembly/mask/silk CAM correction.
Cu, outline and drill bytes are preserved exactly.
"""
import argparse,csv,hashlib,importlib.util,json,os,pathlib,subprocess,zipfile,io,re,platform
ROOT=pathlib.Path(__file__).resolve().parents[1]
def record_versions(directory):
 packages={}
 for package in ['@tscircuit/cli','@tscircuit/core','@tscircuit/checks','circuit-json','circuit-json-to-gerber','typescript']:
  path=ROOT/'node_modules'/package/'package.json'
  packages[package]=json.loads(path.read_text())['version']
 generators={}
 for path in directory.glob('*_Cu.gbr'):
  match=re.search(r'%TF.GenerationSoftware,([^*]+)\*%',path.read_text())
  if not match:raise ValueError(f'Actual copper lacks generation-software metadata: {path.name}')
  generators[path.name]=match[1]
 versions={'python':platform.python_version(),'installed_packages':packages,'actual_copper_generation_software':generators,'note':'The CLI embeds its own Gerber converter; actual Gerber metadata is authoritative and can differ from the separately installed package version.'}
 (directory/'software-versions.json').write_text(json.dumps(versions,indent=2)+'\n')
 return versions

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--raw-only',action='store_true');ap.add_argument('--use-existing-raw',action='store_true',help='Process already saved official CLI raw ZIP; only when bound to the same source state');args=ap.parse_args();raw=ROOT/'artifacts/manufacturing-raw.zip';env=dict(os.environ,XDG_CONFIG_HOME='/workspace/.config')
 source_path=ROOT/'artifacts/board.circuit.json';source_bytes=source_path.read_bytes();source_sha=hashlib.sha256(source_bytes).hexdigest();binding_path=ROOT/'artifacts/raw-cli-export-binding.json'
 if args.use_existing_raw:
  if not binding_path.exists():raise ValueError('Existing raw ZIP has no recorded source/hash binding; regenerate official CLI export')
  binding=json.loads(binding_path.read_text())
  if binding['source_sha256']!=source_sha or binding['raw_archive_sha256']!=hashlib.sha256(raw.read_bytes()).hexdigest():raise ValueError('Existing raw ZIP binding does not match frozen source/archive')
 if not args.use_existing_raw:
  result=subprocess.run(['npx','--no-install','tsci','export','artifacts/board.circuit.json','-f','gerbers','-o',str(raw)],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (ROOT/'artifacts/export-output.txt').write_text(result.stdout)
  print(result.stdout,end='')
  result.check_returncode()
  if source_path.read_bytes()!=source_bytes:raise ValueError('Source changed during official CLI export; freeze and regenerate')
  binding_path.write_text(json.dumps({'source_sha256':source_sha,'raw_archive_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()},indent=2)+'\n')
 if args.raw_only:return
 spec=importlib.util.spec_from_file_location('audit',ROOT/'scripts/audit-manufacturing.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
 j=json.loads(source_bytes);out=ROOT/'artifacts/manufacturing';out.mkdir(exist_ok=True);bare={'J_DEBUG','J_BOOT'};catalog=json.loads((ROOT/'src/jlcpcb-catalog.json').read_text());src={e['source_component_id']:e for e in j if e['type']=='source_component'};pc={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};ref=lambda e:src[pc[e['pcb_component_id']]['source_component_id']]['name'];changed={};original={}
 for stale in out.iterdir():
  if stale.is_file() and stale.suffix in ['.gbr','.drl','.csv']:stale.unlink()
 with zipfile.ZipFile(raw) as z:
  for name in z.namelist():
   if name.endswith('/'):continue
   path=out/pathlib.Path(name).name;data=z.read(name);path.write_bytes(data);original[path.name]=hashlib.sha256(data).hexdigest()
 # Emit assembly apertures / mask / silk as standard polygon regions.
 # Copper, drilled land patterns and board outline remain byte-identical.
 def write_geometry(geometry,label):
  lines=[f'G04 {label} mm*','%FSLAX46Y46*%','%MOMM*%','%LPD*%','%ADD10C,0.001*%','D10*','G01*']
  polys=list(geometry.geoms) if hasattr(geometry,'geoms') else [geometry]
  for polygon in polys:
   if polygon.is_empty:continue
   if polygon.geom_type!='Polygon':raise ValueError('Nonpolygon aperture')
   for ring,dark in [(polygon.exterior,True)]+[(ring,False) for ring in polygon.interiors]:
    lines.extend(['%LPD*%' if dark else '%LPC*%','G36*'])
    for i,(x,y) in enumerate(ring.coords):lines.append(f'X{round(x*1e6)}Y{round(y*1e6)}D{2 if i==0 else 1:02}*')
    lines.append('G37*')
  lines.append('M02*');return ('\n'.join(lines)+'\n').encode()
 def change(name,data,reason):
  (out/name).write_bytes(data);changed[name]={'reason':reason,'before_sha256':original[name],'after_sha256':hashlib.sha256(data).hexdigest()}
 for name,layer in [('F_Paste.gbr','top'),('B_Paste.gbr','bottom')]:
  shapes=[a.shape(e) for e in j if e['type']=='pcb_solder_paste' and e['layer']==layer and ref(e) not in bare]
  change(name,write_geometry(a.unary_union(shapes),'Explicit reviewed solder-paste apertures'), 'Explicit top SMT stencil policy; manual plated joints and bare interfaces have no paste')
 mask_report={};masks={}
 for name in ['F_Mask.gbr','B_Mask.gbr']:
  native=a.gerber(out/name)[0]
  native_polys=list(native.geoms) if hasattr(native,'geoms') else [native];expanded=[p.buffer(.05,quad_segs=64) for p in native_polys]
  # Distinct opening pairs must keep at least 0.10 mm solder-mask web.
  # Touching native openings are already a single native mask polygon.
  tree=a.STRtree(expanded);bad=[];minimum=None
  for i,g in enumerate(expanded):
   for k in tree.query(g.buffer(.1003)):
    k=int(k)
    if k<=i:continue
    distance=g.distance(expanded[k]);minimum=distance if minimum is None else min(minimum,distance)
    if distance<.1002:bad.append({'opening_i':i,'opening_j':k,'expanded_web_mm':distance,'native_web_mm':native_polys[i].distance(native_polys[k])})
  # Do not silently merge openings or remove a web. Retain native geometry
  # at conflicting openings and record the exception for process review.
  expansion=[.05]*len(native_polys)
  for conflict in bad:
   safe=max(0,min(.05,(conflict['native_web_mm']-.1002)/2))
   for index in [conflict['opening_i'],conflict['opening_j']]:expansion[index]=min(expansion[index],safe)
  retained={i for i,radius in enumerate(expansion) if radius==0}
  final=[p.buffer(radius,quad_segs=64) if radius else p for p,radius in zip(native_polys,expansion)]
  finaltree=a.STRtree(final);webs=[]
  for i,g in enumerate(final):
   for k in finaltree.query(g.buffer(.101)):
    k=int(k)
    if k>i:webs.append(g.distance(final[k]))
  minimum_final=min(webs) if webs else None
  if minimum_final is not None and minimum_final<.1-1e-7:raise ValueError(f'{name}: native/expanded mask web {minimum_final} below 0.10 mm')
  masks[name]=a.unary_union(final)
  mask_report[name]={'nominal_expansion_mm':.05,'minimum_expanded_web_mm':minimum,'minimum_final_web_mm':minimum_final,'minimum_actual_expansion_mm':min(expansion) if expansion else None,'reduced_expansion_count':sum(radius<.05 for radius in expansion),'individual_expansions_mm':expansion,'retained_native_openings':sorted(retained),'conflicts':bad}
  change(name,write_geometry(masks[name],'Reviewed solder-mask openings +0.05 mm where >=0.10 mm web'),'0.05 mm nominal mask expansion reduced locally to guarantee 0.10 mm webs')
 for name,maskname in [('F_SilkScreen.gbr','F_Mask.gbr'),('B_SilkScreen.gbr','B_Mask.gbr')]:
  native=a.gerber(out/name)[0];final=native.difference(masks[maskname].buffer(.15)).intersection(a.box(-17.4,-17.4,17.4,17.4))
  change(name,write_geometry(final,'Reviewed silkscreen clear of solder openings and board edge'),'Clip native silk against mask openings +0.15 mm and 0.10 mm edge inset; full reference labels remain on assembly drawings')
 (out/'mask-web-policy.json').write_text(json.dumps(mask_report,indent=2)+'\n')
 for name in ['bom.csv','pick_and_place.csv']:
  path=out/name;reader=csv.DictReader(io.StringIO(path.read_text()));fields=list(reader.fieldnames);rows=[r for r in reader if r['Designator'] not in bare and (name!='pick_and_place.csv' or r['Designator']!='J_MOTOR')]
  if name=='bom.csv':
   for field in ['Manufacturer Part Number','Assembly Process']:
    if field not in fields:fields.append(field)
   for row in rows:
    cid=catalog['components'][row['Designator']];entry=catalog['parts'][cid];row['Manufacturer Part Number']=entry.get('manufacturerPartNumber',entry.get('mpn',''));source=next(e for e in src.values() if e['name']==row['Designator'])
    if cid not in source.get('supplier_part_numbers',{}).get('jlcpcb',[]):raise ValueError(f'Catalog/source supplier identity mismatch for {row["Designator"]}')
    if row['JLCPCB Part #']!=cid:raise ValueError(f'Raw export/catalog identity mismatch for {row["Designator"]}')
    if source.get('manufacturer_part_number')!=row['Manufacturer Part Number']:raise ValueError(f'MPN/source identity mismatch for {row["Designator"]}')
    row['Comment']=row['Manufacturer Part Number'];row['Value']=source.get('display_resistance',source.get('display_capacitance',row['Manufacturer Part Number']));row['Assembly Process']='Top-side through-hole; hand solder after reflow' if row['Designator']=='J_MOTOR' else ('Top SMT reflow; shield slots hand solder' if row['Designator'] in {'J_PD','J_DATA'} else 'Top SMT reflow')
    if not row['Manufacturer Part Number']:raise ValueError(f'Missing exact MPN for {row["Designator"]}')
  stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows);data=stream.getvalue().encode();path.write_bytes(data);(ROOT/'artifacts'/name).write_bytes(data);changed[name]={'reason':'Exclude bare debug/boot; motor header in BOM and manual manifest, excluded from automated CPL','before_sha256':original[name],'after_sha256':hashlib.sha256(data).hexdigest()}
 manual=out/'manual_assembly.csv'
 with manual.open('w',newline='') as stream:
  writer=csv.DictWriter(stream,fieldnames=['Designator','Manufacturer Part Number','JLCPCB Part #','Process','Pin 1','Inspection'],lineterminator='\n');writer.writeheader();writer.writerow({'Designator':'J_MOTOR','Manufacturer Part Number':'B4B-PH-K-S(LF)(SN)','JLCPCB Part #':'C131334','Process':'Top THT; hand solder after reflow; trim tails <=0.8 mm below PCB; insulate','Pin 1':'Leftmost pad viewed from component side; black A+','Inspection':'Header seated; polarity; wetting; tail length; plug retention; insulation'})
 (ROOT/'artifacts/manual_assembly.csv').write_bytes(manual.read_bytes())
 for name in ['fabrication-notes.md','via_process.csv','ordinary_via_process.csv']:
  (out/name).write_bytes((ROOT/'artifacts/assembly'/name).read_bytes())
 preserved={}
 for name,sha in original.items():
  if name not in changed:
   actual=hashlib.sha256((out/name).read_bytes()).hexdigest();assert actual==sha;preserved[name]=sha
 if source_path.read_bytes()!=source_bytes:raise ValueError('Source changed during CAM correction; freeze and regenerate')
 software=record_versions(out)
 manifest={'software_versions':software,'source_sha256':source_sha,'raw_cli_archive_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'intentional_CAM_changes':changed,'preserved_original_files':preserved,'policy':{'assembly':'top SMT reflow; USB shield slots and keyed JST motor header manually soldered afterward','DNP':sorted(bare),'exposed_pad_vias':'filled and capped (VIPPO) required; supplier capability/quote approval remains pending','solder_mask':'0.05 mm nominal opening expansion reduced locally to guarantee 0.10 mm webs; source native copper unchanged','silkscreen':'0.15 mm clearance from mask apertures; 0.10 mm edge inset; full untrimmed refs on assembly drawing','lead_stencil':'Fine-pitch MCU/driver rectangular leads 90% native dimensions; rounded driver leads use safe inscribed rectangles; candidate foil 0.10 mm; native copper unchanged','exposed_pad_stencil':'four panes, nominal 60% native copper-pad coverage, 0.20 mm cross-gap'},'status':'PROTOTYPE CANDIDATE; fabrication and assembly approvals pending'}
 (out/'export-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');zipout=ROOT/'artifacts/nema14-gerbers.zip'
 with zipfile.ZipFile(zipout,'w',zipfile.ZIP_DEFLATED) as z:
  for name in sorted(set(original)|{'manual_assembly.csv','fabrication-notes.md','via_process.csv','ordinary_via_process.csv'}):z.write(out/name,name)
 print(f'Reviewed archive: {zipout}; {len(preserved)} CAM files byte-identical to official CLI export; assembly tables, paste, mask and silk reviewed.')
if __name__=='__main__':main()
