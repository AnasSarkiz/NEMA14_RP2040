"""Full placement, physical pickup, drilled barrel, CP2 and local loop qualification."""
from pathlib import Path
import json,sys,math,importlib.util,hashlib,copy
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
s=importlib.util.spec_from_file_location('v','experiments/anchored/verify-current.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);v.spec=read('experiments/placement/generated.json')
p=Path(sys.argv[1]);j=resolve_copper_nets(read(p));critical,cu=v.verify(p);_,cs,_,sps,pps,ps,courts=index(j);pads={e['pcb_port_id']:e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole']};st={e['source_trace_id']:e for e in j if e['type']=='source_trace'};groups={st[t['source_trace_id']].get('name',''):t for t in j if t['type']=='pcb_trace'};vias=[e for e in j if e['type']=='pcb_via'];holes=unary_union([g.pad_shape(e,True) for e in j if e['type'] in ['pcb_via','pcb_plated_hole','pcb_hole']])
def port(ref):
 owner,pin=ref.split('.');hits=[e for (n,k),e in ps.items() if n==owner and pin in sps[e['source_port_id']].get('port_hints',[k])];assert len(hits)==1,ref;return hits[0]
def connected(names,refs,missing=None):
 rec=[]
 for name in names:
  t=groups[name]
  for a,z in zip(t['route'],t['route'][1:]):
   poly=LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(min(a['width'],z['width'])/2,quad_segs=128).difference(holes)
   for part in list(poly.geoms) if hasattr(poly,'geoms') else [poly]:
    if part.area>1e-10:rec.append((part,[a['layer']],None))
 for ref in refs:
  pp=port(ref);e=pads[pp['pcb_port_id']];poly=g.pad_shape(e).difference(holes)
  for part in list(poly.geoms) if hasattr(poly,'geoms') else [poly]:rec.append((part,e.get('layers',[e.get('layer','top')]),ref))
 if len(names)==3:
  for spec in read('experiments/reconnect/vias.json'):
   if spec['name']==missing:continue
   e=next(e for e in vias if math.dist([e['x'],e['y']],[spec['x'],spec['y']])<1e-9);rec.append((g.pad_shape(e).difference(g.pad_shape(e,True)),e['layers'],None))
 parent=list(range(len(rec)))
 def find(i):
  while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,(a,ls,_) in enumerate(rec):
  for k,(z,other,_) in enumerate(rec[:i]):
   if set(ls)&set(other) and a.intersection(z).area>1e-10:parent[find(k)]=find(i)
 return bool(set.intersection(*[{find(i) for i,e in enumerate(rec) if e[2]==ref} for ref in refs]))
branches=[]
for names,refs in [(['AUTHORED_CP1_CORRIDOR'],['U_DRV.CP1','C_CP.pin1']),(['AUTHORED_CP2_CORRIDOR'],['U_DRV.CP2','C_CP.pin2']),(['BUZ_FLYBACK_SINK'],['BZ1._NEG','D_BUZZER.anode']),(['BUZ_FLYBACK_SUPPLY'],['D_BUZZER.cathode','BZ1._POS']),(['BUZ_SWITCH_SUPPLY__0','BUZ_SWITCH_SUPPLY__1','BUZ_SWITCH_SUPPLY__2'],['C_BUZZER.pin1','BZ1._POS']),(['BUZ_SWITCH_DRAIN'],['BZ1._NEG','Q_BUZZER.D']),(['BUZ_SWITCH_RETURN'],['Q_BUZZER.S','C_BUZZER.pin2']),(['BUZ_GATE_SERIES'],['R_BUZZER_GATE.pin2','Q_BUZZER.G']),(['BUZ_GATE_PULLDOWN'],['R_BUZZER_PD.pin1','Q_BUZZER.G'])]:
 assert connected(names,refs),refs
 failures=[]
 if len(names)==3:
  for spec in read('experiments/reconnect/vias.json'):assert not connected(names,refs,spec['name']);failures.append(spec['name'])
 branches.append({'fragments':names,'terminals':refs,'drilled_copper_continuity':True,'missing_barrels_rejected':failures})
ep=g.pad_shape(pads[ps['U_DRV','EP']['pcb_port_id']]);cp=[]
for name in ['AUTHORED_CP1_CORRIDOR','AUTHORED_CP2_CORRIDOR']:
 t=groups[name];poly=unary_union([LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(a['width']/2,quad_segs=128) for a,z in zip(t['route'],t['route'][1:])]);square=box(9.8,9.8,16.2,16.2);circle=Point(13,13).buffer(3.2,quad_segs=128);cp.append({'path':name,'actual_EP_gap_mm':poly.distance(ep),'native_square_gap_mm':poly.distance(square),'actual_screw_circle_gap_mm':poly.distance(circle),'actual_width_mm':.16,'maximum_centerline_y_mm':max(a['y'] for a in t['route'])});assert all(cp[-1][k]>=.15-1e-6 for k in ['actual_EP_gap_mm','native_square_gap_mm','actual_screw_circle_gap_mm'])
old=read('artifacts/iteration-7/locality.json');new=read('artifacts/iteration-8/locality.json');key=lambda x:tuple(x[k] for k in ['a','pa','b','pb']);o={key(x):x for x in old['rows']};lost=[x for x in new['rows'] if o[key(x)]['pass'] and not x['pass']];assert not lost
critical.update({'local_branch_continuity':branches,'CP_corridors':cp,'locality':{'previous_pass':sum(x['pass'] for x in old['rows']),'candidate_pass':sum(x['pass'] for x in new['rows']),'total':len(new['rows']),'regressed_previous_passes':lost},'minimum_top_courtyard_screw_gap_mm':min(poly.distance(Point(x,y))-3.2 for poly in courts.values() for x in [-13,13] for y in [-13,13])})
Path(sys.argv[2]).write_text(json.dumps(critical,indent=2)+'\n');print(json.dumps({k:critical[k] for k in ['independent','locality','CP_corridors','actual_ground_returns','minimum_top_courtyard_screw_gap_mm']},indent=2))
