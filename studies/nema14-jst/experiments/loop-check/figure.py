from pathlib import Path
import json,sys,subprocess
from xml.sax.saxutils import escape
sys.path.insert(0,'experiments/external-star')
from model import *
r=Path('artifacts/iteration-14');a=read(r/'audit.json');j=read(r/'candidate.circuit.json');_,_,_,sp,pp,ps,_=index(j);pads={e['pcb_port_id']:e for e in j if e['type']=='pcb_smtpad'};st={e['source_trace_id']:e.get('name') for e in j if e['type']=='source_trace'};tr={st[e['source_trace_id']]:e for e in j if e['type']=='pcb_trace'}
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="745"><rect width="1080" height="745" fill="#f6f8fc"/><style>text{font:14px DejaVu Sans,sans-serif;fill:#20304c}.h{font-size:23px;font-weight:bold}.b{font-weight:bold}.s{font-size:12px}.red{fill:#ac2439}</style>']
def text(x,y,s,c=''):svg.append(f'<text x="{x}" y="{y}" class="{c}">{escape(s)}</text>')
text(28,36,'NEMA14 JST — VREG loop and EP placement checks','h');text(28,63,'Separate comparison • native ground-length gate retained • fabrication on hold','red')
text(28,101,'A. Real top copper; no moved parts or new vias','b')
X=lambda x:45+(x-4)*64;Y=lambda y:520-(y-5.5)*64
for k in [('U_DRV',p) for p in ['OUT2B','ENABLE_N','GND','CP1','CP2','VCP','NC7','VREG','MS1','MS2','MS3','RESET_N','ROSC','SLEEP','VDD','STEP','REF','GND18','DIR','NC20','OUT1B','VBB1','SENSE1','OUT1A','NC25','OUT2A','SENSE2','VBB2','EP']]+[('C_VREG','pin1'),('C_VREG','pin2')]:
 poly=g.pad_shape(pads[ps[k]['pcb_port_id']]);coords=list(poly.exterior.coords);d=' '.join(('M' if i==0 else 'L')+f'{X(x):.3f},{Y(y):.3f}' for i,(x,y) in enumerate(coords));color='#eb9aab' if k[1]=='RESET_N' else '#c2cfdf';svg.append(f'<path d="{d} Z" fill="{color}" stroke="#667a93" stroke-width=".8"/>')
for n,col in [('AUTHORED_VREG_BASELINE','#d58118'),('VREG_GROUND_LOOP','#008da5')]:
 pts=tr[n]['route'];d=' '.join(('M' if i==0 else 'L')+f'{X(q["x"]):.3f},{Y(q["y"]):.3f}' for i,q in enumerate(pts));svg.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{pts[0]["width"]*64}" stroke-linecap="round" stroke-linejoin="round"/>')
text(45,132,'C_VREG','b');text(212,198,'RESET_N','red');text(240,419,'EP','b');text(38,596,'Cyan: ground; orange: preserved VREG positive trace','s');text(38,618,'External PCB copper travel: 6.981761 mm (both legs)','b');text(38,638,'Internal component paths and actual loop area unknown','s')
text(570,105,'B. Ground-limit geometry, unchanged rules','b');text(570,138,'Driver courtyard beyond EP: ≥1.599870 mm');text(570,166,'Cap ground-pad courtyard inset: ≥0.250000 mm');text(570,194,'Optimistic two end-cap reach: −0.160000 mm');text(570,227,'Wire lower bound: ≥1.689870 mm','b');text(570,255,'Native ground maximum: 1.000000 mm','red');text(570,283,'Orthogonal top-side poses, retained courtyards only','s');text(570,306,'No limit override, courtyard overlap or source splitting','s')
text(570,354,'C. Minimal native EP controls','b');text(570,384,'Control','s');text(858,384,'Overlap','s');text(950,384,'Electrical','s')
for y,n,o,e in [(414,'Same GND / bottom tented',4,0),(443,'Same GND / exposed',4,0),(472,'Foreign net / same geometry',4,4),(501,'Same GND / holes outside',0,0),(530,'Pad / no vias',0,0)]:text(570,y,n,'s');text(885,y,str(o),'b');text(982,y,str(e),'b')
text(570,568,'Overlap rule reads shared layers + drill geometry.','s');text(570,590,'It does not read fill/cap/planarization or net ownership.','s');text(570,612,'No per-via process qualification in this native pin.','s')
svg.append('<rect x="28" y="665" width="1024" height="58" rx="8" fill="#fff0df" stroke="#bd8e49"/>');text(43,689,'STOP: ground-length policy and two inherited star-drill failures still block promotion.','b');text(43,711,'59 disconnected nets remain. Accepted source, footprint, mechanical locks and fabrication process are unchanged.','s');svg.append('</svg>');(r/'loop-review.svg').write_text(''.join(svg));subprocess.run(['inkscape',str(r/'loop-review.svg'),'--export-type=png','--export-filename='+str(r/'loop-review.png')],check=True)
