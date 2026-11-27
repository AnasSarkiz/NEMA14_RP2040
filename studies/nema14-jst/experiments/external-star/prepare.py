"""One bounded external escape, retaining actual supplier pads and original via drills."""
from model import *
base=read('experiments/original-process/vias.json');over=read('experiments/external-star/vias.json');vs={n:{**v,**over.get(n,{})} for n,v in base.items()};Path('experiments/external-star/all-vias.json').write_text(json.dumps(vs,indent=2)+'\n');paths=[]
def port(n,p):return [ports[n,p]['x'],ports[n,p]['y']]
def add(name,src,dst,points,layer):
 owner=src[1:].split(' > .')[0];c=co.get(owner,{'center':vs.get(owner,{}),'rotation':0});a=math.radians(-c['rotation']);local=[]
 for x,y in points:
  dx,dy=x-c['center']['x'],y-c['center']['y'];local.append({'x':dx*math.cos(a)-dy*math.sin(a),'y':dx*math.sin(a)+dy*math.cos(a),'layer':layer})
 paths.append({'name':name,'from':src,'to':dst,'anchor':src,'width_mm':.6,'world_points_mm':points,'local_points':local})
for phase,gnd,outer,inside in [('A','GND18',4.36,5.84),('B','GND',10.84,9.36)]:
 g=vs['V_G'+phase];v=vs['V_STAR_'+phase];gy=ports['U_DRV',gnd]['y'];add('RETURN_'+phase+'_TOP','.R_S'+phase+' > .pin2','.V_G'+phase+' > .top',[port('R_S'+phase,'pin2'),[g['x'],g['y']]],'top');add('RETURN_'+phase+'_INNER','.V_G'+phase+' > .inner1','.V_STAR_'+phase+' > .inner1',[[g['x'],g['y']],[v['x'],v['y']]],'inner1');add('RETURN_'+phase+'_EXTERNAL','.V_STAR_'+phase+' > .top','.U_DRV > .'+gnd,[[v['x'],v['y']],[outer,gy]],'top');add('RETURN_'+phase+'_EP','.U_DRV > .'+gnd,'.U_DRV > .EP',[[inside,gy],port('U_DRV','EP')],'top')
Path('experiments/external-star/paths.json').write_text(json.dumps(paths,indent=2)+'\n')

# Remove needless layer detours in a second bounded control; source and star barrels are not counted as conducted.
direct=[]
for phase in 'AB':
 v=vs['V_STAR_'+phase];before=len(paths);add('RETURN_'+phase+'_TOP','.R_S'+phase+' > .pin2','.V_STAR_'+phase+' > .top',[port('R_S'+phase,'pin2'),[v['x'],v['y']]],'top');direct.append(paths.pop())
Path('experiments/external-star/direct-paths.json').write_text(json.dumps(direct,indent=2)+'\n')
