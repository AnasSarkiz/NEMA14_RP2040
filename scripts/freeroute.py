"""Export actual Circuit JSON pad geometry; add explicit exposed-pad ground vias.
The original tscircuit autorouting is retained in artifacts/autorouted.circuit.json.
"""
import json,math,pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def q(s):return json.dumps(str(s))
def um(x):return f'{x*1000:.3f}'
j=json.loads((ROOT/'artifacts/unrouted.circuit.json').read_text())
ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'}
sourceports={e['source_port_id']:e for e in j if e['type']=='source_port'}
nets={e.get('subcircuit_connectivity_map_key'):e['name'] for e in j if e['type']=='source_net'}
netids={e['name']:e['source_net_id'] for e in j if e['type']=='source_net'}
padnet={};netpins={};shapes=[];images=[];placements=[];pinmap={};padcount=0
for comp in [e for e in j if e['type']=='pcb_component']:
 cid=comp['pcb_component_id'];cx,cy=comp['center']['x'],comp['center']['y'];pins=[]
 for pad in [e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and e.get('pcb_component_id')==cid]:
  padcount+=1;pid=pad.get('pcb_port_id');port=ports.get(pid,{});sp=sourceports.get(port.get('source_port_id'),{})
  key=sp.get('subcircuit_connectivity_map_key');net=nets.get(key) if key else None
  if not net:net='SIGNAL_'+key.rsplit('_',1)[-1] if key else f'NC_{padcount}'
  padnet[pad.get('pcb_smtpad_id',pad.get('pcb_plated_hole_id'))]=net
  pin=f'p{padcount}';pinmap[cid+'-'+pin]={'pcb_port_id':pid,'net':net}
  if pad['type']=='pcb_smtpad':
   w=pad.get('width',pad.get('radius',0)*2);h=pad.get('height',pad.get('radius',0)*2);layers=[pad['layer']]
  else:w=pad.get('outer_width',pad.get('outer_diameter',0));h=pad.get('outer_height',pad.get('outer_diameter',0));layers=['top','bottom']
  angle=pad.get('ccw_rotation',0)%180
  if abs(angle-90)<.01:w,h=h,w
  desc=[]
  for layer in layers:
   l='F.Cu' if layer=='top' else 'B.Cu';desc.append(f'(shape (rect {l} {um(-w/2)} {um(-h/2)} {um(w/2)} {um(h/2)}))')
  shape=f'pad_{padcount}';shapes.append(f'(padstack {q(shape)} '+ ' '.join(desc)+' (attach off))')
  pins.append(f'(pin {q(shape)} {q(pin)} {um(pad["x"]-cx)} {um(pad["y"]-cy)})')
  netpins.setdefault(net,[]).append(cid+'-'+pin)
 images.append(f'(image {q(cid)} '+ ' '.join(pins)+')')
 placements.append(f'(component {q(cid)} (place {q(cid)} {um(cx)} {um(cy)} front 0))')
keep=[]
for i,e in enumerate([e for e in j if e['type']=='pcb_hole']):
 x=e.get('x',e.get('center',{}).get('x',0));y=e.get('y',e.get('center',{}).get('y',0));d=e.get('hole_diameter',e.get('diameter',0))
 for l in ['F.Cu','B.Cu']:keep.append(f'(keepout {q("hole"+str(i)+l)} (circle {l} {um(d+.1)} {um(x)} {um(y)}))')
for i,e in enumerate([e for e in j if e['type']=='pcb_keepout']):
 c=e.get('center',e); x=c.get('x',0);y=c.get('y',0)
 for l in ['F.Cu','B.Cu']:keep.append(f'(keepout {q("head"+str(i)+l)} (rect {l} {um(x-2.7)} {um(y-2.7)} {um(x+2.7)} {um(y+2.7)}))')
thermal=[]
sourcenames={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'}
for c in [e for e in j if e['type']=='pcb_component' and sourcenames.get(e['source_component_id']) in ['U_MCU','U_DRV','U_PD']]:
 p=next(p for p in j if p['type']=='pcb_smtpad' and p.get('pcb_component_id')==c['pcb_component_id'] and p.get('width',0)>1 and p.get('height',0)>1)
 thermal.append({'x':p['x'],'y':p['y'],'net':'GND','component':sourcenames[c['source_component_id']]})
# Neck-down is handled by the router at IC pads. Long motor/power traces use 0.30mm.
wide=['PD_VBUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2']
classes=f'(class "signals" '+ ' '.join(q(n) for n in netpins if n not in wide)+' (circuit (use_via "via600")) (rule (width 200) (clearance 150)))'
classes+=f'(class "motor_power" '+ ' '.join(q(n) for n in wide)+' (circuit (use_via "via600")) (rule (width 300) (clearance 150)))'
via='(padstack "via600" (shape (circle F.Cu 600)) (shape (circle B.Cu 600)) (attach off))'
text='(pcb nema14 (parser (string_quote ") (space_in_quoted_tokens on)) (resolution um 10) (unit um)'
text+='(structure (layer F.Cu (type signal) (property (index 0))) (layer B.Cu (type signal) (property (index 1))) (boundary (path pcb 0 -17200 -17200 17200 -17200 17200 17200 -17200 17200 -17200 -17200)) (via "via600") (rule (width 200) (clearance 150)) '+ ' '.join(keep)+')'
text+='(placement '+' '.join(placements)+') (library '+' '.join(images+shapes+[via])+')'
text+='(network '+' '.join(f'(net {q(n)} (pins '+' '.join(p for p in pp)+'))' for n,pp in netpins.items())+' '+classes+')'
text+='(wiring '+' '.join(f'(via "via600" {um(v["x"])} {um(v["y"])} (net "GND") (type fix))' for v in thermal)+'))\n'
(ROOT/'artifacts/freerouting-input.dsn').write_text(text)
(ROOT/'artifacts/freerouting-map.json').write_text(json.dumps({'pinmap':pinmap,'thermalVias':thermal,'netids':netids},indent=2)+'\n')
print(f'Exported {padcount} physical pads, {len(netpins)} nets, {len(thermal)} explicit exposed-pad thermal vias.')
