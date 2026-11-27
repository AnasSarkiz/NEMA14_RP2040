"""Bounded discrete placement around immutable native power and mechanical geometry.
Domains use exact transformed supplier courtyard bounds and screw circles; no router runs.
"""
from pathlib import Path
import json,math,sys,time
import numpy as np
from ortools.sat.python import cp_model
from model import *
from routing_geometry import resolve_copper_nets
start=time.monotonic();groups=read('artifacts/iteration-7/collision-groups.json');cluster=set(read('experiments/compact/candidate-poses.json'));mechanical={'J_PD','J_DATA','J_MOTOR','U_ENCODER','C_ENCODER','C_ENCODER_BULK'};movable=sorted({e[k] for e in groups['all_top_courtyard_conflicts'] for k in ['a','b'] if e[k] not in cluster and e[k] not in mechanical}|{'C_VM_SENSE','R_REF_L','C_REF','R_BUZZER_GATE'})
if '--wider' in sys.argv:movable=sorted(set(movable)|{'R_CC2','R_ENABLE','D_PWR','R_PWR_LED','C_TEMP','U_TEMP','Q_STATUS_R','Q_STATUS_G','D_PD','D_DATA','D_TVS','TP_SWDIO'})
fixed={n:p for n,p in courts.items() if n not in movable};assert not court_conflicts(fixed),'Fixed native courtyards conflict';print('movable',len(movable),movable,flush=True)
# Critical analog/regulation targets and net-functional neighborhoods are explicit.
targets={
 'C_BOOTSTRAP':[('U_BUCK','BST'),('U_BUCK','SW')], 'R_PD':[('U_PD','VHV')], 'R_PG':[('U_PD','PG')], 'R_PD_CFG':[('U_PD','CFG1')],
 'R_FLASH_CS':[('U_FLASH','CS')], 'R_BOOT':[('U_FLASH','CS')], 'R_RUN':[('U_MCU','RUN')], 'R_CC1':[('J_DATA','CC1')], 'R_CC2':[('J_DATA','CC2')],
 'R_USB_SENSE_H':[('U_MCU','GPIO29')], 'R_USB_SENSE_L':[('U_MCU','GPIO29')], 'R_VM_H':[('U_MCU','GPIO28')], 'R_VM_L':[('U_MCU','GPIO28')], 'C_VM_SENSE':[('U_MCU','GPIO28')],
 'R_REF_H':[('U_DRV','REF')], 'R_REF_L':[('U_DRV','REF')], 'C_REF':[('U_DRV','REF')], 'R_SLEEP':[('U_DRV','SLEEP')], 'R_ENABLE':[('U_DRV','ENABLE_N')],
 'Q_BUZZER':[('BZ1','_NEG')], 'D_BUZZER':[('BZ1','_NEG')], 'C_BUZZER':[('BZ1','_POS')], 'R_BUZZER_PD':[('BZ1','_NEG')], 'R_BUZZER_GATE':[('BZ1','_NEG')],
 'R_TEMP_SDA':[('U_TEMP','SDA')], 'R_TEMP_SCL':[('U_TEMP','SCL')], 'TP_3V3':[('U_MCU','IOVDD22')], 'TP_GND':[('U_MCU','GND')], 'TP_SWCLK':[('U_MCU','SWCLK')], 'TP_RUN':[('U_MCU','RUN')], 'TP_BOOT':[('U_MCU','QSPI_SS')],
 'D_STATUS':[('J_DATA','VBUS1')], 'R_STATUS_R':[('Q_STATUS_R','pin3')], 'R_STATUS_G':[('Q_STATUS_G','pin3')], 'R_STATUS_B':[('Q_STATUS_B','pin3')], 'Q_STATUS_B':[('U_MCU','GPIO3')]
}
# Actual immutable copper: candidates must also keep moved pads away from fixed foreign copper.
bb=resolve_copper_nets(b);fixed_copper=[]
for e in bb:
 if e['type']=='pcb_trace':
  for a,z in zip(e['route'],e['route'][1:]):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']=='top':fixed_copper.append((LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(max(a['width'],z['width'])/2,quad_segs=32),e['subcircuit_connectivity_map_key']))
 elif e['type']=='pcb_via':fixed_copper.append((g.pad_shape(e),e['subcircuit_connectivity_map_key']))
padrows={n:[] for n in movable}
for e in b:
 if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and pc.get(e['pcb_component_id']) in padrows:padrows[pc[e['pcb_component_id']]].append((g.pad_shape(e),sp[pp[e['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key')))
from shapely.strtree import STRtree
cu_tree=STRtree([p for p,key in fixed_copper])
fixed_boxes=np.array([p.bounds for p in fixed.values()]);grid=np.arange(-17.3,17.3001,.1);gx,gy=np.meshgrid(grid,grid);x=gx.ravel();y=gy.ravel();domains={};max_candidates=int(next((v.split('=')[1] for v in sys.argv if v.startswith('--candidates=')),'450'))
for n in movable:
 candidates=[]
 for rot in [poses[n][2],(poses[n][2]+90)%360,(poses[n][2]+180)%360,(poses[n][2]+270)%360]:
  z=courtyard(n,[0,0,rot]).bounds;boxes=np.stack([x+z[0],y+z[1],x+z[2],y+z[3]],axis=1);ok=(boxes[:,0]>=-17.4)&(boxes[:,1]>=-17.4)&(boxes[:,2]<=17.4)&(boxes[:,3]<=17.4)
  for a in fixed_boxes:ok &= ((boxes[:,2]<=a[0]-.015)|(boxes[:,0]>=a[2]+.015)|(boxes[:,3]<=a[1]-.015)|(boxes[:,1]>=a[3]+.015))
  for hx in [-13,13]:
   for hy in [-13,13]:
    dx=np.maximum(np.maximum(boxes[:,0]-hx,hx-boxes[:,2]),0);dy=np.maximum(np.maximum(boxes[:,1]-hy,hy-boxes[:,3]),0);ok &= dx*dx+dy*dy>=(3.205)**2
  inds=np.where(ok)[0];score=np.zeros(len(inds));ns=targets.get(n,[])
  for owner,pinname in ns:
   q=ports[owner,pinname];score += abs(x[inds]-q['x'])+abs(y[inds]-q['y'])
  if not ns:score += abs(x[inds]-poses[n][0])+abs(y[inds]-poses[n][1])
  score += .05*(abs(x[inds]-poses[n][0])+abs(y[inds]-poses[n][1]))
  if n=='C_BOOTSTRAP':
   for pn,target,limit in [('pin1','BST',3),('pin2','SW',4)]:
    px,py=pin(n,pn,[0,0,rot]);a=ports['U_BUCK',target];d=abs(x[inds]+px-a['x'])+abs(y[inds]+py-a['y']);score[d>limit-1e-5]=1e8
  for k in np.argsort(score)[:max_candidates*2]:
   if score[k]>1e7:continue
   i=inds[k];pose=[round(float(x[i]),6),round(float(y[i]),6),rot];actual=[(transform(poly,n,pose),net) for poly,net in padrows[n]]
   bad=False
   for poly,net in actual:
    a=poly.bounds
    for j in cu_tree.query(__import__('shapely').geometry.box(a[0]-.15002,a[1]-.15002,a[2]+.15002,a[3]+.15002)):
     q,key=fixed_copper[int(j)]
     if net!=key and poly.distance(q)<.15+1e-5:bad=True;break
    if bad:break
   if bad:continue
   candidates.append((score[k],pose,boxes[i]))
 candidates.sort(key=lambda v:v[0]);diverse=[];cells={}
 for z in candidates:
  cell=(math.floor(z[1][0]),math.floor(z[1][1]),z[1][2]);count=cells.get(cell,0)
  if count<8:diverse.append(z);cells[cell]=count+1
 candidates=diverse[:max_candidates];assert candidates,'No legal discrete pose for '+n;domains[n]=candidates;Path('artifacts/iteration-7/domains.json').write_text(json.dumps({k:[{'score':float(z[0]),'pose':z[1],'box':[float(q) for q in z[2]]} for z in vals] for k,vals in domains.items()}));print(n,len(candidates),'best',candidates[0][1],round(candidates[0][0],3),flush=True)
# Allowed-domain rectangles remove all fixed-obstacle and screw choices before solving.
m=cp_model.CpModel();ix=[];iy=[];vars={};costs=[]
for n,cs in domains.items():
 choice=m.new_int_var(0,len(cs)-1,n+'choice');q=[m.new_int_var(-17400,17400,n+str(i)) for i in range(4)];cost=m.new_int_var(0,1000000,n+'cost');m.add_allowed_assignments([choice,*q,cost],[[i,*[round(float(t)*1000) for t in box],round(score*100)] for i,(score,pose,box) in enumerate(cs)]);w=m.new_int_var(1,12000,n+'w');h=m.new_int_var(1,12000,n+'h');m.add(w==q[2]-q[0]);m.add(h==q[3]-q[1]);ix.append(m.new_interval_var(q[0],w,q[2],n+'ix'));iy.append(m.new_interval_var(q[1],h,q[3],n+'iy'));vars[n]=choice;costs.append(cost)
m.add_no_overlap_2d(ix,iy);m.minimize(sum(costs));solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=45;solver.parameters.num_search_workers=8
class Save(cp_model.CpSolverSolutionCallback):
 def on_solution_callback(self):
  result={n:poses[n] for n in poses};result.update({n:domains[n][self.value(v)][1] for n,v in vars.items()});Path('experiments/placement/poses.json').write_text(json.dumps(result,indent=2)+'\n');print('solution',self.objective_value,flush=True)
result=solver.solve(m,Save());report={'status':solver.status_name(result),'candidate_found':result in [cp_model.OPTIMAL,cp_model.FEASIBLE],'movable':movable,'domain_grid_mm':.1,'retained_native_cluster_and_fixed_mechanics':True,'max_domain_candidates':max_candidates,'solver_budget_seconds':45,'elapsed_seconds':time.monotonic()-start,'statistics':solver.response_stats(),'no_router_run':True,'bounded_search_not_impossibility_proof':True};Path('artifacts/iteration-7/packing-result.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
