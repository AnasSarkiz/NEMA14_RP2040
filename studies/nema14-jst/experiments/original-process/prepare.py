"""Small geometry corrections derived from real native pad anchors; no router result."""
from model import *
from routing_geometry import resolve_copper_nets
j=resolve_copper_nets(b);st={e['source_trace_id']:e for e in j if e['type']=='source_trace'};tr={st[e['source_trace_id']]['name']:e for e in j if e['type']=='pcb_trace'}
spec=read('experiments/placement/generated.json');fr={e['name']:e for e in spec['fragments']};vs={e['name']:{**e,'hole_mm':.3,'pad_mm':.55} for e in spec['vias']+read('experiments/reconnect/vias.json')};vs['V_GB'].update(x=10.83,y=7.0);vs['V_PB_D'].update(x=8.1,y=4.125);Path('experiments/original-process/vias.json').write_text(json.dumps(vs,indent=2)+'\n')
changes={}
for n in ['POWER_A_DRV__2','POWER_B_DRV__2']:
 p=[[e['x'],e['y']] for e in tr[n]['route']];p[-1][1]-=.12
 if n=='POWER_B_DRV__2':p[0][0]=vs['V_PB_D']['x'];p[0][1]=p[1][1]=vs['V_PB_D']['y']
 changes[n]=p
p=[[e['x'],e['y']] for e in tr['POWER_B_DRV__1']['route']];p[-1][1]=vs['V_PB_D']['y'];p[-1][0]=p[-2][0]=vs['V_PB_D']['x'];changes['POWER_B_DRV__1']=p
for n in ['RETURN_A_EP','RETURN_B_EP']:
 r=tr[n]['route'];start=[r[0]['x'],r[0]['y']];end=[r[-1]['x'],r[-1]['y']];d=math.dist(start,end);changes[n]=[[start[i]+.25*(end[i]-start[i])/d for i in [0,1]],end]
p=[[e['x'],e['y']] for e in tr['POWER_B_DRV__0']['route']];p[2][0]=p[3][0]=6.09;changes['POWER_B_DRV__0']=p
p=[[e['x'],e['y']] for e in tr['AUTHORED_SENSE_A']['route']];p[2][0]=6.50;changes['AUTHORED_SENSE_A']=p
for n in ['RETURN_B_TOP','RETURN_B_INNER']:
 p=[[e['x'],e['y']] for e in tr[n]['route']]
 if n=='RETURN_B_TOP':p[-1]=[vs['V_GB']['x']-.2,vs['V_GB']['y']]
 else:p[0]=[vs['V_GB']['x'],vs['V_GB']['y']]
 changes[n]=p
out=[]
for n,points in changes.items():
 f=fr[n];owner=f['anchor'][1:].split(' > .')[0];c=co.get(owner,{'center':vs[owner] if owner in vs else {'x':0,'y':0},'rotation':0});ox,oy=c['center']['x'],c['center']['y'];angle=math.radians(-c['rotation']);local=[];layer=tr[n]['route'][0]['layer']
 for x,y in points:
  dx,dy=x-ox,y-oy;local.append({'x':dx*math.cos(angle)-dy*math.sin(angle),'y':dx*math.sin(angle)+dy*math.cos(angle),'layer':layer})
 out.append({'name':n,'from':f['from'],'to':f['to'],'anchor':f['anchor'],'width_mm':f['width_mm'],'world_points_mm':points,'local_points':local})
Path('experiments/original-process/paths.json').write_text(json.dumps(out,indent=2)+'\n')
