"""Verify the fitted reference JST, native model identity, coil order, and actual CAM drills."""
import csv,decimal,hashlib,json,pathlib,re,zipfile
root=pathlib.Path(__file__).resolve().parents[1];D=decimal.Decimal
records=[];expected=None
for name in ['artifacts/final-source.circuit.json','artifacts/board.circuit.json','index.circuit.json']:
 raw=(root/name).read_bytes();j=json.loads(raw);part=next(e for e in j if e['type']=='source_component' and e['name']=='J_MOTOR');assert part['manufacturer_part_number']=='B4B-PH-K-S(LF)(SN)' and part['supplier_part_numbers']=={'jlcpcb':['C131334']}
 cad=next(e for e in j if e['type']=='cad_component' and e['source_component_id']==part['source_component_id']);assert cad['model_step_url'] and cad['model_obj_url']
 pc=next(e for e in j if e['type']=='pcb_component' and e['source_component_id']==part['source_component_id']);assert pc['layer']=='top' and not pc['do_not_place']
 ports={e['source_port_id']:e for e in j if e['type']=='source_port' and e['source_component_id']==part['source_component_id']};pp={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};nets={e['subcircuit_connectivity_map_key']:e['name'] for e in j if e['type']=='source_net'}
 holes=[e for e in j if e['type']=='pcb_plated_hole' and e['pcb_component_id']==pc['pcb_component_id']];assert len(holes)==4
 rows=[]
 for h in holes:
  port=ports[pp[h['pcb_port_id']]['source_port_id']];pin=port['pin_number'];assert nets[port['subcircuit_connectivity_map_key']]==['A_PLUS','A_MINUS','B_PLUS','B_MINUS'][pin-1];assert h['shape']=='circle' and abs(h['outer_diameter']-1.5999968)<1e-8 and abs(h['hole_diameter']-.999998)<1e-8
  rows.append({'pin':pin,'net':nets[port['subcircuit_connectivity_map_key']],'x':h['x'],'y':h['y'],'drill_diameter_mm':h['hole_diameter']})
 rows.sort(key=lambda h:h['pin'])
 if expected is None:expected=rows
 assert rows==expected, 'Motor native drill coordinates differ between source and delivered files'
 records.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'pins_and_native_drills':rows})
archive=root/'artifacts/nema14-gerbers.zip';matches=[]
with zipfile.ZipFile(archive) as z:
 files=[n for n in z.namelist() if n.endswith('.drl') and 'npth' not in n.lower()];assert len(files)==1
 raw=z.read(files[0]);s=raw.decode();assert 'METRIC' in s and 'G90' in s;tools={};tool=None;hits=[]
 for line in s.splitlines():
  m=re.fullmatch(r'T(\d+)C([\d.]+)',line)
  if m:tools[m[1]]=D(m[2]);continue
  m=re.fullmatch(r'T(\d+)',line)
  if m:tool=m[1];continue
  m=re.fullmatch(r'X([+-]?[\d.]+)Y([+-]?[\d.]+)',line)
  if m:hits.append((D(m[1]),D(m[2]),tools[tool]))
 for h in expected:
  want=[D(str(h[k])) for k in ['x','y','drill_diameter_mm']];near=[hit for hit in hits if all(abs(a-b)<D('.0001') for a,b in zip(hit,want))];assert len(near)==1, 'Actual JST Excellon hole missing, duplicated, or wrong diameter';matches.append({'pin':h['pin'],'net':h['net'],'actual_excellon_x_mm':float(near[0][0]),'actual_excellon_y_mm':float(near[0][1]),'actual_tool_diameter_mm':float(near[0][2])})
 bom_names=[n for n in z.namelist() if pathlib.Path(n).name=='bom.csv'];assert len(bom_names)==1
 bom=z.read(bom_names[0]).decode();native_rows=list(csv.DictReader(bom.splitlines()));native_motor=next(row for row in native_rows if row['Designator']=='J_MOTOR');assert native_motor['JLCPCB Part #']=='C131334'
 supplier_rows=list(csv.DictReader((root/'artifacts/bom.csv').open()));row=next(e for e in supplier_rows if e['Reference']=='J_MOTOR');assert row['JLCPCB part']=='C131334' and row['MPN']=='B4B-PH-K-S(LF)(SN)' and row['Review note']=='native supplier import with OBJ and STEP'
cat=json.loads((root/'src/jlcpcb-catalog.json').read_text());part=cat['parts']['C131334']
for ext in ['step','obj']:
 f=root/next(f for f in part['modelFiles'] if f.endswith('.'+ext));assert hashlib.sha256(f.read_bytes()).hexdigest()==part['sha256'][ext]
report={'passed':True,'manufacturer_part_number':'B4B-PH-K-S(LF)(SN)','supplier_id':'C131334','mating_housing':'PHR-4','pins_1_through_4':['A_PLUS','A_MINUS','B_PLUS','B_MINUS'],'source_saved_delivered_checks':records,'actual_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'actual_plated_drill_file':files[0],'actual_plated_drill_sha256':hashlib.sha256(raw).hexdigest(),'actual_JST_drill_matches':matches,'drill_comparison_tolerance_mm':.0001,'native_and_supplier_BOM_include_fitted_JST':True,'native_BOM_value':native_motor['Value'],'native_BOM_identity_policy_requires_assembly_review':True,'original_STEP_and_OBJ_hashes_verified':True,'rear_motor_compatibility_verified':False}
(root/'artifacts/jst-restoration/connector-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
