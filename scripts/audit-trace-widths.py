"""Review actual saved copper, not nominal widths in the JSX source.

IPC-2221 equations are a conservative screening estimate, not qualification.
External copper: 35 um. Internal copper: 17.5 um. Allowed estimate: 30 C rise.
Power budgets are deliberately higher than normal logic/phase consumption.
BUCK_SW 0.48A is an RMS thermal screen: sqrt(0.55*0.31 + 0.741**2/12)=0.465A,
rounded up; 0.921A transient peak remains separately checked. GND 0.8A includes
two 0.25A phase ceilings, 0.1A baseline and 0.4A sounder pulses at 50% carrier/
10% burst duty (0.0895A RMS), conservatively summed and rounded up.
Parallel-plane disposition is only used where actual same-net fill covers
the complete centerline. Current sharing/return impedance require bench testing.
"""
import json, math, hashlib, collections
import verify_supplier_connectivity as g
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

board=next(e for e in g.j if e['type']=='pcb_board')
budgets={'PD_VBUS':.75,'A_PLUS':.4,'A_MINUS':.4,'B_PLUS':.4,'B_MINUS':.4,
         'SENSE1':.4,'SENSE2':.4,'LOGIC_IN':.25,'DATA_VBUS':.15,
         'V3V3':.55,'V1V1':.10,'BUCK_SW':.48,'BUZZER_SINK':.4,'GND':.8}
segments=[]; errors=[]; netrows=collections.defaultdict(list)
ground_geometry={}
supply_geometry={}
for layer in ['top','inner1','inner2','bottom']:
    regions=[]
    for e in g.j:
        if e['type']!='pcb_copper_pour' or e['layer']!=layer or g.nets.get(g.key(e))!='GND':continue
        b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']]
        regions.append(Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]))
    ground_geometry[layer]=unary_union(regions)
    power=[]
    for e in g.j:
        if e['type']!='pcb_copper_pour' or e['layer']!=layer or g.nets.get(g.key(e))!='V3V3':continue
        b=e['brep_shape'];pts=lambda ring:[(p['x'],p['y']) for p in ring['vertices']]
        power.append(Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]))
    supply_geometry[layer]=unary_union(power)
# A reduced budget is permitted only after physically cutting this exact record
# separates a sole series-resistor input from the inlet and all motor loads.
branch_budgets={};branch_proofs=[];original=g.j
pdkey=next((k for k,n in g.nets.items() if n=='PD_VBUS'),None)
for trace in [e for e in original if e['type']=='pcb_trace' and g.key(e)==pdkey]:
    g.j=[e for e in original if e is not trace];es,rs=g.groups(pdkey);groups=collections.defaultdict(set)
    for e,r in zip(es,rs):
        if e.get('pcb_port_id'):
            p=g.ports[e['pcb_port_id']];groups[r].add(g.src[g.comp[p['pcb_component_id']]['source_component_id']]+'.'+g.sp[p['source_port_id']]['name'])
    if len(groups)!=2:continue
    for leaf in groups.values():
        ref='R_VM_H' if leaf=={'R_VM_H.pin1'} else 'R_PD' if leaf=={'R_PD.pin1'} else None
        if not ref:continue
        main=next(v for v in groups.values() if v is not leaf)
        if not {'J_PD.VBUS1','J_PD.VBUS2','U_DRV.VBB1','U_DRV.VBB2'}<=main:continue
        nominal=100000 if ref=='R_VM_H' else 1000
        bound=(35+3.6)/(nominal*.99);budget=.001 if ref=='R_VM_H' else .04
        assert bound<budget
        branch_budgets[trace['pcb_trace_id']]=budget;branch_proofs.append({'trace':trace['pcb_trace_id'],'leafNativePorts':sorted(leaf),'mainNativePorts':sorted(main),'seriesResistorOhms':nominal,'resistanceToleranceFraction':.01,'voltageDifferenceScreenV':38.6,'calculatedResistorLimitedCurrentA':bound,'screenBudgetA':budget,'method':'Remove exact Cu record; all-layer native-pad/barrel connectivity splits into exactly two pad islands. The leaf contains only the input of the named series resistor. No motor or inlet pad resides on it.','qualification':'Voltage case is conductor screening only; does not approve 35V operation or component/driver surge limits.'})
g.j=original
# The main-width/layer rule is mandatory and independently bound to this source.
# Thermal screening does not grant a width exception. The policy positively
# proves native pin escapes and resistor-only leaves against physical islands.
import subprocess
q=subprocess.run([__import__('sys').executable,str(g.ROOT/'scripts/audit-outer-power.py')],capture_output=True,text=True)
policy=json.loads((g.ROOT/'artifacts/validation/service-outer-power-policy.json').read_text())
assert policy['sha256']==hashlib.sha256(g.path.read_bytes()).hexdigest()
errors.extend(policy['errors'])
if q.returncode and not policy['errors']:errors.append('Outer power policy failed')
allowed_necks={p['trace'] for p in policy['boundedExceptions']}
neck_proofs=policy['boundedExceptions']
# Prove the driver-only VDD leaf by removing its actual conductor from the graph.
# Motor bridge/buzzer/current-setting references are not on this branch.
branch='diagnostics_3c928318_trace_191_new_0'
t=next((e for e in g.j if e.get('pcb_trace_id')==branch),None)
driver_proof=None
if t:
    index=g.j.index(t);g.j.pop(index)
    items,roots=g.groups(g.key(t));sets={}
    for item,root in zip(items,roots):
        if item.get('pcb_port_id'):
            port=g.ports[item['pcb_port_id']]
            ref=g.src[g.comp[port['pcb_component_id']]['source_component_id']]
            sets.setdefault(root,set()).add((ref,g.sp[port['source_port_id']]['pin_number']))
    g.j.insert(index,t)
    expected={('U_DRV',pin) for pin in [9,10,11,12,15]}|{('C_DRV_LOGIC',1)}
    assert len(sets)==2 and expected in sets.values(), 'Driver leaf topology changed; review branch load again'
    branch_budgets[branch]=.020
    driver_proof={'trace':branch,'physicallyIsolatedTerminals':sorted(expected),'screenCurrentA':.020,'datasheetLogicSupplyMaximumA':.008,'datasheetCondition':'A4988 Rev5, fPWM <50kHz; input leakage20uA/pin. 20mA branch budget adds margin for transient/bypass currents; scope actual ripple/current and fPWM. Not measured.'}
one_bridge=None
for e in g.j:
    if e['type']!='pcb_trace':continue
    name=g.nets.get(g.key(e),'direct')
    for a,b in zip(e['route'],e['route'][1:]):
        if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
        length=math.hypot(a['x']-b['x'],a['y']-b['y']);width=min(a['width'],b['width'])
        internal=a['layer'].startswith('inner');thickness=.0175 if internal else .035
        current=branch_budgets.get(e['pcb_trace_id'],budgets.get(name,0))
        area=width*thickness/(.0254**2);k=.024 if internal else .048
        rise=(current/(k*area**.725))**(1/.44) if current else None
        plane=ground_geometry[a['layer']] if name=='GND' else supply_geometry[a['layer']] if name=='V3V3' else None
        shunted=plane is not None and plane.buffer(.00001).covers(LineString([(a['x'],a['y']),(b['x'],b['y'])]))
        row={'trace':e['pcb_trace_id'],'net':name,'layer':a['layer'],'widthMm':width,'lengthMm':length,
             'copperThicknessUm':thickness*1000,'currentBudgetA':current,
             'ipc2221TemperatureRiseEstimateC':rise,'resistanceAt20CMilliohm':.01724*length/(width*thickness),
             'sameNetPourCoversCenterline':shunted,
             'thermalScreenDisposition':'parallel-plane-requires-prototype-current-sharing-review' if shunted else 'isolated-track-screen'}
        segments.append(row);netrows[name].append(row)
        if width<.16-1e-6:errors.append('Trace below 0.16 mm: '+e['pcb_trace_id'])
        if rise is not None and rise>30 and not shunted:errors.append('Thermal screening budget exceeded: '+e['pcb_trace_id'])
        if name in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','PD_VBUS'] and width < (.30 if name in ['SENSE1','SENSE2'] else .45)-1e-6 and e['pcb_trace_id'] not in allowed_necks:
            errors.append('Power copper below mandatory main floor without a proved exception: '+e['pcb_trace_id'])
summary=[]
for name,rows in sorted(netrows.items()):
    # Total includes all branches; it is not an end-to-end path measurement.
    summary.append({'net':name,'minWidthMm':min(r['widthMm'] for r in rows),'maxWidthMm':max(r['widthMm'] for r in rows),
                    'totalBranchedCopperLengthMm':sum(r['lengthMm'] for r in rows),
                    'maxTemperatureRiseEstimateC':max((r['ipc2221TemperatureRiseEstimateC'] or 0) for r in rows)})
pours=[e for e in g.j if e['type']=='pcb_copper_pour']
pour_areas=[]
for e in pours:
    b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']]
    p=Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])])
    pour_areas.append({'id':e['pcb_copper_pour_id'],'net':g.nets.get(g.key(e),'direct'),'layer':e['layer'],'areaMm2':p.area})
ground_areas=[p for p in pour_areas if p['net']=='GND']
if not ground_areas:errors.append('Ground pours missing')
# Holeless CAM export splits one physical plane into touching contours.
# Area is evaluated on their union; connectedness remains independently checked.
inner1_ground=unary_union([Polygon([(v['x'],v['y']) for v in e['brep_shape']['outer_ring']['vertices']], [[(v['x'],v['y']) for v in r['vertices']] for r in e['brep_shape'].get('inner_rings',[])]) for e in g.j if e['type']=='pcb_copper_pour' and e['layer']=='inner1' and g.key(e)==next(x['subcircuit_connectivity_map_key'] for x in g.j if x['type']=='source_net' and x['name']=='GND')])
if board['num_layers']==4 and inner1_ground.area<=700:
    errors.append('Large inner1 ground plane missing')
resistors={e['name']:e['resistance'] for e in g.j if e['type']=='source_component' and 'resistance' in e}
parallel=lambda a,b:a*b/(a+b)
adc_load=parallel(resistors['R_VM_L'],resistors['R_VM_BLEED'])
adc_load_max=parallel(resistors['R_VM_L']*1.01,resistors['R_VM_BLEED']*1.01)
adcmax=35*adc_load_max/(resistors['R_VM_H']*.99+adc_load_max)
vm_div_max=35*resistors['R_VM_L']*1.01/(resistors['R_VM_H']*.99+resistors['R_VM_L']*1.01)
if adcmax+1e-6*resistors['R_VM_BLEED']*1.01>.3:errors.append('Passive motor monitor exceeds powered-off0.3V ADC limit')
vias=[]
for via in [e for e in g.j if e['type']=='pcb_via']:
    name=g.nets.get(g.key(via),'direct');current=budgets.get(name,0)
    # Ideal barrel estimate with a required 20 um minimum plating thickness.
    area=math.pi*via['hole_diameter']*.020
    resistance=.01724*board['thickness']/area
    vias.append({'id':via['pcb_via_id'],'net':name,'drillMm':via['hole_diameter'],
                 'padMm':via['outer_diameter'],'minimumPlatingUm':20,
                 'estimatedBarrelResistanceMilliohm':resistance,
                 'voltageDropAtNetBudgetMillivolt':current*resistance})
    if name in ['PD_VBUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2'] and via['hole_diameter']<.25:
        errors.append('Power via drill below reviewed 0.25 mm: '+via['pcb_via_id'])
report={'driverLogicBranchProof':driver_proof,'bounded_output_neck_proofs':neck_proofs,'viaReview':vias,'sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'checksPassed':not errors,'errors':errors,
        'copperSpecification':{'externalUmMinimum':35,'internalUmMinimum':17.5,'boardThicknessMm':1.6,'viaPlatingUmMinimum':20},
        'temperatureRiseScreenLimitC':30,'method':'IPC-2221 k=0.048 external / 0.024 internal; area in square mils',
        'budgetsA':budgets,'physicallyVerifiedResistorBranchBudgets':branch_proofs,'singleBridgePdBranchTrace':one_bridge,'nets':summary,'segments':segments,
        'groundPours':ground_areas,'copperPours':pour_areas,'adcVoltageAt15V':15*adc_load/(resistors['R_VM_H']+adc_load),
        'passiveAdcWorstVoltageAt35V':adcmax,'enabledAdcNominalScale':(resistors['R_VM_H']+adc_load)/adc_load,
        'poweredOffDcVoltageBoundVolts':adcmax+1e-6*resistors['R_VM_BLEED']*1.01,
        'adcWorstVoltageAt35V':adcmax,'qualifiedForManufacture':False,
        'groundThermalCurrentSharingAnalysisPending':True,
        'limits':['Temperature estimates assume specified minimum copper, not a measured fabrication stackup.',
                  'Ground planes add parallel paths; the individual trace screen does not model plane necks or ground bounce.',
                  'Via resistance/plating, switching pulses, USB impedance, EMI and regulator stability require separate validation.',
                  'Branched copper totals are not USB pair skew or point-to-point resistance.',
                  'A4988 current accuracy and sense/ground path parasitics still require phase-current measurements.']}
(g.ROOT/'artifacts/trace-width-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'segmentsChecked':len(segments),'groundRegions':len(pours),'errors':errors,'qualifiedForManufacture':False},indent=2))
raise SystemExit(bool(errors))
