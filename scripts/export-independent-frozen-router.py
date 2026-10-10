"""Prepare official Freerouting fallback with approved copper as fixed DSN geometry."""
import pathlib,json,subprocess,hashlib
r=pathlib.Path(__file__).resolve().parents[1];subprocess.run(['/workspace/.routing-venv/bin/python','scripts/export-supplier-router.py'],check=True,cwd=r)
j=json.loads((r/'artifacts/board.circuit.json').read_text());seeds=[e for e in j if e['type']in['pcb_trace','pcb_via']];m=json.loads((r/'artifacts/supplier-map.json').read_text());names={v:k for k,v in m['netkeys'].items()};ln={'top':'F.Cu','inner2':'In2.Cu','bottom':'B.Cu'};um=lambda v:f'{v*1000:.4f}';q=lambda x:json.dumps(x);fixed=[];viastacks={}
for e in seeds:
 name=names[e['subcircuit_connectivity_map_key']]
 if e['type']=='pcb_trace':
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']:
    assert a['layer']in ln
    fixed.append(f'(wire (path {ln[a["layer"]]} {um(max(a["width"],b["width"]))} {um(a["x"])} {um(a["y"])} {um(b["x"])} {um(b["y"])}) (net {q(name)}) (type fix))')
 else:
  stack=f'fixed_via_{um(e["outer_diameter"])}';viastacks[stack]=e['outer_diameter'];fixed.append(f'(via {q(stack)} {um(e["x"])} {um(e["y"])} (net {q(name)}) (type fix))')
s=(r/'artifacts/supplier-input.dsn').read_text();classes='(class "motor_power" '+' '.join(q(n)for n in ['PD_VBUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS'])+' (circuit (use_via "via500") (use_layer F.Cu B.Cu)) (rule (width 450) (clearance 150)))'
import re
s=re.sub(r'\(class "motor_power".*?\(rule \(width 300\) \(clearance 150\)\)\)',classes,s)
s,n=re.subn(r'\(wiring\s*', lambda _: '(wiring '+' '.join(fixed)+' ',s,count=1);assert n==1
assert s.count('(type fix)')>=len(fixed), 'Fixed copper was not serialized'
s,n=re.subn(r'\(library\s*', lambda _: '(library '+' '.join(f'(padstack {q(n)} '+' '.join(f'(shape (circle {l} {um(w)}))'for l in ln.values())+' (attach off))'for n,w in viastacks.items())+' ',s,count=1);assert n==1
# Automatic thermal-via insertion is replaced by the exact preserved and specified barrels.
for v in m['thermalVias']:
 original=f'(via "via500" {um(v["x"])} {um(v["y"])} (net "GND") (type fix))';s=s.replace(original,'')
(r/'artifacts/independent-input.dsn').write_text(s);(r/'artifacts/independent-map.json').write_text(json.dumps(m,indent=2)+'\n');(r/'artifacts/independent-unrouted.circuit.json').write_text((r/'artifacts/final-source.circuit.json').read_text());(r/'artifacts/independent-seeds.circuit.json').write_text(json.dumps(seeds,indent=2)+'\n');(r/'artifacts/validation/independent-freerouting-input.json').write_text(json.dumps({'nativeRouterBlocked':'Pipeline9 cannot reconnect preloaded trace supplier_repair_island_net0_26xxx for exact repair','fixedCopperRecords':len(seeds),'outerLayerPowerRule':True,'dsn_sha256':hashlib.sha256(s.encode()).hexdigest(),'state':'routing input; qualification pending'},indent=2)+'\n');print('Frozen records',len(seeds),'DSN fixed primitives',len(fixed))
