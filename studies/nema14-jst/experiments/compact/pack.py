"""Distinct top-side anchored power cluster; no mechanical or electrical gate relaxed."""
from pathlib import Path
import json,math,sys
from ortools.sat.python import cp_model
S=1000;b=json.load(open('artifacts/final-source.circuit.json'));poses=json.load(open('src/supplier-placement.json'));sc={e['source_component_id']:e['name'] for e in b if e['type']=='source_component'};co={sc[e['source_component_id']]:e for e in b if e['type']=='pcb_component'};pcn={e['pcb_component_id']:sc[e['source_component_id']] for e in b if e['type']=='pcb_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};ports={(sc[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'}
anchors={'U_DRV': [7.6, 7.45, 90], 'R_SA': [3.4, 5.5, 90], 'R_SB': [11.8, 6.75, 270], 'R_SHUNT_A': [10.55, 2.2, 90], 'R_SHUNT_B': [7.75, 2.8, 0], 'U_IA': [14.5, 5.7, 0], 'U_IB': [5, 0.1, 90], 'C_IA': [16.85, 6.6, 270], 'C_IB': [3.9, 2.4, 0], 'C_VM': [5.375, 3.28, 270], 'C_BULK': [5.9, -6.4, 270], 'C_CP': [11.75, 9.1, 0], 'C_VCP': [8.95, 11.35, 180], 'C_VREG': [6.65, 11.375, 180], 'C_DRV_LOGIC': [1.7, 9.75, 180], 'C_IO42': [1.7, 6.9, 90], 'U_BUCK': [-12.2, -7.7, 90], 'L_BUCK': [-14.95, -3.6, 180], 'C_BUCK_IN': [-11.1, -2.6, 90], 'C_BUCK_OUT1': [-14.95, 0.1, 0], 'C_BUCK_OUT2': [-16.5, -7.925, 270]}
anchors.update({'C_DV23':[-10.1,.65,180],'R_IA':[3.2,10.15,90],'C_IADC_A':[3.2,8.25,270],'R_IB':[.3,-1.5,90],'C_IADC_B':[.15,.35,0],'R_DM':[-1.5,10.2,90],'R_DP':[-2.6,10.2,90],'C_IO42':[-.4,10.15,90]})
fixed={'J_PD','J_DATA','J_MOTOR','U_ENCODER','C_ENCODER','C_ENCODER_BULK','U_MCU','U_PD','BZ1','U_FLASH','Y_MCU','R_XOUT','C_XIN','C_XOUT','C_IO1','C_IO10','C_IO22','C_IO33','C_IO49','C_DV23','C_DV50','C_USB','C_ADC','C_VREG_IN','C_VREG_OUT','C_FLASH','U_ESD'}
fixed.discard('C_DV23')
for n in fixed:anchors[n]=[co[n]['center']['x'],co[n]['center']['y'],co[n]['rotation']]
json.dump(anchors,open('experiments/compact/anchors.json','w'),indent=2)
courts={}
for e in b:
 if e['type']=='pcb_courtyard_outline' and e.get('layer')=='top':
  n=pcn[e['pcb_component_id']];c=co[n]['center'];courts[n]=[(p['x']-c['x'],p['y']-c['y']) for p in e['outline']]
def rotate(p,t):
 a=math.radians(t);c,s=round(math.cos(a)),round(math.sin(a));return (p[0]*c-p[1]*s,p[0]*s+p[1]*c)
def bounds(n,r):
 q=[rotate(p,r-co[n]['rotation']) for p in courts[n]];return [min(p[0] for p in q),min(p[1] for p in q),max(p[0] for p in q),max(p[1] for p in q)]
# Retain additional original parts only when their true courtyards and current
# fixed-neighbor electrical constraints remain clear. This reduces search domains.
def at(n,q):
 z=bounds(n,q[2]);return [z[0]+q[0],z[1]+q[1],z[2]+q[0],z[3]+q[1]]
def pin_at(n,pin,q):
 p=ports[n,pin];c=co[n];d=rotate((p['x']-c['center']['x'],p['y']-c['center']['y']),q[2]-c['rotation']);return [q[0]+d[0],q[1]+d[1]]
local0=json.load(open('artifacts/iteration-4/locality.json'))['rows']
for n in sorted(set(courts)-set(anchors),key=lambda n:-(bounds(n,co[n]['rotation'])[2]-bounds(n,co[n]['rotation'])[0])*(bounds(n,co[n]['rotation'])[3]-bounds(n,co[n]['rotation'])[1])):
 q=[co[n]['center']['x'],co[n]['center']['y'],co[n]['rotation']];a=at(n,q)
 if any(min(a[2],at(m,p)[2])-max(a[0],at(m,p)[0])>1e-6 and min(a[3],at(m,p)[3])-max(a[1],at(m,p)[1])>1e-6 for m,p in anchors.items() if m in courts):continue
 bad=False
 for e in local0:
  if n not in [e['a'],e['b']]:continue
  other=e['b'] if n==e['a'] else e['a']
  if other not in anchors:continue
  z={n:q,other:anchors[other]};aa=pin_at(e['a'],e['pa'],z[e['a']]);bb=pin_at(e['b'],e['pb'],z[e['b']]);distance=abs(aa[0]-bb[0])+abs(aa[1]-bb[1]);limit=e['limit'] if e['pass'] else e['distance_l1_mm'] if e['weight']>=6 else 1e6
  if distance>limit+1e-6:bad=True;break
 if bad:continue
 anchors[n]=q;fixed.add(n)
print('RETAINED',len(fixed),'VARIABLE',len(set(courts)-set(anchors)),flush=True)
json.dump(anchors,open('experiments/compact/anchors.json','w'),indent=2)
# Fail before solving on any fixed overlap; the original board remains untouched.
problems=[]
for i,n in enumerate(courts):
 if n not in anchors:continue
 q=anchors[n];a=bounds(n,q[2]);a=[a[0]+q[0],a[1]+q[1],a[2]+q[0],a[3]+q[1]]
 for m in list(courts)[i+1:]:
  if m not in anchors:continue
  p=anchors[m];z=bounds(m,p[2]);z=[z[0]+p[0],z[1]+p[1],z[2]+p[0],z[3]+p[1]]
  if min(a[2],z[2])-max(a[0],z[0])>1e-5 and min(a[3],z[3])-max(a[1],z[1])>1e-5:problems.append([n,m,a,z])
if problems:Path('artifacts/iteration-5/fixed-conflicts.json').write_text(json.dumps(problems,indent=2));print('FIXED CONFLICTS',problems);sys.exit(2)
if '--anchors-only' in sys.argv:sys.exit(0)
model=cp_model.CpModel()
def absolute(target,expr):
 # Materialize differences: this solver pin mis-negates offsets in compound abs expressions.
 d=model.new_int_var(-50000,50000,'signed_difference');model.add(d==expr);model.add_abs_equality(target,d)
variables={};xx=[];yy=[];objective=[];boxes={}
for n in courts:
 if n in anchors:
  x,y,r=anchors[n];x=round(x*S);y=round(y*S);rot=r//90
 else:
  x=model.new_int_var(-17000,17000,n+'x');y=model.new_int_var(-17000,17000,n+'y');rot=model.new_int_var(0,3,n+'r');variables[n]=(x,y,rot);model.add_hint(x,round(poses[n]['pcbX']*S));model.add_hint(y,round(poses[n]['pcbY']*S));model.add_hint(rot,round(poses[n]['pcbRotation']/90)%4)
  for var,target in [(x,poses[n]['pcbX']),(y,poses[n]['pcbY'])]:
   d=model.new_int_var(0,35000,n+'move');absolute(d,var-round(target*S));objective.append(d)
 params=[]
 for turn in range(4):
  z=bounds(n,turn*90);params.append([turn,*(round(v*S) for v in z)])
 offset=[model.new_int_var(-12500,12500,n+'offset'+str(k)) for k in range(4)];model.add_allowed_assignments([rot,*offset],params)
 x0,y0,x1,y1=[model.new_int_var(-17500,17500,n+'box'+str(k)) for k in range(4)];model.add(x0==x+offset[0]);model.add(y0==y+offset[1]);model.add(x1==x+offset[2]);model.add(y1==y+offset[3]);w=model.new_int_var(1,12500,n+'w');h=model.new_int_var(1,12500,n+'h');model.add(w==x1-x0);model.add(h==y1-y0);xx.append(model.new_interval_var(x0,w,x1,n+'ix'));yy.append(model.new_interval_var(y0,h,y1,n+'iy'));boxes[n]=(x0,y0,x1,y1)
 # Tangent separation from all four real circular screw reserves; 32 directions.
 for mx in [-13*S,13*S]:
  for my in [-13*S,13*S]:
   bits=[]
   for k in range(32):
    c=round(math.cos(2*math.pi*k/32)*1000);s=round(math.sin(2*math.pi*k/32)*1000);bit=model.new_bool_var(n+'head');model.add(c*(x0 if c>=0 else x1)+s*(y0 if s>=0 else y1)>=c*mx+s*my+math.ceil(3.2*S*math.hypot(c,s))).only_enforce_if(bit);bits.append(bit)
   model.add_bool_or(bits)
 # Port coordinates for true native footprint rotation, used by locality constraints.
 for (owner,pin),p in ports.items():
  if owner!=n:continue
  dx=p['x']-co[n]['center']['x'];dy=p['y']-co[n]['center']['y'];opts=[[t,*[round(v*S) for v in rotate((dx,dy),90*t-co[n]['rotation'])]] for t in range(4)];ox=model.new_int_var(-15000,15000,n+pin+'ox');oy=model.new_int_var(-15000,15000,n+pin+'oy');model.add_allowed_assignments([rot,ox,oy],opts);ports[n,pin]={'x':x+ox,'y':y+oy}
model.add_no_overlap_2d(xx,yy)
assumptions={}
local=json.load(open('artifacts/iteration-4/locality.json'))['rows'];distances=[]
for i,e in enumerate(local):
 a,z=ports[e['a'],e['pa']],ports[e['b'],e['pb']];
 dx=model.new_int_var(0,40000,'dx'+str(i));dy=model.new_int_var(0,40000,'dy'+str(i));absolute(dx,a['x']-z['x']);absolute(dy,a['y']-z['y']);d=dx+dy
 if e['pass']:
  gate=model.new_bool_var('retain_'+str(i));model.add(d<=round(e['limit']*S)-1).only_enforce_if(gate);model.add_assumption(gate);assumptions[gate.index]=e
 elif e['weight']>=6 and not(e['a'] in fixed and e['b'] in fixed):
  gate=model.new_bool_var('nonworse_'+str(i));model.add(d<=math.floor(e['distance_l1_mm']*S)+1).only_enforce_if(gate);model.add_assumption(gate);assumptions[gate.index]=e
 success=model.new_bool_var('locality'+str(i));model.add(d<=round(e['limit']*S)-1).only_enforce_if(success);model.add(d>=round(e['limit']*S)).only_enforce_if(success.Not());objective.append((1-success)*30000*e['weight']);objective.append(d*e['weight']);distances.append(d)
model.clear_objective();solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=120;solver.parameters.num_search_workers=8;solver.parameters.log_search_progress=True
class Save(cp_model.CpSolverSolutionCallback):
 def on_solution_callback(self):
  p={n:anchors[n] for n in anchors if n not in fixed}
  for n,(x,y,r) in variables.items():p[n]=[self.value(x)/S,self.value(y)/S,self.value(r)*90]
  Path('experiments/compact/poses.json').write_text(json.dumps(p,indent=2)+'\n');print('candidate',self.objective_value,flush=True);self.stop_search()
print('VALIDATION',model.validate(),flush=True);result=solver.solve(model,Save());print('UNSAT_CORE',[str(assumptions.get(i,i)) for i in solver.sufficient_assumptions_for_infeasibility()] if result==cp_model.INFEASIBLE else [],flush=True);report={'status':solver.status_name(result),'statistics':solver.response_stats(),'constraints_require_original_passes_retained':True,'constraints_require_critical_distances_not_worse':True,'candidate_found':result in [cp_model.OPTIMAL,cp_model.FEASIBLE],'bounded_search_is_not_impossibility_proof':True,'fixed_envelope':True,'not_copper_or_manufacturing_validation':True};Path('artifacts/iteration-5/packing-result.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
