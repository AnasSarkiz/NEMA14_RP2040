"""Add readable captions and labels at Blender's native projected part positions."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];review=root/'review';sha=hashlib.sha256((root/'artifacts/final-source.circuit.json').read_bytes()).hexdigest()
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f=ImageFont.truetype(font,24);title=ImageFont.truetype(font,37);small=ImageFont.truetype(font,18)
for side in ['top','bottom']:
 raw=Image.open(review/f'{side}-3d-raw.png').convert('RGB');canvas=Image.new('RGB',(1500,1500),'white');canvas.paste(raw,(0,80));draw=ImageDraw.Draw(canvas)
 draw.text((50,30),f'NEMA14 JST · {side} 3D engineering view',fill='#173749',font=title)
 rows=json.loads((review/f'{side}-labels.json').read_text());occupied=[]
 for row in rows:
  x,y=row['x'],row['y']+80;label=row['name'];w=draw.textlength(label,font=f)+14;lx=x-w/2;ly=y-30
  while any(abs(ly-oy)<31 and lx<ox+ow and lx+w>ox for ox,oy,ow in occupied):ly-=31
  occupied.append((lx,ly,w));draw.line((x,y,lx+w/2,ly+26),fill='#31556b',width=2);draw.rounded_rectangle((lx,ly,lx+w,ly+30),radius=4,fill='white',outline='#8fa6b2');draw.text((lx+7,ly),label,fill='#173749',font=f)
 draw.rectangle((0,1360,1500,1500),fill='white')
 lines=['Native source · 35 × 35 mm · no routed copper','Red dashed rings: Ø6.4 mm screw reserves. Cyan: catalog plug / withdrawal. Purple: assumed service allowance.' if side=='top' else 'Bottom DNP encoder copper is shown. Rear motor, magnet and selected fasteners are not modeled.','Supplier meshes and native CAD transforms. Catalog plug envelope; physical handling is unverified.','Circuit JSON SHA256: '+sha]
 for i,line in enumerate(lines):draw.text((42,1375+i*28),line,fill='#344b58',font=small)
 canvas.save(review/f'{side}-3d.png')
 (review/f'{side}-3d-raw.png').unlink();(review/f'{side}-labels.json').unlink()
print('NEMA14 JST labeled review views:',sha)
