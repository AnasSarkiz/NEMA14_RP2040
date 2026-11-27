"""Local corridor corrections; preserve the real Kelvin pickup coordinates."""
from model import *
p=read('experiments/original-process/paths.json');by={e['name']:e for e in p};spec=read('experiments/placement/generated.json');fr={e['name']:e for e in spec['fragments']};vs=read('experiments/original-process/vias.json')
by['RETURN_B_TOP']['world_points_mm'][-1]=[vs['V_GB']['x']+.2,vs['V_GB']['y']]
for n in ['POWER_A_DRV__2','POWER_B_DRV__2']:by[n]['world_points_mm'][-1][1]=4.3400059
for n,points in {'POWER_A_DRV__1':[[10.55,.1],[10.55,2.30],[8.5,2.57224576],[7.65,2.6875],[6.9,2.78919492],[6.9,4.2],[7.099747,4.2]],'POWER_B_COIL__1':[[9.4,1.7],[8.7,1.7],[8.7,-1.3],[13.25,-2.79962]]}.items():
 f=fr[n];by[n]={**f,'world_points_mm':points};p.append(by[n])
for e in p:
 owner=e['anchor'][1:].split(' > .')[0];c=co.get(owner,{'center':vs[owner] if owner in vs else {'x':0,'y':0},'rotation':0});ox,oy=c['center']['x'],c['center']['y'];angle=math.radians(-c['rotation']);layer='inner2' if e['name'] in ['POWER_A_DRV__1','POWER_B_COIL__1'] else 'inner1' if e['name']=='RETURN_B_INNER' else 'bottom' if e['name']=='POWER_B_DRV__1' else 'top';e['local_points']=[]
 for x,y in e['world_points_mm']:
  dx,dy=x-ox,y-oy;e['local_points'].append({'x':dx*math.cos(angle)-dy*math.sin(angle),'y':dx*math.sin(angle)+dy*math.cos(angle),'layer':layer})
Path('experiments/original-process/paths.json').write_text(json.dumps(p,indent=2)+'\n')
