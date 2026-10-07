"""Verify exact supplier CAD assets, A4 pin/net coverage, and write assembly sourcing BOM."""
import base64,csv,hashlib,json,pathlib,math
root=pathlib.Path(__file__).resolve().parents[1]
j=json.loads((root/'artifacts/board.circuit.json').read_text());cat=json.loads((root/'src/jlcpcb-catalog.json').read_text())
source={e['source_component_id']:e for e in j if e['type']=='source_component'}
pcb={e['source_component_id']:e for e in j if e['type']=='pcb_component'}
models={e['source_component_id']:e for e in j if e['type']=='cad_component' and e.get('model_obj_url')}
rows=[];bare=[];pending=[];mapped={};checked=[]
for s in source.values():
 name=s['name'];p=pcb[s['source_component_id']];id=cat['components'].get(name)
 isbare=name in ['J_MOTOR','J_DEBUG','J_BOOT']
 if isbare:bare.append(name)
 elif not id:pending.append(name)
 else:
  part=cat['parts'][id];model=models.get(s['source_component_id']);assert model,name+' missing model'
  assert s['supplier_part_numbers']['jlcpcb']==[id],name+' supplier mismatch'
  assert model['model_obj_url']==part['cadModel']['objUrl'],name+' model mismatch'
  if 'supplierPackage' in part:
   span=max(p['width'],p['height'])
   package=min({'0402':1.56,'0603':2.45,'0805':2.85},key=lambda k:abs({'0402':1.56,'0603':2.45,'0805':2.85}[k]-span))
   assert abs(span-{'0402':1.56,'0603':2.45,'0805':2.85}[package])<.01,(name,span)
   assert package==part['supplierPackage'],name+' supplier package does not match PCB footprint'
  mapped[name]=id
 rows.append([name,s.get('manufacturer_part_number',''),id or '',s.get('display_resistance',s.get('display_capacitance',s.get('display_inductance',''))),s.get('max_voltage_rating',''),s.get('tolerance',''),p['center']['x'],p['center']['y'],p.get('rotation',0),p.get('layer','top'),'bare PCB interface' if isbare else ('exact supplier CAD attached; assembly review required' if id else 'supplier import and CAD pending')])
for id,part in cat['parts'].items():
 for path in part['modelFiles']:
  p=root/path;ext=p.suffix[1:];actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==part['sha256'][ext],path+' hash mismatch'
  if ext=='obj':assert part['cadModel']['objUrl'].endswith('/'+path)
 checked.append(id)
# Exact C165948 opening plane in the saved board coordinate frame.
usb=[]
for s in source.values():
 if s['name'] not in ['J_PD','J_DATA']:continue
 m=models[s['source_component_id']];part=cat['parts'][mapped[s['name']]]
 vertices=[list(map(float,line.split()[1:4])) for line in (root/next(f for f in part['modelFiles'] if f.endswith('.obj'))).read_text().splitlines() if line.startswith('v ')]
 angle=math.radians(m['rotation']['z']);mouth_y=min(v[1] for v in vertices)
 # Rotation is about Z; supplied local Y minimum is the mating opening plane.
 x=m['position']['x']-math.sin(angle)*mouth_y;expected=-17.5 if s['name']=='J_PD' else 17.5
 assert abs(x-expected)<.001,(s['name'],x)
 usb.append({'reference':s['name'],'supplierPart':mapped[s['name']],'mouthXmm':round(x,5),'expectedEdgeXmm':expected})
ports=[e for e in j if e['type']=='source_port' and 'pin_number' in e]
schports={e['source_port_id']:e for e in j if e['type']=='schematic_port'}
assert all(p['source_port_id'] in schports for p in ports),'Missing schematic pin'
sheets=[e for e in j if e['type']=='schematic_sheet'];assert all(e['sheet_size']=='a4' and e['sheet_width']==297 and e['sheet_height']==210 for e in sheets)
netmap={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}
labelcounts={}
for e in j:
 if e['type']=='schematic_net_label':labelcounts[e['source_net_id']]=labelcounts.get(e['source_net_id'],0)+1
for net in netmap.values():
 expected=sum(p.get('subcircuit_connectivity_map_key')==net['subcircuit_connectivity_map_key'] for p in ports)
 assert labelcounts.get(net['source_net_id'],0)==expected,(net['name'],expected,labelcounts.get(net['source_net_id'],0))
report={'mappedComponents':len(mapped),'distinctParts':len(checked),'references':mapped,'pending':pending,'barePcbPads':bare,'complete':not pending,'blocker':'Fresh JLCPCB/EasyEDA search and asset downloads are blocked by the active network allowlist. Required hosts are saved in the cloud draft.' if pending else None,'supplierAssetsHashVerified':True,'mappedPassivePackagesMatchSavedFootprints':True,'usbSupplierModelOpenings':usb,'schematicA4PageCount':len(sheets),'allNumberedPhysicalPinsOnSchematic':True,'numberedPinCount':len(ports),'schematicNamedNetStubCoverageVerified':True}
(root/'artifacts/jlcpcb-import-report.json').write_text(json.dumps(report,indent=2)+'\n')
with (root/'artifacts/bom.csv').open('w') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['Reference','MPN','JLCPCB part','Value','Voltage rating (V)','Tolerance','PCB X mm','PCB Y mm','Rotation deg','Assembly side','Review note']);w.writerows(rows)
p=root/'artifacts/verification.json';v=json.loads(p.read_text());v.update({'supplierCadModels':len(mapped),'supplierImportsComplete':not pending,'schematicA4PageCount':len(sheets),'allNumberedPhysicalPinsOnSchematic':True})
v['sha256'].update({f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in v['sha256'] if (root/f).exists()})
v['sha256'].update({str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [root/'artifacts/board.circuit.json',root/'artifacts/final-source.circuit.json',root/'artifacts/schematic-a4.pdf',root/'artifacts/jlcpcb-import-report.json',root/'artifacts/bom.csv',root/'artifacts/nema14-gerbers.zip']})
p.write_text(json.dumps(v,indent=2)+'\n')
print(len(mapped),'supplier CAD placements verified;',len(pending),'supplier imports pending;',len(sheets),'A4 pages;',len(ports),'physical pins represented')
