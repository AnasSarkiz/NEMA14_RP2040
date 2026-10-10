"""Mandatory actual-copper policy: outer-layer motor/PD routes and bounded native pin escapes."""
import json,math,hashlib,collections
from shapely.ops import unary_union
import verify_supplier_connectivity as g
from shapely.geometry import LineString,Point
rp=g.ROOT.name=='NEMA14_RP2040';original=g.j
motor=['A_PLUS','A_MINUS','B_PLUS','B_MINUS'];selected=motor+['PD_VBUS','SENSE1','SENSE2']
errors=[];rows=[];proofs=[];branches={}
pdkey=next(k for k,n in g.nets.items()if n=='PD_VBUS')
for trace in [e for e in original if e['type']=='pcb_trace'and g.key(e)==pdkey]:
 if min(p.get('width',100)for p in trace['route'])>=.6-1e-6:continue
 g.j=[e for e in original if e is not trace];es,rs=g.groups(pdkey);groups=collections.defaultdict(set)
 for e,r in zip(es,rs):
  if e.get('pcb_port_id'):
   p=g.ports[e['pcb_port_id']];groups[r].add(g.src[g.comp[p['pcb_component_id']]['source_component_id']]+'.'+g.sp[p['source_port_id']]['name'])
 if len(groups)!=2:continue
 for leaf in groups.values():
  ref='R_VM_H'if leaf=={'R_VM_H.pin1'}else'R_PD'if leaf=={'R_PD.pin1'}else None
  if not ref:continue
  main=next(v for v in groups.values()if v is not leaf)
  if not {'J_PD.VBUS1','J_PD.VBUS2','U_DRV.VBB1','U_DRV.VBB2'}<=main:continue
  limit=.001 if ref=='R_VM_H'else .04;ohms=100000 if ref=='R_VM_H'else 1000
  assert 38.6/(ohms*.99)<limit
  branches[trace['pcb_trace_id']]={'leaf':sorted(leaf),'seriesResistorOhms':ohms,'screenCurrentA':limit,'proof':'Removing this exact copper record leaves exactly two native-pad islands; the leaf contains only the resistor input, and the other retains both inlet and driver supply pins.'}
g.j=original
# Exact footprints force narrow fanout out of their native pad rows. No
# general motor-current width reduction is allowed outside these bounded records.
allowed={}
for n in motor:allowed['inside_phase_escape_'+n]=('U_DRV',{'A_PLUS':'OUT1A','A_MINUS':'OUT1B','B_PLUS':'OUT2A','B_MINUS':'OUT2B'}[n],.2 if n=='A_MINUS'else .3,2.0)
for ref,pin in [('U_DRV','VBB1'),('U_DRV','VBB2'),('C_VM'if rp else'C_VM2','pin1')]:allowed['inside_power_escape_'+ref+'_'+pin]=(ref,pin,.3,2.0)
for pin in ['VBUS1','VBUS2']:allowed['outer_usb_power_pin_escape_'+pin]=('J_PD',pin,.3,1.250001)
for e in original:
 if e['type']!='pcb_trace'or g.nets.get(g.key(e))not in selected:continue
 name=g.nets[g.key(e)];tid=e['pcb_trace_id'];route=e['route'];segments=[(a,b)for a,b in zip(route,route[1:])if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']];length=sum(math.dist((a['x'],a['y']),(b['x'],b['y']))for a,b in segments);widths=[min(a['width'],b['width'])for a,b in segments];minimum=.45 if name=='PD_VBUS'or name in motor else .3
 for a,b in segments:
  if a['layer']not in ['top','bottom']:errors.append(tid+': forbidden motor/PD/sense wire layer '+a['layer'])
 exception=None
 if widths and min(widths)<minimum-1e-6:
  if tid in allowed:
   ref,pin,w,maxlength=allowed[tid];port=next((p for p in g.ports.values()if g.src[g.comp[p['pcb_component_id']]['source_component_id']]==ref and g.sp[p['source_port_id']]['name']==pin),None)
   start=route[0];end=route[-1];via=next((v for v in original if v['type']=='pcb_via'and g.key(v)==g.key(e)and math.dist((end['x'],end['y']),(v['x'],v['y']))<1e-6),None)
   topmain=unary_union([LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(min(a['width'],b['width'])/2)for other in original if other['type']=='pcb_trace'and other is not e and g.key(other)==g.key(e)for a,b in zip(other['route'],other['route'][1:])if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']=='top'and min(a['width'],b['width'])>=minimum-1e-6])
   direct=topmain.buffer(1e-7).covers(Point(end['x'],end['y']).buffer(w/2))
   standard=via is not None and via['hole_diameter']==.25 and via['outer_diameter']==.5
   valid=port is not None and math.dist((start['x'],start['y']),(port['x'],port['y']))<1e-6 and len(segments)==len(route)-1 and all(a['layer']=='top'and a['width']==w and b['width']==w for a,b in segments)and length<=maxlength and (standard or direct)
   exception={'kind':'bounded_native_pin_escape','reference':ref,'pin':pin,'widthMm':w,'maximumLengthMm':maxlength,'lengthMm':length,'startsAtExactNativePin':port is not None and math.dist((start['x'],start['y']),(port['x'],port['y']))<1e-6,'endConnectionKind':'standard_0p25_0p50_barrel'if standard else'full_endcap_direct_top_main','endsAtStandardViaOrFullWidthTopMain':valid}
   if not valid:errors.append(tid+': invalid bounded native pin escape')
  elif tid in branches and min(widths)>=.16-1e-6:exception={'kind':'physically_proven_resistor_only_branch',**branches[tid]}
  else:errors.append(tid+': width below '+str(minimum)+' mm outside proven pin escape/resistor leaf')
 if exception:proofs.append({'trace':tid,'net':name,**exception})
 rows.append({'trace':tid,'net':name,'wireLayers':sorted({a['layer']for a,b in segments}),'minimumWidthMm':min(widths)if widths else None,'lengthMm':length,'exception':exception is not None})
summary=[]
for name in selected:
 nr=[r for r in rows if r['net']==name];main=[r for r in nr if not r['exception']];vias=[v for v in original if v['type']=='pcb_via'and g.nets.get(g.key(v))==name]
 if not nr:errors.append('No routed copper on '+name)
 if not main:errors.append('No compliant main route on '+name)
 summary.append({'net':name,'wireLayers':sorted({l for r in nr for l in r['wireLayers']}),'mainMinimumWidthMm':min([r['minimumWidthMm']for r in main if r['minimumWidthMm']is not None]or[0]),'mainBranchedLengthMm':sum(r['lengthMm']for r in main),'allBranchedLengthMm':sum(r['lengthMm']for r in nr),'totalThroughVias':len(vias),'viaIds':[v['pcb_via_id']for v in vias],'notes':'Counts/lengths include all branches, not series path counts. Standard barrels traverse the stack; no inner-layer wire routes are permitted.'})
report={'schema':'outer-power-routing-policy-1','sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'checksPassed':not errors,'errors':errors,'rules':{'motorMainMm':.45,'pdMainMm':.45,'senseMainMm':.30,'wireLayers':['top','bottom'],'finePitchPinEscapeMaximumMm':2,'usbPinEscapeMaximumMm':1.25,'vias':'Minimize; nonzero through-via counts are disclosed, not represented as via-free.','separateRequiredChecks':['actual Gerber/drill connectivity, shorts and clearance','native placement/connectivity','minimum via plating and thermal/current qualification']},'nets':summary,'boundedExceptions':proofs,'traces':rows,'hardwareQualified':False}
(g.ROOT/'artifacts/validation/service-outer-power-policy.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checksPassed':not errors,'errors':errors,'nets':summary},indent=2));raise SystemExit(bool(errors))
