"""Actual native geometry close-ups, including conservative native keepout bounds."""
from pathlib import Path
import json,sys,html
from model import *
j=read(sys.argv[1]);names,co,pc,sp,pp,ports,courts=index(j);st={e['source_trace_id']:e.get('name','') for e in j if e['type']=='source_trace'}
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="800" viewBox="0 0 1160 800"><rect width="1160" height="800" fill="#f7f8fa"/>']
def text(x,y,s,size=16,color='#17212b'):svg.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{size}" fill="{color}">{html.escape(s)}</text>')
text(26,36,'NEMA14 JST · actual CP2 and buzzer copper',26)
text(26,65,'Separate comparison: 43 traces / 22 vias. Accepted controller and prior baseline unchanged.',16)
for x,y,w,h,bounds,label,layers in [(24,88,460,450,(8.5,6.8,12.9,10.6),'Driver charge pump · TOP',['top']),(508,88,628,450,(-10,-16.2,11.2,-5.4),'Buzzer power loops · TOP + INNER2',['top','inner2'])]:
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="white" stroke="#cfd6df"/>');text(x+15,y+28,label,18);a,b,c,d=bounds;scale=min((w-35)/(c-a),(h-65)/(d-b));ox=x+18-a*scale;oy=y+50+d*scale;svg.append(f'<g transform="translate({ox},{oy}) scale({scale},{-scale})">')
 def poly(p,color,stroke=None):
  if p.is_empty:return
  if hasattr(p,'geoms'):
   for q in p.geoms:poly(q,color,stroke)
  else:svg.append('<path d="'+' '.join(('M' if i==0 else 'L')+f'{xx},{yy}' for i,(xx,yy) in enumerate(p.exterior.coords))+' Z" fill="'+color+'"'+(f' stroke="{stroke}" stroke-width=".025"' if stroke else '')+'/>')
 clip=box(a,b,c,d)
 for e in j:
  if e['type']=='pcb_keepout':
   cx,cy,r=e['center']['x'],e['center']['y'],e['radius'];poly(box(cx-r,cy-r,cx+r,cy+r).intersection(clip),'#fff1ef');p=Point(cx,cy).buffer(r,quad_segs=128).intersection(clip);poly(p,'#f5ceca')
 for e in j:
  if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and set(layers)&set(e.get('layers',[e.get('layer','top')])):poly(g.pad_shape(e).intersection(clip),'#acb7c3')
 for e in j:
  if e['type']!='pcb_trace':continue
  n=st[e['source_trace_id']];color='#257b4a' if n.startswith('RETURN') else '#ba5320' if n.startswith('BUZ_') else '#1568c0'
  for v,z in zip(e['route'],e['route'][1:]):
   if v['route_type']==z['route_type']=='wire' and v['layer']==z['layer'] and v['layer'] in layers:
    if v['layer']=='inner2':color='#8d43a3'
    poly(LineString([(v['x'],v['y']),(z['x'],z['y'])]).buffer(v['width']/2,quad_segs=64).intersection(clip),color)
 for e in j:
  if e['type']=='pcb_via':poly(g.pad_shape(e).intersection(clip),'#9f6922');poly(g.pad_shape(e,True).intersection(clip),'white')
 svg.append('</g>')
text(26,570,'CP2: EP 0.820 mm · native square 0.360 mm · real circle 0.619 mm; rule stays 0.15 mm.',17)
text(26,601,'Buzzer external copper: flyback 13.325 mm; switch 35.399 mm including 2.843 mm barrel travel.',17)
text(26,632,'Baseline pad-edge lower bounds: flyback 56.265 mm; switch 37.928 mm. No baseline routed loop exists.',16)
text(26,668,'Blue: charge pump / Kelvin · Orange: buzzer TOP · Purple: supply INNER2 · Green: driver returns',15)
text(26,702,'Nominal full placement: 0 shorts / spacing / courtyard findings. 60 nets remain open.',17)
text(26,735,'Unapproved small-hole process; 24 width-stress spacing findings. Physical handling and CAM unverified.',16,'#ab3030')
text(26,770,'Diagram shows actual native copper. It is not a completed or fabrication-qualified controller.',15)
svg.append('</svg>');Path(sys.argv[2]).write_text(''.join(svg))
