"""Restore compact qualified power loops; remove conflicting ordinary copper for rework."""
"""Keep legal baseline conductor segments instead of discarding whole routes.

Fixed reviewed USB constructions take precedence. Changed-land stubs, foreign
contacts and the coupled-trunk reference corridors are removed for repair.
"""
import json,copy,math,pathlib,hashlib
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
j=g.j;ROOT=g.ROOT;old=json.loads((ROOT/'artifacts/upright-revision/baseline-board.circuit.json').read_text());fresh=json.loads((ROOT/'artifacts/final-source.circuit.json').read_text())
def idx(a,t):return {e[t+'_id']:e for e in a if e['type']==t}
os,ns=idx(old,'source_component'),idx(fresh,'source_component');op,np=idx(old,'source_port'),idx(fresh,'source_port');opp,npp=idx(old,'pcb_port'),idx(fresh,'pcb_port');oldpc,newpc=idx(old,'pcb_component'),idx(fresh,'pcb_component')
def semantic(p,s):return s[p['source_component_id']]['name'],p['name']
newroles={semantic(p,ns):p for p in np.values()};remap={};keys={}
for id,p in op.items():
 q=newroles[semantic(p,os)];remap[id]=q['source_port_id'];a,b=p.get('subcircuit_connectivity_map_key'),q.get('subcircuit_connectivity_map_key')
 if a:keys[a]=b
remap.update(keys);newpports={p['source_port_id']:p for p in npp.values()}
for id,p in opp.items():remap[id]=newpports[remap[p['source_port_id']]]['pcb_port_id']
nets={e['subcircuit_connectivity_map_key']:e for e in fresh if e['type']=='source_net'}
for e in old:
 if e['type']=='source_net':remap[e['source_net_id']]=nets[keys[e['subcircuit_connectivity_map_key']]]['source_net_id']
for e in old:
 if e['type']=='source_trace':
  mapped={remap[p] for p in e['connected_source_port_ids']};choices=[q for q in fresh if q['type']=='source_trace' and q.get('subcircuit_connectivity_map_key')==keys[e['subcircuit_connectivity_map_key']]];remap[e['source_trace_id']]=max(choices,key=lambda q:len(mapped.intersection(q['connected_source_port_ids'])))['source_trace_id']
def reid(v):
 if isinstance(v,str):return remap.get(v,v)
 if isinstance(v,list):return [reid(x) for x in v]
 if isinstance(v,dict):return {k:reid(x) for k,x in v.items()}
 return v
def padkey(p,pps,sps):return sps[pps[p['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key')

critical_names={'BUCK_SW','BUCK_BST','CP1','CP2','VCP','VREG','VREF','SENSE2','B_PLUS'}
names={e['subcircuit_connectivity_map_key']:e['name'] for e in fresh if e['type']=='source_net'};critical={k for k,n in names.items() if n in critical_names};pads=[e for e in fresh if e['type'] in ['pcb_smtpad','pcb_plated_hole']]
fixed=[];skipped=[]
for original in old:
 if original['type'] not in ['pcb_trace','pcb_via']:continue
 e=reid(copy.deepcopy(original));key=e['subcircuit_connectivity_map_key']
 if key not in critical:continue
 if e['type']=='pcb_via':
  e['outer_diameter']=max(.45,e['outer_diameter']);e['hole_diameter']=max(.3,e['hole_diameter']);geoms=[(l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in e['layers']]
 else:geoms=[(a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']]
 if any(l in p.get('layers',[p.get('layer','top')]) and padkey(p,npp,np)!=key and geom.distance(g.geometry(p))<.153 for l,geom in geoms for p in pads):skipped.append(e.get(e['type']+'_id'));continue
 e[e['type']+'_id']='reviewed_local_critical_'+e[e['type']+'_id'];fixed.append(e)
fx=[]
for e in fixed:
 key=g.key(e)
 if e['type']=='pcb_via':fx.extend((l,key,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in e['layers'])
 else:fx.extend((a['layer'],key,LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'])
kept=[];ripped=[]
for e in j:
 typ=e['type'];key=g.key(e)
 if typ=='pcb_copper_pour':continue
 if typ not in ['pcb_trace','pcb_via']:kept.append(e);continue
 if key in critical:continue
 geoms=[(l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in e['layers']] if typ=='pcb_via' else [(a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)) for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']]
 hit=any(l==fl and fk!=key and geom.distance(shape)<.153 for l,geom in geoms for fl,fk,shape in fx)
 if hit:
  assert not e.get(typ+'_id','').startswith(('usb_','oscillator_')), 'Critical power intersects a fixed oscillator/USB construction'
  ripped.append(e[typ+'_id'])
 else:kept.append(e)
g.path.write_text(json.dumps(kept+fixed,indent=2)+'\n');(ROOT/'artifacts/upright-revision/critical-power-restoration.json').write_text(json.dumps({'construction_not_qualification':True,'baseline_critical_records_restored':len(fixed),'baseline_records_requiring_local_rework':skipped,'foreign_copper_removed_for_rework':ripped},indent=2)+'\n');print('Restored',len(fixed),'compact baseline power records; omitted',len(skipped),'changed-pad conflicts; reroute',len(ripped),'foreign records')
