"""Bounded two-cap placement screen. Uses real footprints/courtyards and preserved copper; no autorouting."""
from model import *
from shapely.ops import unary_union
from shapely import intersects_xy,prepare
import numpy as np
pads={e['pcb_port_id']:e for e in b if e['type']=='pcb_smtpad'};drv=g.pad_shape(pads[ports['U_DRV','VREG']['pcb_port_id']]);vcp=ports['U_DRV','VCP'];bounds=box(-17.5,-17.5,17.5,17.5);mounts=[Point(x,y).buffer(3.2,quad_segs=128) for x in [-13,13] for y in [-13,13]];others={n:p for n,p in courts.items() if n not in ['C_VREG','C_VCP']};fixed=unary_union(list(others.values())+mounts)
def choices(name,xs,ys):
 out=[]
 for rot in [0,90,180,270]:
  for x in xs:
   for y in ys:
    pose=[round(float(x),5),round(float(y),5),rot];ct=transform(courts[name],name,pose)
    if not bounds.covers(ct) or ct.intersection(fixed).area>1e-8:continue
    pad=transform(g.pad_shape(pads[ports[name,'pin1']['pcb_port_id']]),name,pose);p=pin(name,'pin1',pose)
    gap=pad.distance(drv) if name=='C_VREG' else abs(p[0]-vcp['x'])+abs(p[1]-vcp['y'])
    if (gap>1.16 if name=='C_VREG' else gap>4):continue
    out.append({'pose':pose,'gap_mm':gap,'move_mm':math.dist(pose[:2],[co[name]['center']['x'],co[name]['center']['y']]),'court':ct,'positive_pin':p})
 return out
reg=choices('C_VREG',np.arange(5.5,12.801,.05),np.arange(8.8,13.001,.05));cp=choices('C_VCP',np.arange(6.5,14.501,.05),np.arange(5.5,13.001,.05));pairs=[]
for a in reg:
 for z in cp:
  if a['court'].intersection(z['court']).area>1e-8:continue
  pairs.append({'C_VREG':{k:v for k,v in a.items() if k!='court'},'C_VCP':{k:v for k,v in z.items() if k!='court'},'total_move_mm':a['move_mm']+z['move_mm']})
pairs.sort(key=lambda e:e['total_move_mm']);out={'search_step_mm':.05,'orthogonal_rotations':[0,90,180,270],'C_VREG_local_choices':len(reg),'C_VCP_local_choices':len(cp),'pair_count':len(pairs),'pairs':pairs[:30],'independent_checks':'Courtyard intersections, circle screw reserves, real board boundary and pad gap/L1 placement bounds only; no routed copper acceptance'};Path('artifacts/iteration-11/two-cap-search.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
