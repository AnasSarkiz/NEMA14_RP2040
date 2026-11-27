"""Before/after native geometry with real +20% copper envelopes."""
from model import *
from shapely.ops import unary_union
import html
j=read('artifacts/iteration-9/final.circuit.json');svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="850" viewBox="0 0 1160 850"><rect width="1160" height="850" fill="#f7f8fa"/>']
def text(x,y,s,n=16,c='#17212b'):svg.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{n}" fill="{c}">{html.escape(s)}</text>')
text(26,36,'NEMA14 JST · tolerance-aware charge-pump comparison',25);text(26,65,'Same top-side driver, returns, Kelvin pickups, buzzer copper and 22 vias. Only C_CP and its two routes move.',15)
for ox,data,title in [(24,b,'BEFORE · 13 introduced stress findings'),(594,j,'AFTER · 0 introduced stress findings')]:
 svg.append(f'<rect x="{ox}" y="88" width="542" height="470" rx="8" fill="white" stroke="#cfd6df"/>');text(ox+15,117,title,18);clip=box(9.3,7.0,12.9,10.0);scale=132;svg.append(f'<g transform="translate({ox+18-9.3*scale},{137+10*scale}) scale({scale},{-scale})">')
 def poly(p,color,stroke=None):
  if p.is_empty:return
  if hasattr(p,'geoms'):
   for q in p.geoms:poly(q,color,stroke)
  else:svg.append('<path d="'+' '.join(('M' if i==0 else 'L')+f'{x},{y}' for i,(x,y) in enumerate(p.exterior.coords))+' Z" fill="'+color+'"'+(f' stroke="{stroke}" stroke-width=".008"' if stroke else '')+'/>')
 poly(box(9.8,9.8,16.2,16.2).intersection(clip),'#fff0ee');poly(Point(13,13).buffer(3.2,quad_segs=64).intersection(clip),'#f0cbc6')
 st={e['source_trace_id']:e.get('name','') for e in data if e['type']=='source_trace'}
 for e in data:
  if e['type']=='pcb_smtpad' and e['layer']=='top':poly(g.pad_shape(e).intersection(clip),'#aeb9c5')
 for e in data:
  if e['type']!='pcb_trace':continue
  name=st[e['source_trace_id']];cp=name.startswith('AUTHORED_CP');color='#176eb4' if cp else '#778d80'
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']=='top':
    line=LineString([(a['x'],a['y']),(z['x'],z['y'])]);poly(line.buffer(a['width']*.6,quad_segs=64).intersection(clip),'#95d6ed' if cp else '#d9e3da');poly(line.buffer(a['width']/2,quad_segs=64).intersection(clip),color)
 for e in data:
  if e['type']=='pcb_via':poly(g.pad_shape(e).intersection(clip),'#9f6922');poly(g.pad_shape(e,True).intersection(clip),'white')
 svg.append('</g>');text(ox+15,542,'Light envelopes: +20% trace width. Gray: real pads. Pink: square / circle exclusions.',11)
text(26,590,'CP1 wire 2.296 → 1.820 mm · CP2 wire 3.299 → 2.126 mm · nominal width 0.16 mm, stress width 0.192 mm.',17)
text(26,624,'Minimum stressed gaps: CP1 0.150559 mm / CP2 0.150501 mm; unchanged required clearance 0.15 mm.',17)
text(26,658,'CP2 stress: EP 0.803872 mm · native square 0.323884 mm · real circle 0.622362 mm.',17)
text(26,692,'Capacitor pad-to-square 0.169885 mm · combined CP drill/width margin +0.075874 mm.',17)
text(26,731,'Full board: 11 inherited stress spacing failures; 3 inherited combined drill/width failures; 59 open nets.',17,'#a62b2b')
text(26,765,'VREG copper stays exact; named replay exposes native 1 mm maximum versus 2.606 mm actual. Gate retained.',16,'#a62b2b')
text(26,807,'Verified local improvement only. No new native routing, process approval, physical fit or fabrication readiness.',16)
svg.append('</svg>');Path('artifacts/iteration-9/charge-pump-review.svg').write_text(''.join(svg))
