"""Draw the current hash-bound nominal mechanical screen, including its limits."""
import hashlib,json,pathlib,sys
import cairosvg
root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]
m=json.loads((root/'artifacts/mechanical/mount-usb-screen.json').read_text())
assert m['passed'] and m['board_sha256']==hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest()
items=[];xy=lambda x,y:(425+20*x,520-20*y)
def rect(a,b,c,d,fill,stroke,dash=''):
 x,y=xy(a,d);items.append(f'<rect x="{x}" y="{y}" width="{(c-a)*20}" height="{(d-b)*20}" fill="{fill}" stroke="{stroke}" stroke-width="2" {dash}/>')
def text(x,y,s,size=17):
 a,b=xy(x,y);items.append(f'<text x="{a}" y="{b}" text-anchor="middle" font-size="{size}" fill="#17324d">{s}</text>')
rect(-17.5,-17.5,17.5,17.5,'#edf6ef','#245943')
for x,y in m['mounts']:
 a,b=xy(x,y)
 for r,fill,stroke,dash in [(3.2,'none','#d18a00','stroke-dasharray="5 4"'),(3,'#dbe3ea','#3b536a',''),(1.6,'white','#17324d','')]:
  items.append(f'<circle cx="{a}" cy="{b}" r="{r*20}" fill="{fill}" stroke="{stroke}" stroke-width="2" {dash}/>')
for u in m['usb']:
 a,b,_,c,d,_=u['bbox_mm'];rect(a,b,c,d,'#bac4cf','#334a62')
 x,y,_=u['mouth_xyz_mm'];rect(x-5,y-3.5,x+5,y+3.5,'none','#2877af','stroke-dasharray="6 4"')
 text(x,19 if y>0 else -20,u['reference'].replace('J_','')+' ↑ +Z',16)
text(0,24,'Opposite-edge upright USB-C · nominal mechanical screen',23)
text(0,22,f"10 mm housing width · {m['minimum_simultaneous_plug_gap_mm']:.3f} mm pair gap",18)
text(0,5,'35 × 35 mm PCB · no extension',21)
text(0,3.4,'Four Ø3.2 mm holes at (±13, ±13)',18)
text(0,1.8,'Heads ≤Ø6 × 3 mm; dashed Ø6.4 mm tolerance envelope',16)
text(0,0,f"Minimum USB body-to-head envelope gap: {min(u['native_body_to_mount_envelope_mm'] for u in m['usb']):.3f} mm",16)
text(0,-2,'USB bodies: conservative bounds of the native STEP models',15)
text(0,-4,'Blue dashed housings: defined 10 × 7 × 30 mm bounds',15)
z=min(u['mouth_xyz_mm'][2] for u in m['usb'])-.5
text(0,-6,f'Housings begin at z={z:.2f} mm; head screen ends at z=3.80 mm',15)
text(0,-8,'Nominal 3D screen passes; physical assemblies remain untested',15)
text(0,-10,'Factory assembly TOP; encoder + two caps BOTTOM DNP',15)
text(0,-11.5,'Ø6 mm vertical tool path clear with both defined plugs fitted',14)
text(0,-22,'Rear mounting, shaft/magnet and complete tolerance stack remain unverified',14)
svg='<svg xmlns="http://www.w3.org/2000/svg" width="850" height="1030" viewBox="0 0 850 1030"><rect width="850" height="1030" fill="white"/><g font-family="Arial,sans-serif">'+''.join(items)+'</g></svg>'
out=root/'artifacts/mechanical/opposite-edge-fit.svg';out.write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(out.with_suffix('.png')),output_width=1275,output_height=1470)
print(out.with_suffix('.png'))
