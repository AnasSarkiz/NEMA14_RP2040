"""Merge native placements while retaining still-connected copper.

All terminal partitions must remain unchanged except nets whose actual foreign
copper collides with a moved pad. No qualification result is inferred here.
"""
import json,sys,hashlib
from shapely.geometry import Point,LineString
import verify_supplier_connectivity as g
names=set(sys.argv[1:]);fresh=json.loads((g.ROOT/'artifacts/final-source.circuit.json').read_text())
assert not [e for e in fresh if e['type'].endswith('_error')]
for typ in ['source_component','source_port','source_net','source_trace']:
 assert [e for e in fresh if e['type']==typ]==[e for e in g.j if e['type']==typ], 'Logical source changed: '+typ
sids={sid for sid,n in g.src.items() if n in names};assert len(sids)==len(names)
cids={e['pcb_component_id'] for e in g.j if e['type']=='pcb_component' and e['source_component_id'] in sids}
def selected(e):
 return e.get('pcb_component_id') in cids or e['type']=='cad_component' and e.get('source_component_id') in sids
replacements=[e for e in fresh if selected(e)]
assert {e['pcb_component_id'] for e in replacements if e['type']=='pcb_component'}==cids
pads=[e for e in replacements if e['type'] in ['pcb_smtpad','pcb_plated_hole']]
def signature(net):
 es,rs=g.groups(net);groups={}
 for e,r in zip(es,rs):
  if e.get('pcb_port_id'):groups.setdefault(r,set()).add(e['pcb_port_id'])
 return sorted(tuple(sorted(v)) for v in groups.values())
before={k:signature(k) for k in g.nets};before_sha=hashlib.sha256(g.path.read_bytes()).hexdigest();ripped=[]
protected={'USB_DP','USB_DM','MCU_DP','MCU_DM','XIN','XOUT','XTAL_OUT','QSPI_SCLK','QSPI_SD0','QSPI_SD1','QSPI_SD2','QSPI_SD3','QSPI_SS','RUN','SWCLK','SWDIO'}
for e in list(g.j):
 typ=e['type'];hit=False
 if typ=='pcb_trace':
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
   shape=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
   if any(g.key(e)!=g.key(p) and a['layer'] in p.get('layers',[p.get('layer','top')]) and shape.distance(g.geometry(p))<.15-1e-6 for p in pads):hit=True;break
 elif typ=='pcb_via':
  land=Point(e['x'],e['y']).buffer(e['outer_diameter']/2);hole=Point(e['x'],e['y']).buffer(e['hole_diameter']/2)
  hit=any(land.distance(g.geometry(p))<.15-1e-6 if g.key(e)!=g.key(p) else hole.intersects(g.geometry(p)) for p in pads)
 if hit:
  assert g.nets.get(g.key(e)) not in protected, 'Moved placement conflicts with protected copper'
  ripped.append({'id':e[typ+'_id'],'net':g.nets.get(g.key(e)),'record':e})
ids={r['id'] for r in ripped};g.j[:]=[e for e in g.j if not selected(e) and e.get(e['type']+'_id') not in ids]+replacements
changed_nets={r['net'] for r in ripped}
for k,n in g.nets.items():
 if n not in changed_nets:assert signature(k)==before[k], 'Retained copper lost a physical terminal: '+n
g.path.write_text(json.dumps(g.j,indent=2)+'\n');out=g.ROOT/'artifacts/opposite-edge/native-placement-retained-copper.json';history=json.loads(out.read_text()) if out.exists() else [];history.append({'components':sorted(names),'before_sha256':before_sha,'after_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'logical_records_identical':True,'all_unaffected_pad_partitions_preserved':True,'displaced_foreign_copper':ripped,'construction_only_full_qualification_required':True});out.write_text(json.dumps(history,indent=2)+'\n');print('Native placement merged; all unaffected terminal partitions preserved; displaced',[(r['id'],r['net']) for r in ripped])
