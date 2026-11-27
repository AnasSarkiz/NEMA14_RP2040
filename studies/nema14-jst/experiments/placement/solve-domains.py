"""Resolve cached legal domains with explicit locality preservation and rounded-box safety."""
from pathlib import Path
import json,math,time
from ortools.sat.python import cp_model
from model import *
start=time.monotonic();domains=read('artifacts/iteration-7/domains.json');m=cp_model.CpModel();ix=[];iy=[];choices={};costs=[];pinvars={}
for n,cs in domains.items():
 choice=m.new_int_var(0,len(cs)-1,n+'choice');q=[m.new_int_var(-18000,18000,n+str(i)) for i in range(4)];cost=m.new_int_var(0,1000000,n+'cost');rows=[]
 for i,row in enumerate(cs):
  box=row['box'];rows.append([i,math.floor(box[0]*1000)-8,math.floor(box[1]*1000)-8,math.ceil(box[2]*1000)+8,math.ceil(box[3]*1000)+8,round(row['score']*100)])
 m.add_allowed_assignments([choice,*q,cost],rows);w=m.new_int_var(1,15000,n+'w');h=m.new_int_var(1,15000,n+'h');m.add(w==q[2]-q[0]);m.add(h==q[3]-q[1]);ix.append(m.new_interval_var(q[0],w,q[2],n+'ix'));iy.append(m.new_interval_var(q[1],h,q[3],n+'iy'));choices[n]=choice;costs.append(cost)
m.add_no_overlap_2d(ix,iy)
def actual_pin(n,pn):
 if (n,pn) in pinvars:return pinvars[n,pn]
 if n not in choices:return [round(v*1000) for v in pin(n,pn,poses[n])]
 values=[pin(n,pn,row['pose']) for row in domains[n]];xy=[]
 for axis in range(2):
  q=m.new_int_var(-25000,25000,n+pn+str(axis));m.add_element(choices[n],[round(v[axis]*1000) for v in values],q);xy.append(q)
 pinvars[n,pn]=xy;return xy
retained=[]
for e in read('artifacts/iteration-6/current-locality.json')['rows']:
 if not e['pass'] or not (e['a'] in choices or e['b'] in choices):continue
 a=actual_pin(e['a'],e['pa']);z=actual_pin(e['b'],e['pb']);ds=[]
 for axis in range(2):
  signed=m.new_int_var(-50000,50000,'delta');m.add(signed==a[axis]-z[axis]);absolute=m.new_int_var(0,50000,'abs');m.add_abs_equality(absolute,signed);ds.append(absolute)
 m.add(sum(ds)<=round(e['limit']*1000)-5);retained.append(e)
m.minimize(sum(costs));solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=45;solver.parameters.num_search_workers=8
class Save(cp_model.CpSolverSolutionCallback):
 def on_solution_callback(self):
  result={n:poses[n] for n in poses};result.update({n:domains[n][self.value(v)]['pose'] for n,v in choices.items()});Path('experiments/placement/poses.json').write_text(json.dumps(result,indent=2)+'\n');print('solution',self.objective_value,flush=True)
result=solver.solve(m,Save());r={'status':solver.status_name(result),'candidate_found':result in [cp_model.FEASIBLE,cp_model.OPTIMAL],'solver_seconds':solver.wall_time,'courtyard_rounding_margin_each_side_mm':.008,'mandatory_previous_pass_constraints':retained,'statistics':solver.response_stats(),'native_router_runs':0};Path('artifacts/iteration-7/refined-packing-result.json').write_text(json.dumps(r,indent=2)+'\n');print(r,flush=True)
