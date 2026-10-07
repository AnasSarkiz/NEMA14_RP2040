"""Merge supplier/CAD/schematic metadata while retaining every saved PCB record."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json'
a=json.loads(path.read_text());b=json.loads((root/'artifacts/final-source.circuit.json').read_text())
idkey=lambda e:e.get(e['type']+'_id')
oldports={idkey(e):e for e in a if e['type']=='source_port'};newports={idkey(e):e for e in b if e['type']=='source_port'}
assert oldports.keys()==newports.keys(),'Physical source pin identities changed'
for k,o in oldports.items():
 for field in ['source_component_id','pin_number','name','subcircuit_connectivity_map_key']:
  assert o.get(field)==newports[k].get(field),f'Pin/net changed: {k}.{field}'
source={idkey(e):e for e in b if e['type'].startswith('source_') and not e['type'].endswith(('_warning','_error'))}
for e in a:
 if e['type']=='source_component':assert e['name']==source[idkey(e)]['name']
keep=[source.get(idkey(e),e) if e['type'].startswith('source_') else e for e in a
      if not e['type'].startswith('schematic_') and e['type']!='cad_component'
      and not e['type'].endswith(('_error','_warning'))]
new=keep+[e for e in b if (e['type'].startswith('schematic_') or e['type']=='cad_component')
          and not e['type'].endswith(('_warning','_error'))]
def pcb(records):return [e for e in records if e['type'].startswith('pcb_') and not e['type'].endswith(('_warning','_error'))]
assert pcb(a)==pcb(new),'Saved PCB geometry changed'
path.write_text(json.dumps(new,indent=2)+'\n')
proof={'savedPcbGeometryUnchanged':True,'sourcePinsAndNetsUnchanged':True,
       'pcbGeometrySha256':hashlib.sha256(json.dumps(pcb(new),sort_keys=True,separators=(',',':')).encode()).hexdigest(),
       'boardSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
       'nativeA4Sheets':[e for e in new if e['type']=='schematic_sheet'],
       'componentModels':sum(e['type']=='cad_component' and bool(e.get('model_obj_url')) for e in new)}
(root/'artifacts/presentation-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Saved PCB geometry/pin identities retained; attached',proof['componentModels'],'supplier models')
