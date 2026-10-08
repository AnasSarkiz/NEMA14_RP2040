"""Freeze selected standard-via escape paths in the native-pad DSN."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
seeds=json.loads((ROOT/'artifacts/supplier-seeds.circuit.json').read_text())
src=json.loads((ROOT/'artifacts/final-source.circuit.json').read_text())
nets={e['subcircuit_connectivity_map_key']:e['name'] for e in src if e['type']=='source_net'}
records=[]
def path(net,points):
    if len(points)<2:return
    layer={'top':'F.Cu','bottom':'B.Cu','inner2':'In2.Cu'}[points[0]['layer']]
    records.append('(wire (path '+layer+' '+f'{points[0]["width"]*1000:.4f} '+' '.join(f'{p[k]*1000:.4f}' for p in points for k in ['x','y'])+') (net '+json.dumps(net)+') (type fix))')
for e in seeds:
    if not e.get(e['type']+'_id','').startswith('supplier_repair_'):continue
    net=nets[e['subcircuit_connectivity_map_key']]
    if e['type']=='pcb_trace':
        points=[]
        for p in e['route']:
            if p['route_type']=='via':path(net,points);points=[]
            else:points.append(p)
        path(net,points)
    else:
        records.append('(via "via500" '+f'{e["x"]*1000:.4f} {e["y"]*1000:.4f}'+' (net '+json.dumps(net)+') (type fix))')
p=ROOT/'artifacts/supplier-input.dsn';s=p.read_text();assert '(wiring ' in s
p.write_text(s.replace('(wiring ','(wiring '+' '.join(records)+' ',1))
print('Frozen',len(records),'DSN escape wire/via records')
