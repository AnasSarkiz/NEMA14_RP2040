"""Draw actual scoped native copper, not reserved corridors or a completed board."""
from pathlib import Path
import json,html,math
import sys
b=json.load(open(sys.argv[1]));sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};names={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};st={e['source_trace_id']:e.get('name','') for e in b if e['type']=='source_trace'}
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="1340" viewBox="0 0 1160 1340"><rect width="1160" height="1340" fill="#f7f8fa"/>']
def text(x,y,s,size=16,color='#17212b'):svg.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" fill="{color}">{html.escape(s)}</text>')
text(30,38,'NEMA14 JST · regenerated anchored copper',26);text(30,68,'53-part authored scope only. Experimental four 0.20 mm holes; accepted source unchanged.',17)
for i,layer in enumerate(['top','inner1','inner2','bottom']):
 x=30+(i%2)*570;y=100+(i//2)*510;svg.append(f'<rect x="{x}" y="{y}" width="550" height="490" rx="8" fill="white" stroke="#cfd6df"/>');text(x+18,y+30,layer.upper(),19);svg.append(f'<g transform="translate({x+260},{y+255}) scale(11,-11)"><rect x="-17.5" y="-17.5" width="35" height="35" fill="#eef2f4" stroke="#1e293b" stroke-width=".12"/>')
 for e in b:
  if e['type']=='pcb_keepout':svg.append(f'<circle cx="{e["center"]["x"]}" cy="{e["center"]["y"]}" r="{e["radius"]}" fill="#fff0ef" stroke="#b83131" stroke-width=".10" stroke-dasharray=".3,.2"/>')
  elif e['type']=='pcb_hole':svg.append(f'<circle cx="{e["x"]}" cy="{e["y"]}" r="{e["hole_diameter"]/2}" fill="white" stroke="#6d7480" stroke-width=".08"/>')
 for e in b:
  if e['type'] not in ['pcb_smtpad','pcb_plated_hole']:continue
  if layer not in e.get('layers',[e.get('layer','top')]):continue
  if e.get('shape')=='polygon':svg.append('<polygon points="'+' '.join(f'{p["x"]},{p["y"]}' for p in e['points'])+'" fill="#9aa8b9"/>');continue
  w=e.get('width',e.get('outer_width',e.get('outer_diameter',e.get('radius',0)*2)));h=e.get('height',e.get('outer_height',w));shape=e.get('shape',e.get('hole_shape','circle'));angle=e.get('ccw_rotation',0)
  if shape=='circle':svg.append(f'<circle cx="{e["x"]}" cy="{e["y"]}" r="{w/2}" fill="#9aa8b9"/>')
  else:svg.append(f'<rect x="{e["x"]-w/2}" y="{e["y"]-h/2}" width="{w}" height="{h}" rx="{min(w,h)/2 if shape in ["pill","rotated_pill"] else 0}" transform="rotate({angle} {e["x"]} {e["y"]})" fill="#9aa8b9"/>')
 for e in b:
  if e['type']!='pcb_trace':continue
  name=st[e['source_trace_id']];color='#28733b' if name.startswith('RETURN') else '#cd6120' if name.startswith('POWER') else '#116cc5'
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']==layer:svg.append(f'<line x1="{a["x"]}" y1="{a["y"]}" x2="{z["x"]}" y2="{z["y"]}" stroke="{color}" stroke-width="{min(a["width"],z["width"])}" stroke-linecap="round"/>')
 for e in b:
  if e['type']=='pcb_via' and layer in e['layers']:svg.append(f'<circle cx="{e["x"]}" cy="{e["y"]}" r="{e["outer_diameter"]/2}" fill="#9f6922"/><circle cx="{e["x"]}" cy="{e["y"]}" r="{e["hole_diameter"]/2}" fill="white"/>')
 svg.append('</g>')
 for e in b:
  if e['type']=='pcb_component' and names.get(e['source_component_id']) in ['U_DRV','R_SHUNT_A','R_SHUNT_B','U_IA','U_IB','R_SA','R_SB','J_MOTOR']:
   cx=x+260+e['center']['x']*11;cy=y+255-e['center']['y']*11;text(cx-9,cy-10,names[e['source_component_id']].replace('R_SHUNT_','SH_'),10)
 text(x+18,y+468,'Red circles: fixed screw reserves. All vias are through holes.',12,'#5a6471')
text(30,1150,'Blue 0.16 mm Kelvin · Orange 0.45 mm winding · Green 0.60 mm ground',18)
text(30,1180,'Authored scope: 0 shorts / 0 spacing findings; 36 subset nets still open.',17)
text(30,1210,'Returns including annulus access + conducted barrels: 4.892 / 4.572 mm.',17)
text(30,1240,'Named stack / fill-cap comparison only. Tolerance and width-stress checks fail.',17,'#aa3030')
text(30,1270,'Full candidate: 33 shorts / 39 spacing. Native CP1 adds two spacing findings.',17,'#aa3030')
text(30,1305,'This map shows actual authored copper, not a routed-controller DRC pass.',15)
svg.append('</svg>');Path(sys.argv[2]).write_text(''.join(svg))
