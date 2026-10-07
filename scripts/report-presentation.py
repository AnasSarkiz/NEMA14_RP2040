"""Verify genuine JLCPCB imports, native footprints, CAD assets and A4 coverage."""
import csv,hashlib,json,pathlib,math,re
import numpy as np
from shapely.geometry import Polygon,box
root=pathlib.Path(__file__).resolve().parents[1]
j=json.loads((root/'artifacts/board.circuit.json').read_text());cat=json.loads((root/'src/jlcpcb-catalog.json').read_text())
source={e['source_component_id']:e for e in j if e['type']=='source_component'}
pcb={e['source_component_id']:e for e in j if e['type']=='pcb_component'}
models={e['source_component_id']:e for e in j if e['type']=='cad_component' and e.get('model_obj_url')}
courts={e['pcb_component_id']:Polygon([(p['x'],p['y']) for p in e['outline']]) for e in j if e['type']=='pcb_courtyard_outline'}
rows=[];bare=[];mapped={};usb=[];alignment=[];cache={}
for id,part in cat['parts'].items():
 p=root/part['importPath'];original=pathlib.Path(str(p)+'.original')
 assert hashlib.sha256(original.read_bytes()).hexdigest()==part['originalImportSha256']
 footprint=lambda t:re.search(r'<footprint>.*?</footprint>',t,re.S).group(0)
 assert footprint(p.read_text())==footprint(original.read_text()),id+' native footprint changed'
 for f in part['modelFiles']:
  p=root/f;assert hashlib.sha256(p.read_bytes()).hexdigest()==part['sha256'][p.suffix[1:]],f
 cache[id]=np.array([list(map(float,l.split()[1:4])) for l in (root/next(f for f in part['modelFiles'] if f.endswith('.obj'))).read_text().splitlines() if l.startswith('v ')])
 assert len(cache[id]) and np.isfinite(cache[id]).all()
for sid,s in source.items():
 name=s['name'];p=pcb[sid];id=cat['components'].get(name);isbare=name in ['J_MOTOR','J_DEBUG','J_BOOT']
 if isbare:bare.append(name)
 else:
  assert id,name+' missing exact supplier import';part=cat['parts'][id];m=models[sid]
  assert s['supplier_part_numbers']['jlcpcb']==[id]
  assert s['manufacturer_part_number']==part['manufacturerPartNumber'],name
  for ext,field in [('obj','model_obj_url'),('step','model_step_url')]:assert m[field].endswith('/'+next(f for f in part['modelFiles'] if f.endswith('.'+ext)))
  origin=np.array([m['model_origin_position'][a] for a in ['x','y','z']]);v=cache[id]-origin;a=math.radians(m['rotation']['z']);r=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
  v=v@r.T+np.array([m['position'][a] for a in ['x','y','z']]);lo=v.min(axis=0);hi=v.max(axis=0);outside=box(*lo[:2],*hi[:2]).difference(courts[p['pcb_component_id']].buffer(.15)).area
  assert outside<.01,(name,'CAD outside native courtyard',outside)
  alignment.append({'reference':name,'part':id,'min':lo.tolist(),'max':hi.tolist(),'bboxAreaOutsideCourtyard':outside});mapped[name]=id
  if name in ['J_PD','J_DATA']:
   opening=m['position']['x']-math.sin(a)*(cache[id][:,1].max()-origin[1]);expected=-17.5 if name=='J_PD' else 17.5
   assert abs(opening-expected)<.001,(name,opening);usb.append({'reference':name,'supplierPart':id,'mouthXmm':opening,'expectedEdgeXmm':expected})
 rows.append([name,s.get('manufacturer_part_number',''),id or '',s.get('display_resistance',s.get('display_capacitance',s.get('display_inductance',''))),s.get('max_voltage_rating',''),s.get('tolerance',''),p['center']['x'],p['center']['y'],p.get('rotation',0),p.get('layer','top'),'bare PCB interface' if isbare else 'native supplier import with OBJ and STEP'])
fresh=json.loads((root/'artifacts/final-source.circuit.json').read_text())
for typ in ['pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_hole','pcb_courtyard_outline']:
 key=typ+'_id';actual={e[key]:e for e in j if e['type']==typ};expected={e[key]:e for e in fresh if e['type']==typ}
 def same(a,b):
  if isinstance(a,(int,float)) and isinstance(b,(int,float)):return abs(a-b)<1e-6
  if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
  if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
  return a==b
 assert same(actual,expected),typ+' saved supplier geometry differs from source'
ports=[e for e in j if e['type']=='source_port' and 'pin_number' in e];schports={e['source_port_id'] for e in j if e['type']=='schematic_port'}
assert all(p['source_port_id'] in schports for p in ports)
sheets=[e for e in j if e['type']=='schematic_sheet'];assert sheets and all(e['sheet_size']=='a4' and e['sheet_width']==297 and e['sheet_height']==210 for e in sheets)
labels={}
for e in j:
 if e['type']=='schematic_net_label' and 'source_net_id' in e:labels[e['source_net_id']]=labels.get(e['source_net_id'],0)+1
for net in [e for e in j if e['type']=='source_net']:
 expected=sum(p.get('subcircuit_connectivity_map_key')==net['subcircuit_connectivity_map_key'] for p in ports)
 assert labels.get(net['source_net_id'],0)==expected,(net.get('name'),expected,labels.get(net['source_net_id'],0))
report={'mappedComponents':len(mapped),'distinctParts':len(cat['parts']),'references':mapped,'pending':[],'barePcbPads':bare,'complete':True,'supplierAssetsHashVerified':True,'nativeImportedFootprintsUnchanged':True,'allFittedPartsHaveObjAndStep':True,'cadBoundsWithinSupplierCourtyards':True,'usbSupplierModelOpenings':usb,'schematicA4PageCount':len(sheets),'allNumberedPhysicalPinsOnSchematic':True,'numberedPinCount':len(ports),'schematicNamedNetStubCoverageVerified':True}
(root/'artifacts/jlcpcb-import-report.json').write_text(json.dumps(report,indent=2)+'\n');(root/'artifacts/supplier-cad-alignment.json').write_text(json.dumps(alignment,indent=2)+'\n')
with (root/'artifacts/bom.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','MPN','JLCPCB part','Value','Voltage rating (V)','Tolerance','PCB X mm','PCB Y mm','Rotation deg','Assembly side','Review note']);w.writerows(rows)
p=root/'artifacts/verification.json';v=json.loads(p.read_text());v.update({'supplierCadModels':len(mapped),'supplierImportsComplete':True,'schematicA4PageCount':len(sheets),'allNumberedPhysicalPinsOnSchematic':True})
v['sha256']={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (root/'artifacts').iterdir() if f.is_file() and f.suffix in ['.json','.dsn','.ses','.zip','.pdf'] and f!=p};p.write_text(json.dumps(v,indent=2)+'\n')
print(len(mapped),'fitted supplier imports with OBJ+STEP;',len(sheets),'A4 pages;',len(ports),'numbered pins')
