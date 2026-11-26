"""NEMA14 JST native pad/courtyard review with explicitly planned return corridors."""
from pathlib import Path
import json,hashlib,html,importlib.util
r=Path(__file__).resolve().parents[1];raw=(r/'artifacts/final-source.circuit.json').read_bytes();b=json.loads(raw);report=json.loads((r/'artifacts/critical-paths.json').read_text());assert report['board_sha256']==hashlib.sha256(raw).hexdigest()
spec=importlib.util.spec_from_file_location('copper',Path(__file__).with_name('inspect-copper.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
xy=lambda x,y:(365+14*x,320-14*y)
s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 750 700"><rect width="750" height="700" fill="white"/><text x="35" y="30" font-size="20">NEMA14 JST · planned star-return corridors</text>']
def line(points,color,width,dash=''):
 pts=' '.join('%.4f,%.4f'%xy(*p) for p in points);s.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" opacity=".72" stroke-dasharray="{dash}"/>')
def circle(x,y,rad,color,fill='none',dash=''):
 px,py=xy(x,y);s.append(f'<circle cx="{px}" cy="{py}" r="{rad*14}" fill="{fill}" stroke="{color}" stroke-width="1.2" stroke-dasharray="{dash}"/>')
line([[-17.5,-17.5],[17.5,-17.5],[17.5,17.5],[-17.5,17.5],[-17.5,-17.5]],'#294d48',1.5)
for e in b:
 if e['type']=='pcb_courtyard_outline' and e['layer']=='top':line([[p['x'],p['y']] for p in e['outline']],'#c7d4d1',.45)
 if e['type']=='pcb_smtpad' and e.get('layer')=='top' or e['type']=='pcb_plated_hole':
  shape=g.pad_shape(e);polys=list(shape.geoms) if hasattr(shape,'geoms') else [shape]
  for poly in polys:
   pts=' '.join('%.4f,%.4f'%xy(*p) for p in poly.exterior.coords);s.append(f'<polygon points="{pts}" fill="#9faaa7"/>')
for x in [-13,13]:
 for y in [-13,13]:circle(x,y,3.2,'#be4940',dash='5 3');circle(x,y,1.6,'#647a73','white')
for i,ret in enumerate(report['return_corridors']):
 color='#137a6c' if ret['placement_corridor_pass'] else '#c56118';line(ret['top_stub'],color,8.4);line(ret['inner1_path'],color,8.4,'8 5')
 for v in ret['via_centers']:circle(*v,.225,color,'white')
 s.append(f'<text x="40" y="{600+i*24}" font-size="15" fill="{color}">{html.escape(ret["source"])} → U_DRV.EP: {ret["path_length_mm"]:.3f} mm; target ≤5 mm</text>')
s += ['<text x="40" y="658" font-size="13">0.6 mm reserved width. Dashed paths are planned inner1 strips, not routed copper.</text>','<text x="40" y="678" font-size="9">Native Circuit JSON SHA256: '+hashlib.sha256(raw).hexdigest()+'</text>','</svg>'];(r/'review/critical-corridors.svg').write_text('\n'.join(s)+'\n')
