"""Keep legal baseline conductor segments instead of discarding whole routes.

Fixed reviewed USB constructions take precedence. Changed-land stubs, foreign
contacts and the coupled-trunk reference corridors are removed for repair.
"""
import json,copy,math,pathlib,hashlib
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
import verify_supplier_connectivity as g
j=g.j;ROOT=g.ROOT;old=json.loads((ROOT/'artifacts/engineering-fixes/baseline.circuit.json').read_text());fresh=json.loads((ROOT/'artifacts/final-source.circuit.json').read_text())
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
newpads=[e for e in fresh if e['type'] in ['pcb_smtpad','pcb_plated_hole']];newpadbyport={e['pcb_port_id']:e for e in newpads};changed=[]
for p in old:
 if p['type'] not in ['pcb_smtpad','pcb_plated_hole']:continue
 q=newpadbyport[remap[p['pcb_port_id']]]
 if g.geometry(p).symmetric_difference(g.geometry(q)).area>1e-7:changed.append(p)
usb_names={'USB_DP','USB_DM','MCU_DP','MCU_DM'};netnames={k:v['name'] for k,v in nets.items()};ground=next(k for k,v in nets.items() if v['name']=='GND')
fixed=[e for e in j if e['type'] in ['pcb_trace','pcb_via'] and e.get(e['type']+'_id','').startswith(('usb_coupled_','usb_fan_','usb_escape_'))]
fx=[]
for e in fixed:
 if e['type']=='pcb_via':
  for l in e['layers']:fx.append((l,e['subcircuit_connectivity_map_key'],Point(e['x'],e['y']).buffer(e['outer_diameter']/2)))
 else:
  for a,b in zip(e['route'],e['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:fx.append((a['layer'],e['subcircuit_connectivity_map_key'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)))
policy=json.loads((ROOT/'artifacts/engineering-fixes/usb-routing-plan.json').read_text());guards=[(c['reference_layer'],LineString(c['centerline']).buffer(policy['reference_corridor_buffer_mm'])) for c in policy['cores']]
padlayers={l:[(padkey(p,npp,np),g.geometry(p)) for p in newpads if l in p.get('layers',[p.get('layer','top')])] for l in ['top','inner1','inner2','bottom']}
changedshapes=[(keys.get(padkey(p,opp,op)),p.get('layers',[p.get('layer','top')]),g.geometry(p)) for p in changed]
kept=[];removed=[]
def legal(key,layer,geometry):
 if any(k!=key and geometry.distance(s)<.149999 for k,s in padlayers[layer]):return False
 if any(l==layer and k!=key and geometry.distance(s)<.149999 for l,k,s in fx):return False
 if key!=ground and any(l==layer and geometry.intersects(s) for l,s in guards):return False
 if any(layer in ls and k==key and geometry.intersects(s) for k,ls,s in changedshapes):return False
 return True
for original in old:
 if original['type'] not in ['pcb_trace','pcb_via']:continue
 e=reid(copy.deepcopy(original));key=e['subcircuit_connectivity_map_key'];name=netnames[key]
 if name in usb_names or name in ['DIO','DCK'] and any(f.get('pcb_via_id','').startswith('usb_escape_') and f.get('subcircuit_connectivity_map_key')==key for f in fixed):continue
 if e['type']=='pcb_via':
  geom=Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
  if all(legal(key,l,geom) for l in e['layers']) and not any(geom.intersects(s) for _,s in guards):kept.append(e)
  else:removed.append(e['pcb_via_id'])
  continue
 for i,(a,b) in enumerate(zip(e['route'],e['route'][1:])):
  if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer'] or math.dist((a['x'],a['y']),(b['x'],b['y']))<1e-8:continue
  geom=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
  if not legal(key,a['layer'],geom):removed.append(e['pcb_trace_id']+'_segment_'+str(i));continue
  aa,bb=dict(a),dict(b)
  for p in [aa,bb]:
   for tag in ['start_pcb_port_id','end_pcb_port_id']:
    if tag in p and (p[tag] not in newpadbyport or not g.geometry(newpadbyport[p[tag]]).buffer(.00001).covers(Point(p['x'],p['y']))):del p[tag]
  out={**e,'pcb_trace_id':'legal_baseline_'+e['pcb_trace_id']+'_segment_'+str(i),'route':[aa,bb],'pcb_port_ids':list({p[tag] for p in [aa,bb] for tag in ['start_pcb_port_id','end_pcb_port_id'] if tag in p})};kept.append(out)
base=[{**e,'is_via_in_pad_allowed':True} if e['type']=='pcb_board' else e for e in fresh if e['type'] not in ['pcb_trace','pcb_via','pcb_copper_pour'] and not e['type'].endswith(('_error','_warning'))]
g.path.write_text(json.dumps(base+kept+fixed,indent=2)+'\n');(ROOT/'artifacts/engineering-fixes/legal-baseline-copper.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256((ROOT/'artifacts/engineering-fixes/baseline.circuit.json').read_bytes()).hexdigest(),'retained_conductor_records':len(kept),'retained_fixed_USB_records':len(fixed),'removed_segments_and_vias':removed,'requires_routing_ground_fill_and_full_validation':True},indent=2)+'\n');print('Preserved',len(kept),'baseline conductors and',len(fixed),'USB constructions; removed',len(removed),'conflicting segments/vias')
