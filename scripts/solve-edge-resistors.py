"""Move/rotate resistors using exact native courtyards and circular screw envelopes."""
import json,math,pathlib,subprocess,itertools
from ortools.sat.python import cp_model
from shapely.geometry import Polygon,box
from shapely.affinity import rotate,translate
root=pathlib.Path(__file__).resolve().parents[1];j=json.loads((root/'artifacts/board.circuit.json').read_text());src={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'};comps={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};scale=200
out=root/'artifacts/edge-resistors';out.mkdir(exist_ok=True)
if not (out/'baseline.json').exists():(out/'baseline.json').write_text(json.dumps({'baseline_git_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'scope':'All resistors, all four board edges, top and bottom; preserve native footprints, pin roles, USB/JST, MCU, driver, mounting and outline.'},indent=2)+'\n')
courts={}
for e in j:
 if e['type']=='pcb_courtyard_outline':courts[e['pcb_component_id']]=Polygon([(q['x'],q['y']) for q in e['outline']])
 if e['type']=='pcb_courtyard_rect':
  c=e['center'];courts[e['pcb_component_id']]=rotate(box(c['x']-e['width']/2,c['y']-e['height']/2,c['x']+e['width']/2,c['y']+e['height']/2),e.get('ccw_rotation',0),origin=(c['x'],c['y']))
res={id:c for id,c in comps.items() if src[c['source_component_id']].startswith('R_')};padbounds={}
for id,c in res.items():
 ps=[e for e in j if e['type']=='pcb_smtpad' and e.get('pcb_component_id')==id];assert len(ps)==2 and all(e['shape']=='rect' and not e.get('ccw_rotation') for e in ps)
 padbounds[id]=(min(e['x']-e['width']/2 for e in ps),min(e['y']-e['height']/2 for e in ps),max(e['x']+e['width']/2 for e in ps),max(e['y']+e['height']/2 for e in ps))
for goal in [1.,.75]:
 model=cp_model.CpModel();ints={l:[[],[]] for l in ['top','bottom']};variables={};cost=[]
 for id,c in comps.items():
  assert id in courts;layer=c.get('layer','top');n=src[c['source_component_id']];cx,cy=c['center']['x'],c['center']['y']
  if id not in res:
   a,b,d,e=courts[id].bounds;xx=math.floor(a*scale);yy=math.floor(b*scale);w=math.ceil(d*scale)-xx;h=math.ceil(e*scale)-yy
   ints[layer][0].append(model.new_fixed_size_interval_var(xx,w,n+'x'));ints[layer][1].append(model.new_fixed_size_interval_var(yy,h,n+'y'));continue
  limit=8 if n=='R_REF_H' else 3
  x=model.new_int_var(math.ceil((cx-limit)*scale),math.floor((cx+limit)*scale),n+'x');y=model.new_int_var(math.ceil((cy-limit)*scale),math.floor((cy+limit)*scale),n+'y');r=model.new_bool_var(n+'rotate');opts=[]
  for ri,angle in enumerate([0,90]):
   active=r.Not() if ri==0 else r;court=rotate(courts[id],angle,origin=(cx,cy));a,b,d,e=court.bounds;pa,pb,pd,pe=rotate(box(*padbounds[id]),angle,origin=(cx,cy)).bounds;pa-=cx;pd-=cx;pb-=cy;pe-=cy
   xmin=math.ceil((-17.5+goal-pa)*scale+.01);xmax=math.floor((17.5-goal-pd)*scale-.01);ymin=math.ceil((-17.5+goal-pb)*scale+.01);ymax=math.floor((17.5-goal-pe)*scale-.01)
   model.add(x>=xmin).only_enforce_if(active);model.add(x<=xmax).only_enforce_if(active);model.add(y>=ymin).only_enforce_if(active);model.add(y<=ymax).only_enforce_if(active)
   ca=math.floor((a-cx)*scale-.001);cb=math.floor((b-cy)*scale-.001);cw=math.ceil((d-cx)*scale+.001)-ca+1;ch=math.ceil((e-cy)*scale+.001)-cb+1
   ints[layer][0].append(model.new_optional_fixed_size_interval_var(x+ca,cw,active,n+'ix'+str(ri)));ints[layer][1].append(model.new_optional_fixed_size_interval_var(y+cb,ch,active,n+'iy'+str(ri)))
   for hx,hy in itertools.product([-13,13],repeat=2):
    sides=[]
    for k in range(32):
     nx,ny=round(math.cos(k*math.tau/32)*1000),round(math.sin(k*math.tau/32)*1000);v=model.new_bool_var(n+'h'+str(ri)+str(hx)+str(hy)+str(k));sides.append(v);offset=min(nx*pa,nx*pd)+min(ny*pb,ny*pe);rhs=math.ceil((nx*hx+ny*hy+2.2*math.hypot(nx,ny)-offset)*scale+.01);model.add(nx*x+ny*y>=rhs).only_enforce_if(v)
    model.add_bool_or(sides).only_enforce_if(active)
   for hx,hy in itertools.product([-13,13],repeat=2):
    sides=[model.new_bool_var(n+'hole'+str(ri)+str(hx)+str(hy)+str(k)) for k in range(4)]
    model.add(x+math.ceil((d-cx)*scale)<=math.floor((hx-1.605)*scale)).only_enforce_if(sides[0]);model.add(x+math.floor((a-cx)*scale)>=math.ceil((hx+1.605)*scale)).only_enforce_if(sides[1]);model.add(y+math.ceil((e-cy)*scale)<=math.floor((hy-1.605)*scale)).only_enforce_if(sides[2]);model.add(y+math.floor((b-cy)*scale)>=math.ceil((hy+1.605)*scale)).only_enforce_if(sides[3]);model.add_bool_or(sides).only_enforce_if(active)
   opts.append({'angle':angle,'court':court,'pad_bounds':[pa,pb,pd,pe]})
  variables[id]=(x,y,r,opts);ox,oy=round(cx*scale),round(cy*scale);dx=model.new_int_var(0,5000,n+'dx');dy=model.new_int_var(0,5000,n+'dy');model.add_abs_equality(dx,x-ox);model.add_abs_equality(dy,y-oy);cost.extend([dx,dy,r*150]);m=model.new_bool_var(n+'m');model.add(x==ox).only_enforce_if(m.Not());model.add(y==oy).only_enforce_if(m.Not());model.add(r==0).only_enforce_if(m.Not());cost.append(m*10000);model.add_hint(x,ox);model.add_hint(y,oy);model.add_hint(r,0)
 for x,y in ints.values():model.add_no_overlap_2d(x,y)
 model.minimize(sum(cost));solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=45;solver.parameters.num_search_workers=8;status=solver.solve(model);print('Target',goal,'mm:',solver.status_name(status),flush=True)
 if status not in [cp_model.FEASIBLE,cp_model.OPTIMAL]:continue
 moves=[];newcourts={};rows=[]
 for id,c in comps.items():
  x,y=c['center']['x'],c['center']['y'];xx,yy=(solver.value(variables[id][0])/scale,solver.value(variables[id][1])/scale) if id in variables else (x,y);angle=variables[id][3][solver.value(variables[id][2])]['angle'] if id in variables else 0
  newcourts[id]=translate(rotate(courts[id],angle,origin=(x,y)),xoff=xx-x,yoff=yy-y)
  if id not in res:continue
  a,b,d,e=padbounds[id];oldclear=min(17.5+a,17.5+b,17.5-d,17.5-e);pa,pb,pd,pe=variables[id][3][solver.value(variables[id][2])]['pad_bounds'];clear=min(17.5+pa+xx,17.5+pb+yy,17.5-pd-xx,17.5-pe-yy);moved=abs(xx-x)+abs(yy-y)>.006 or angle!=0
  if moved:moves.append({'reference':src[c['source_component_id']],'pcb_component_id':id,'layer':c.get('layer','top'),'old_center':{'x':x,'y':y},'new_center':{'x':xx,'y':yy},'old_rotation':c.get('rotation',0),'rotation':(c.get('rotation',0)+angle)%360,'angle_delta':angle,'old_min_pad_edge_mm':oldclear,'new_min_pad_edge_mm':clear})
  rows.append({'reference':src[c['source_component_id']],'layer':c.get('layer','top'),'old_min_pad_edge_mm':oldclear,'new_min_pad_edge_mm':clear,'moved':moved})
 overlaps=[(src[comps[a]['source_component_id']],src[comps[b]['source_component_id']]) for a,b in itertools.combinations(comps,2) if comps[a].get('layer','top')==comps[b].get('layer','top') and newcourts[a].intersection(newcourts[b]).area>1e-6];assert not overlaps,overlaps
 report={'target_minimum_pad_edge_mm':goal,'solver_status':solver.status_name(status),'resistors_checked':len(res),'scope':'All four edges, both assembly sides','native_courtyard_overlaps':overlaps,'moves':moves,'all_resistors':rows,'minimum_after_mm':min(r['new_min_pad_edge_mm'] for r in rows),'requires_copper_and_STEP_validation':True}
 (out/'placement-plan.json').write_text(json.dumps(report,indent=2)+'\n');print('Planned',len(moves),'resistor moves; min clearance',report['minimum_after_mm'],flush=True);break
else:raise RuntimeError('No native-courtyard placement solution; no PCB files changed')
