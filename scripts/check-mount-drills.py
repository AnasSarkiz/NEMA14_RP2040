"""Verify exact mounting geometry in source output, delivered Circuit JSON,
and the actual Excellon member of the native Gerber archive (metric/decimal).
"""
import decimal,hashlib,itertools,json,pathlib,re,zipfile
root=pathlib.Path(__file__).resolve().parents[1];expected=set(itertools.product([-13,13],repeat=2));records=[]
for name in ['artifacts/final-source.circuit.json','artifacts/board.circuit.json','index.circuit.json']:
 path=root/name;j=json.loads(path.read_text());holes=[e for e in j if e['type']=='pcb_hole' and not e.get('pcb_component_id')]
 assert len(holes)==4 and {(e['x'],e['y']) for e in holes}==expected and all(e['hole_diameter']==3.2 for e in holes),name+' mounting geometry mismatch'
 records.append({'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mounts_mm':sorted(expected),'diameter_mm':3.2})
assert json.loads((root/'index.circuit.json').read_text())==json.loads((root/'artifacts/board.circuit.json').read_text())
archive=root/'artifacts/nema14-gerbers.zip'
with zipfile.ZipFile(archive) as z:
 names=[n for n in z.namelist() if n.endswith('.drl') and 'npth' in n.lower()];assert len(names)==1
 raw=z.read(names[0]);text=raw.decode();assert 'METRIC' in text and 'G90' in text and 'NonPlated' in text
 tools={};tool=None;mounts=[];D=decimal.Decimal
 for line in text.splitlines():
  match=re.fullmatch(r'T(\d+)C([\d.]+)',line)
  if match:tools[match[1]]=D(match[2]);continue
  match=re.fullmatch(r'T(\d+)',line)
  if match:tool=match[1];assert tool in tools;continue
  match=re.fullmatch(r'X([+-]?[\d.]+)Y([+-]?[\d.]+)',line)
  if match and tools[tool]==D('3.2'):mounts.append((D(match[1]),D(match[2])))
 assert len(mounts)==4 and set(mounts)==expected,'Actual Ø3.2mm NPTH Excellon coordinates are not ±13mm'
report={'passed':True,'source_and_saved_json':records,'actual_drill_file':names[0],'actual_drill_sha256':hashlib.sha256(raw).hexdigest(),'gerber_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'drill_coordinates_mm':[[float(x),float(y)] for x,y in mounts],'drill_diameter_mm':3.2,'coordinate_system':'Absolute metric, PCB centre origin; no translation or mirroring applied','rear_motor_compatibility_verified':False}
(root/'artifacts/mount-drill-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
