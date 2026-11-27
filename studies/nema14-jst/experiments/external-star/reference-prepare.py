"""Transcribe the official page19 reference dimensions; isolated fixture, never a production replacement."""
from model import *
from shapely import affinity
pads=[e for e in b if e['type']=='pcb_smtpad' and e['pcb_component_id']==co['U_DRV']['pcb_component_id']];ref=[]
for e in pads:
 num=int(e['port_hints'][0].replace('pin',''));p=affinity.rotate(Point(e['x'],e['y']),-co['U_DRV']['rotation'],origin=(co['U_DRV']['center']['x'],co['U_DRV']['center']['y']));x,y=p.x-co['U_DRV']['center']['x'],p.y-co['U_DRV']['center']['y']
 if num==29:ref.append({'pin':num,'x':0,'y':0,'width':3.15,'height':3.15})
 elif abs(x)>abs(y):ref.append({'pin':num,'x':math.copysign(2.4,x),'y':round(y/.5)*.5,'width':1.15,'height':.3})
 else:ref.append({'pin':num,'x':round(x/.5)*.5,'y':math.copysign(2.4,y),'width':.3,'height':1.15})
Path('experiments/external-star/reference-pads.json').write_text(json.dumps(sorted(ref,key=lambda e:e['pin']),indent=2)+'\n')
