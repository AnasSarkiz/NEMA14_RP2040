"""Verify outer power trace strips against independently parsed exported CAM bytes."""
import pathlib,json,hashlib,math
from shapely.geometry import LineString,Polygon
from shapely.ops import unary_union
import importlib.util
root=pathlib.Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('cam_audit',root/'scripts/audit-manufacturing.py');cam=importlib.util.module_from_spec(spec);spec.loader.exec_module(cam)
source=root/'artifacts/board.circuit.json';j=json.loads(source.read_text());policy=json.loads((root/'artifacts/validation/service-outer-power-policy.json').read_text());audit=json.loads((root/'artifacts/manufacturing/audit.json').read_text());archive=root/'artifacts/nema14-gerbers.zip'
assert policy['checksPassed'] and policy['sha256']==sha(source),'Current native outer-power policy required'
assert audit['status']=='PASS' and audit['source_sha256']==sha(source),'Current actual CAM connectivity/clearance required'
assert audit['archive']['sha256']==sha(archive),'Current audited CAM archive required'
directory=root/'artifacts/manufacturing';files={};cu={}
for layer,name in [('top','F_Cu.gbr'),('bottom','B_Cu.gbr')]:
 p=directory/name;cu[layer]=cam.gerber(p)[0];files[name]=sha(p)
holes=[]
for p in directory.glob('*.drl'):
 holes.append(cam.drill(p)[0]);files[p.name]=sha(p)
cut=unary_union(holes);cu={k:v.difference(cut)for k,v in cu.items()}
# Cache the fixed rounding envelope once; do not buffer the whole board per strip.
coverage={k:v.buffer(.0002)for k,v in cu.items()}
from shapely.prepared import prep
prepared_coverage={k:prep(v)for k,v in coverage.items()}
traces={e['pcb_trace_id']:e for e in j if e['type']=='pcb_trace'};errors=[];rows=[]
for row in policy['traces']:
 t=traces[row['trace']];segments=[]
 for a,b in zip(t['route'],t['route'][1:]):
  if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
  width=min(a['width'],b['width']);line=LineString([(a['x'],a['y']),(b['x'],b['y'])]);expected=line.buffer(width/2,quad_segs=64).difference(cut)
  assert a['layer']in cu,'Power wire on forbidden layer'
  missing=0. if prepared_coverage[a['layer']].covers(expected)else expected.difference(coverage[a['layer']]).area
  if missing>1e-6:errors.append({'trace':t['pcb_trace_id'],'layer':a['layer'],'missing_strip_mm2':missing})
  segments.append({'layer':a['layer'],'widthMm':width,'lengthMm':line.length,'missingStripMm2':missing})
 rows.append({'trace':t['pcb_trace_id'],'net':row['net'],'boundedNativeOrLeafException':row['exception'],'segments':segments})
# Count actual available layer changes separately from all branched barrels.
# Copper islands are vertices; independently parsed PLATED drills alone bridge
# layers. Entering a via barrel costs one, native component plated pins cost zero.
from shapely.strtree import STRtree
import heapq,collections
allcu={};plated=[]
for layer,name in [('top','F_Cu.gbr'),('inner1','In1_Cu.gbr'),('inner2','In2_Cu.gbr'),('bottom','B_Cu.gbr')]:
 p=directory/name
 if p.exists():allcu[layer]=cu[layer]if layer in cu else cam.gerber(p)[0].difference(cut);files[name]=sha(p)
for p in directory.glob('*.drl'):
 if 'npth'not in p.name:plated.extend(cam.drill(p)[1])
nodes=[];trees={};indices={};adj=collections.defaultdict(list)
for l,q in allcu.items():
 polys=[p for p in (q.geoms if hasattr(q,'geoms')else[q])if p.area>1e-9];indices[l]=list(range(len(nodes),len(nodes)+len(polys)));nodes.extend(polys);trees[l]=STRtree(polys)
def hits(l,q):return [indices[l][int(i)]for i in trees[l].query(q,predicate='intersects')if nodes[indices[l][int(i)]].intersection(q).area>1e-8]
for d in plated:
 ann=d.buffer(.03).difference(d.buffer(-.0001));contacts=[i for l in allcu for i in hits(l,ann)]
 if len(contacts)<2:continue
 via=next((v for v in j if v['type']=='pcb_via'and math.hypot(v['x']-d.centroid.x,v['y']-d.centroid.y)<.0008 and abs(d.area-math.pi*(v['hole_diameter']/2)**2)<1e-5),None)
 idx=len(nodes);nodes.append(d)
 for i in contacts:adj[i].append((idx,1 if via else 0));adj[idx].append((i,0))
sc={e['source_component_id']:e['name']for e in j if e['type']=='source_component'};pc={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};pp={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'}
def native_nodes(ref):
 out=[]
 for e in j:
  if e['type']not in ['pcb_smtpad','pcb_plated_hole']or not e.get('pcb_port_id'):continue
  p=pp[e['pcb_port_id']]
  if sc[pc[p['pcb_component_id']]['source_component_id']]+'.'+sp[p['source_port_id']]['name']!=ref:continue
  q=cam.shape(e).difference(cut)
  out.extend(i for l in e.get('layers',[e.get('layer','top')])if l in allcu for i in hits(l,q))
 assert out,('No actual native contact nodes',ref)
 return set(out)
def transitions(a,b):
 starts=native_nodes(a);goals=native_nodes(b);best={i:0 for i in starts};heap=[(0,i)for i in starts];heapq.heapify(heap)
 while heap:
  cost,i=heapq.heappop(heap)
  if cost!=best[i]:continue
  if i in goals:return cost
  for nxt,w in adj[i]:
   val=cost+w
   if val<best.get(nxt,1e9):best[nxt]=val;heapq.heappush(heap,(val,nxt))
 raise AssertionError(('Actual power path disconnected',a,b))
pathrows=[]
for net,pin in [('A_PLUS','OUT1A'),('A_MINUS','OUT1B'),('B_PLUS','OUT2A'),('B_MINUS','OUT2B')]:
 a,b='U_DRV.'+pin,'J_MOTOR.'+net;pathrows.append({'net':net,'from':a,'to':b,'minimumAvailableThroughViaTransitions':transitions(a,b)})
for a in ['J_PD.VBUS1','J_PD.VBUS2']:
 for b in ['U_DRV.VBB1','U_DRV.VBB2']:pathrows.append({'net':'PD_VBUS','from':a,'to':b,'minimumAvailableThroughViaTransitions':transitions(a,b)})
report={'schema':'outer-power-actual-cam-1','source_sha256':sha(source),'native_policy_sha256':sha(root/'artifacts/validation/service-outer-power-policy.json'),'cam_audit_sha256':sha(root/'artifacts/manufacturing/audit.json'),'archive_sha256':sha(archive),'files_sha256':files,'checksPassed':not errors,'errors':errors,'method':'Parse actual RS274X copper and Excellon drills independently; require each native-policy-approved wire strip on its designated outer copper layer after drilled voids are removed. Actual CAM net-island assignment, spacing, source equality and archive equality must separately PASS. Analytic rounding tolerance 0.0002 mm. Native bounded fanouts and resistor-only leaves remain explicitly distinguished from main-width strips.','actual_minimum_via_paths':pathrows,'via_path_scope':'Minimum available via-layer changes in actual plated-drill/copper-island topology; total branched via counts remain in the native policy. Does not model current splitting, distributed resistance, temperatures or hardware operation. Native component PTH contacts are not counted as routing vias.','mainWidthMm':.45,'senseMainWidthMm':.30,'traces':rows,'hardwareQualified':False}
(root/'artifacts/validation/service-outer-power-cam.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checksPassed':not errors,'errors':errors,'powerTraceRecords':len(rows)},indent=2));raise SystemExit(bool(errors))
