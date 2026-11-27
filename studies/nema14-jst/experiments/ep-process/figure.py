from pathlib import Path
import json,math
from xml.sax.saxutils import escape
r=Path('artifacts/iteration-13');a=json.load(open(r/'digital-audit.json'));b=json.load(open('artifacts/iteration-11/final.circuit.json'))
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="710" viewBox="0 0 1080 710"><rect width="1080" height="710" fill="#f7f9fc"/><style>text{font-family:DejaVu Sans,sans-serif;fill:#15233c;font-size:15px}.h{font-size:23px;font-weight:bold}.s{font-size:12px}.red{fill:#9d2232}.b{font-weight:bold}</style>']
def text(x,y,s,cl=''):parts.append(f'<text x="{x}" y="{y}" class="{cl}">{escape(s)}</text>')
text(32,38,'NEMA14 JST — digital EP-via process review','h');text(32,65,'NOT FOR FABRICATION • no controller routing, footprint or process adoption','red')
text(32,105,'A. Select only the four cyan vias','b');text(32,127,'Mapped into prior comparison; grey = original vias','s')
scale=10;ox=230;oy=338
parts.append(f'<rect x="{ox-175}" y="{oy-175}" width="350" height="350" fill="white" stroke="#53637c" stroke-width="2"/>')
for e in b:
 if e['type']=='pcb_keepout' and e.get('radius')==3.2:parts.append(f'<circle cx="{ox+e["center"]["x"]*scale}" cy="{oy-e["center"]["y"]*scale}" r="32" fill="#e9f3ec" stroke="#477958"/>')
 if e['type']=='pcb_via':parts.append(f'<circle cx="{ox+e["x"]*scale}" cy="{oy-e["y"]*scale}" r="2.75" fill="#919caf"/>')
for row in a['board_overlay_new_via_only']:
 x=ox+row['board_x_mm']*scale;y=oy-row['board_y_mm']*scale;parts.append(f'<circle cx="{x}" cy="{y}" r="3.75" fill="#06a9bf" stroke="#006b80"/>')
parts.append('<path d="M321 251 L420 211" stroke="#006b80" fill="none"/>');text(423,209,'EP_TV1–4','b');text(423,229,'XY subset','s');text(55,544,'35 × 35 mm outline and four screw reserves retained','s');text(55,565,'No all-vias-of-diameter fill instruction.','red')
text(565,105,'B. Separate complete reference coupon','b');text(565,127,'3.15 mm EP; proposed paste and capped-via array','s')
cx=790;cy=325;s=60
pads=json.load(open('experiments/external-star/reference-pads.json'))
for p in pads:
 color='#d6dfeb' if p['pin']!=29 else '#b4c3d8';parts.append(f'<rect x="{cx+(p["x"]-p["width"]/2)*s}" y="{cy-(p["y"]+p["height"]/2)*s}" width="{p["width"]*s}" height="{p["height"]*s}" fill="{color}" stroke="#54677e"/>')
for x in [-.725,.725]:
 for y in [-.725,.725]:parts.append(f'<rect x="{cx+(x-.625)*s}" y="{cy-(y+.625)*s}" width="{1.25*s}" height="{1.25*s}" fill="#f3bb77" opacity=".8" stroke="#b06b1a"/>')
for i,row in enumerate(a['board_overlay_new_via_only']):
 x=cx+row['fixture_x_mm']*s;y=cy-row['fixture_y_mm']*s;parts.append(f'<circle cx="{x}" cy="{y}" r="{.375*s}" fill="#06a9bf" fill-opacity=".8" stroke="#006b80"/><circle cx="{x}" cy="{y}" r="{.15*s}" fill="#006b80"/>');text(x-4,y+5,str(i+1),'s')
text(565,546,'4 × 0.30 mm CAD holes / 0.75 mm lands / 1 mm pitch','s');text(565,568,'Paste: four 1.25 mm squares = 62.99%; 0.12 mm foil','s')
parts.append('<rect x="32" y="590" width="1016" height="93" rx="8" fill="#fff1df" stroke="#bd904f"/>');text(49,616,'Proposed only: drill + plate → selective epoxy fill → cure → planarize → copper cap → ENIG','b');text(49,640,'Native via = geometry/net/tenting. Fill, cap and flatness require an explicit drawing and production-file confirmation.','s');text(49,663,'Four native EP placement errors remain. VREG ground loop is open. No manufacturing or thermal acceptance.','red')
parts.append('</svg>');(r/'process-review.svg').write_text(''.join(parts))
import subprocess
subprocess.run(['inkscape',str(r/'process-review.svg'),'--export-type=png','--export-filename='+str(r/'process-review.png')],check=True)
