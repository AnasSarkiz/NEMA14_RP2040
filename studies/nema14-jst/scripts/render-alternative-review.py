"""Native geometry map of an unadopted placement comparison; no routing shown."""
from pathlib import Path
import json,sys,hashlib,html,importlib.util
jpath,delta_path,out=map(Path,sys.argv[1:4]);raw=jpath.read_bytes();b=json.loads(raw);delta=json.loads(delta_path.read_text());src={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};pc={e['pcb_component_id']:e for e in b if e['type']=='pcb_component'};names={src[e['source_component_id']]:e for e in pc.values()};spec=importlib.util.spec_from_file_location('copper',Path(__file__).with_name('inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
xy=lambda x,y:(370+18*x,405-18*y);s=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="900" viewBox="0 0 1120 900"><rect width="1120" height="900" fill="#f8fafc"/><g font-family="sans-serif"><text x="45" y="37" font-size="24" fill="#16324f">NEMA14 JST · unadopted placement comparison</text><text x="45" y="64" font-size="15">10 top moves + two bottom capacitors · 21/59 locality · no routed-board qualification</text>']
def poly(points,fill,stroke,width=.8,dash=''):
 s.append('<polygon points="'+' '.join('%.3f,%.3f'%xy(*p) for p in points)+f'" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
poly([[-17.5,-17.5],[17.5,-17.5],[17.5,17.5],[-17.5,17.5]],'white','#466070',1.4)
for e in b:
 if e['type']=='pcb_courtyard_outline':
  n=src[pc[e['pcb_component_id']]['source_component_id']]
  if e['layer']=='top' or n in delta:poly([[q['x'],q['y']] for q in e['outline']],'none','#9ab1bd' if n not in delta else '#8756ad' if e['layer']=='bottom' else '#087e8b',.7 if n not in delta else 1.8,'5 3' if e['layer']=='bottom' else '')
 if e['type']=='pcb_smtpad' and e.get('layer')=='top' or e['type']=='pcb_plated_hole':
  q=g.pad_shape(e);polys=list(q.geoms) if hasattr(q,'geoms') else [q]
  for p in polys:poly(list(p.exterior.coords),'#c7d0d7','none')
for x in [-13,13]:
 for y in [-13,13]:
  px,py=xy(x,y);s.append(f'<circle cx="{px}" cy="{py}" r="57.6" fill="none" stroke="#be493d" stroke-width="2" stroke-dasharray="5 4"/><circle cx="{px}" cy="{py}" r="28.8" fill="#f8fafc" stroke="#7b8d96"/>')
for i,n in enumerate(delta,1):
 p=names[n];x,y=xy(p['center']['x'],p['center']['y']);color='#8756ad' if p['layer']=='bottom' else '#087e8b';s.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{color}"/><text x="{x}" y="{y+3.4}" font-size="10" text-anchor="middle" fill="white">{i}</text>');yy=130+(i-1)*42;s.append(f'<text x="735" y="{yy}" font-size="16" fill="{color}">{i}. {html.escape(n)} · {p["layer"]}</text><text x="754" y="{yy+18}" font-size="12" fill="#526574">({p["center"]["x"]:.2f}, {p["center"]["y"]:.2f}) mm · {p["rotation"]:.0f}°</text>')
s += ['<text x="45" y="775" font-size="16" fill="#8756ad">Bottom C_BUCK_OUT1 / C_BUCK_OUT2: supplier bodies extend 1.30 mm below PCB.</text>','<text x="45" y="805" font-size="14">Four screw exclusions and catalog plug service envelope retained. Rear motor/magnet fit unverified.</text>','<text x="45" y="835" font-size="14">Accepted all-top layout remains unchanged at 25/59 locality. This comparison is not adopted.</text>',f'<text x="45" y="865" font-size="10">Native input SHA256: {hashlib.sha256(raw).hexdigest()}</text>','</g></svg>'];out.write_text('\n'.join(s)+'\n')
