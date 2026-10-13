import json,math,pathlib,itertools,sys
from ortools.sat.python import cp_model
from shapely.geometry import Polygon,box,Point
from shapely.affinity import rotate,translate
root=pathlib.Path(sys.argv[1]);j=json.loads((root/'artifacts/top-assembly/raw-source.circuit.json').read_text());src={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'};comps={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};scale=1000
courts={}
for e in j:
 if e['type']=='pcb_courtyard_outline':courts[e['pcb_component_id']]=Polygon([(q['x'],q['y']) for q in e['outline']])
 if e['type']=='pcb_courtyard_rect':
  c=e['center'];courts[e['pcb_component_id']]=rotate(box(c['x']-e['width']/2,c['y']-e['height']/2,c['x']+e['width']/2,c['y']+e['height']/2),e.get('ccw_rotation',0),origin=(c['x'],c['y']))
for id,c in comps.items():
 if id not in courts:
  assert src[c['source_component_id']].startswith('TP_'),src[c['source_component_id']]
  x,y=c['center']['x'],c['center']['y'];courts[id]=box(x-.7,y-.7,x+.7,y+.7)
model=cp_model.CpModel();ix=[];iy=[];variables={};cost=[]
placements=json.loads((root/'src/supplier-placement.json').read_text())
priority=set(['C_IO49','C_DV50','R_XOUT','C_XOUT','R_TEMP_SDA','Y_MCU','J_MOTOR'])
for id,c in comps.items():
 n=src[c['source_component_id']];cx,cy=c['center']['x'],c['center']['y'];a,b,d,e=courts[id].bounds
 movable=n.startswith(('R_','C_','TP_')) or n in ['Y_MCU','J_MOTOR']
 if not movable:
  x0=math.floor(a*scale);y0=math.floor(b*scale);ix.append(model.new_fixed_size_interval_var(x0,math.ceil(d*scale)-x0,n+'x'));iy.append(model.new_fixed_size_interval_var(y0,math.ceil(e*scale)-y0,n+'y'));continue
 limit=12 if n.startswith('TP_') else 4 if n in priority else 2
 x=model.new_int_var(round((cx-limit)*scale),round((cx+limit)*scale),n+'x');y=model.new_int_var(round((cy-limit)*scale),round((cy+limit)*scale),n+'y');r=model.new_bool_var(n+'rot')
 physical=[p for p in j if p['type'] in ['pcb_smtpad','pcb_plated_hole'] and p.get('pcb_component_id')==id]
 padgeoms=[]
 for p in physical:
  px,py=p['x'],p['y'];w=p.get('width',p.get('radius',.55)*2);h=p.get('height',p.get('radius',.55)*2);padgeoms.append(box(px-w/2,py-h/2,px+w/2,py+h/2))
 from shapely.ops import unary_union
 pads=unary_union(padgeoms)
 for ri,angle in enumerate([0,90] if n!='J_MOTOR' else [0]):
  active=r.Not() if ri==0 else r
  if n=='J_MOTOR':model.add(r==0)
  court=rotate(courts[id],angle,origin=(cx,cy));a,b,d,e=court.bounds;pa,pb,pd,pe=rotate(pads,angle,origin=(cx,cy)).bounds;pa-=cx;pd-=cx;pb-=cy;pe-=cy
  margin=.75 if n.startswith('R_') else .25
  for v,lo,hi in [(x,-17.5+margin-pa,17.5-margin-pd),(y,-17.5+margin-pb,17.5-margin-pe)]:model.add(v>=math.ceil(lo*scale)).only_enforce_if(active);model.add(v<=math.floor(hi*scale)).only_enforce_if(active)
  ca=math.floor((a-cx)*scale-.001);cb=math.floor((b-cy)*scale-.001);cw=math.ceil((d-cx)*scale+.001)-ca+1;ch=math.ceil((e-cy)*scale+.001)-cb+1
  ix.append(model.new_optional_fixed_size_interval_var(x+ca,cw,active,n+'ix'+str(ri)));iy.append(model.new_optional_fixed_size_interval_var(y+cb,ch,active,n+'iy'+str(ri)))
  for hx,hy in itertools.product([-13,13],repeat=2):
   sides=[]
   for k in range(16):
    nx,ny=round(math.cos(k*math.tau/16)*1000),round(math.sin(k*math.tau/16)*1000);v=model.new_bool_var(n+'h'+str(ri)+str(hx)+str(hy)+str(k));sides.append(v);offset=min(nx*pa,nx*pd)+min(ny*pb,ny*pe);rhs=math.ceil((nx*hx+ny*hy+2.2*math.hypot(nx,ny)-offset)*scale+.01);model.add(nx*x+ny*y>=rhs).only_enforce_if(v)
   model.add_bool_or(sides).only_enforce_if(active)
 variables[id]=(x,y,r)
 ox,oy=round(cx*scale),round(cy*scale);dx=model.new_int_var(0,10000,n+'dx');dy=model.new_int_var(0,10000,n+'dy');model.add_abs_equality(dx,x-ox);model.add_abs_equality(dy,y-oy)
 weight=1 if n in priority or n.startswith('TP_') else 5
 cost.extend([dx*weight,dy*weight,r*100*weight]);m=model.new_bool_var(n+'m');model.add(x==ox).only_enforce_if(m.Not());model.add(y==oy).only_enforce_if(m.Not());model.add(r==0).only_enforce_if(m.Not());cost.append(m*(200 if weight==1 else 10000));model.add_hint(x,ox);model.add_hint(y,oy);model.add_hint(r,0)
model.add_no_overlap_2d(ix,iy);model.minimize(sum(cost));solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=55;solver.parameters.num_search_workers=8;status=solver.solve(model);print(root.name,solver.status_name(status),flush=True)
if status not in [cp_model.FEASIBLE,cp_model.OPTIMAL]:sys.exit(1)
moves=[]
for id,(x,y,r) in variables.items():
 c=comps[id];n=src[c['source_component_id']];xx,yy=solver.value(x)/scale,solver.value(y)/scale;angle=90*solver.value(r);dx,dy=xx-c['center']['x'],yy-c['center']['y']
 if abs(dx)+abs(dy)<.0015 and angle==0:continue
 p=placements[n];p['pcbX']+=dx;p['pcbY']+=dy;p['pcbRotation']=(p.get('pcbRotation',0)+angle)%360
 moves.append({'reference':n,'old_center':c['center'],'new_center':{'x':xx,'y':yy},'angle_delta':angle})
(root/'artifacts/top-assembly/placement-plan.json').write_text(json.dumps({'status':solver.status_name(status),'moves':moves,'independent_copper_and_STEP_checks_required':True},indent=2)+'\n');(root/'src/supplier-placement.json').write_text(json.dumps(placements,indent=2)+'\n');print(json.dumps(moves),flush=True)
