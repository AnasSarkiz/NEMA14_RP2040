"""Exact native copper review. This view is not a completed-board DRC claim."""
from pathlib import Path
import json,html,hashlib,importlib.util
spec=importlib.util.spec_from_file_location('copper',Path(__file__).with_name('inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
p=Path('artifacts/iteration-3/authored.circuit.json');raw=p.read_bytes();b=json.loads(raw);names={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};ports={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};traces={e['source_trace_id']:e.get('name','') for e in b if e['type']=='source_trace'}
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 1180"><rect width="1500" height="1180" fill="#f7f9fc"/>','<style>text{font-family:DejaVu Sans,sans-serif;fill:#19304a}.small{font-size:15px}.caption{font-size:18px}.head{font-size:28px;font-weight:bold}</style>', '<text x="38" y="42" class="head">NEMA14 JST · full-controller Kelvin integration</text>', '<text x="38" y="73" class="caption">Experimental copper only. 8 authored paths / 10 through vias. 66 other nets remain disconnected.</text>','<text x="38" y="102" class="caption">All component poses unchanged · locality 25/59 · production source unchanged</text>']
def view(cx,cy,scale,layer,clip=None):
 def xy(x,y):return cx+scale*x,cy-scale*y
 def line(points,color,width=1,dash=''):
  s.append('<polyline points="'+' '.join('%.4f,%.4f'%xy(*q) for q in points)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{dash}"/>')
 def circ(x,y,r,color,fill='none',width=1,dash=''):
  X,Y=xy(x,y);s.append(f'<circle cx="{X}" cy="{Y}" r="{r*scale}" fill="{fill}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
 line([[-17.5,-17.5],[17.5,-17.5],[17.5,17.5],[-17.5,17.5],[-17.5,-17.5]],'#294965',1.4)
 for e in b:
  if e['type']=='pcb_courtyard_outline' and e['layer']==layer:line([[q['x'],q['y']] for q in e['outline']],'#d5dce5',.6)
  if e['type']=='pcb_smtpad' and e.get('layer')==layer or e['type']=='pcb_plated_hole':
   poly=g.pad_shape(e);src=ports[pp[e['pcb_port_id']]['source_port_id']];name=names[src['source_component_id']];color='#c5cdd6' if not name.startswith('R_SHUNT') else '#a95b77'
   s.append('<polygon points="'+' '.join('%.4f,%.4f'%xy(*q) for q in poly.exterior.coords)+f'" fill="{color}"/>')
 for e in b:
  if e['type']=='pcb_trace':
   color='#b66a00' if traces[e['source_trace_id']].startswith('POWER') else '#007c86'
   for a,z in zip(e['route'],e['route'][1:]):
    if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']==layer:line([[a['x'],a['y']],[z['x'],z['y']]],color,a['width']*scale)
  if e['type']=='pcb_via':circ(e['x'],e['y'],e['outer_diameter']/2,'#19304a','#f7f9fc',.7);circ(e['x'],e['y'],e['hole_diameter']/2,'none','#19304a',0)
 for x in [-13,13]:
  for y in [-13,13]:
   circ(x,y,3.2,'#c94459',dash='4 3');circ(x,y,1.6,'#54637c','white');line([[x-3.2,y-3.2],[x+3.2,y-3.2],[x+3.2,y+3.2],[x-3.2,y+3.2],[x-3.2,y-3.2]],'#e6aeb7',.7,'3 3')
 if clip:
  for phase in 'AB':
   for pin in ['pin1','pin2']:
    p=next(p for p in pp.values() if names[ports[p['source_port_id']]['source_component_id']]=='R_SHUNT_'+phase and ports[p['source_port_id']]['name']==pin);X,Y=xy(p['x'],p['y']);s.append(f'<text x="{X+8}" y="{Y-7}" font-size="12">{phase} {pin}</text>')
s.append('<text x="40" y="143" class="caption">Top copper · 0.16 mm Kelvin / 0.45 mm winding</text>');view(375,470,18,'top')
s.append('<text x="790" y="143" class="caption">Bottom copper · same top-view coordinate system</text>');view(1125,470,18,'bottom')
s.append('<text x="40" y="825" class="caption">Actual shunt-pad pickups · top copper magnified (pad body exits separate from winding exits)</text>')
for i,phase in enumerate('AB'):
 component=next(e for e in b if e['type']=='pcb_component' and names[e['source_component_id']]=='R_SHUNT_'+phase);x,y=component['center']['x'],component['center']['y'];left=40+370*i
 s.append(f'<defs><clipPath id="clip{i}"><rect x="{left}" y="850" width="330" height="230" rx="8"/></clipPath></defs><rect x="{left}" y="850" width="330" height="230" rx="8" fill="white" stroke="#c5cdd6"/><g clip-path="url(#clip{i})">');view(left+165-80*x,965+80*y,80,'top',True);s.append(f'</g><text x="{left+12}" y="1106" class="caption">R_SHUNT_{phase} · 50 mΩ</text>')
s+=['<text x="820" y="883" class="caption">Native hard spacing / continuity checks: 0 findings</text>','<text x="820" y="915" class="caption">4 native net-wide thickness warnings retained</text>','<text x="820" y="947" class="caption">Four actual-pad cut tests pass; no shared winding copper</text>','<text x="820" y="979" class="caption">Kelvin A: 25.545 / 43.517 mm (long, mismatched)</text>','<text x="820" y="1011" class="caption">Neither 0.60 mm ground return is qualified</text>','<text x="820" y="1043" class="caption">Physical screw circles and stricter native boxes shown</text>',f'<text x="40" y="1150" class="small">Native authored JSON SHA256 {hashlib.sha256(raw).hexdigest()}</text>','</svg>'];Path('artifacts/iteration-3/integration-review.svg').write_text('\n'.join(s)+'\n')
