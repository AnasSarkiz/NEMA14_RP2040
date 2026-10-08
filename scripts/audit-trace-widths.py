"""Review actual saved copper, not nominal widths in the JSX source.

IPC-2221 equations are a conservative screening estimate, not qualification.
External copper: 35 um. Internal copper: 17.5 um. Allowed estimate: 30 C rise.
Power budgets are deliberately higher than normal logic/phase consumption.
"""
import json, math, hashlib, collections
import verify_supplier_connectivity as g
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

board=next(e for e in g.j if e['type']=='pcb_board')
budgets={'PD_VBUS':.75,'A_PLUS':.4,'A_MINUS':.4,'B_PLUS':.4,'B_MINUS':.4,
         'SENSE1':.4,'SENSE2':.4,'LOGIC_IN':.15,'DATA_VBUS':.15,
         'V3V3':.15,'V1V1':.10,'BUCK_SW':.20,'GND':.8}
segments=[]; errors=[]; netrows=collections.defaultdict(list)
ground_geometry={}
for layer in ['top','inner1','inner2','bottom']:
    regions=[]
    for e in g.j:
        if e['type']!='pcb_copper_pour' or e['layer']!=layer or g.nets.get(g.key(e))!='GND':continue
        b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']]
        regions.append(Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]))
    ground_geometry[layer]=unary_union(regions)
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
        shunted=name=='GND' and ground_geometry[a['layer']].buffer(.00001).covers(LineString([(a['x'],a['y']),(b['x'],b['y'])]))
        row={'trace':e['pcb_trace_id'],'net':name,'layer':a['layer'],'widthMm':width,'lengthMm':length,
             'copperThicknessUm':thickness*1000,'currentBudgetA':current,
             'ipc2221TemperatureRiseEstimateC':rise,'resistanceAt20CMilliohm':.01724*length/(width*thickness),
             'groundPourCoversCenterline':shunted,
             'thermalScreenDisposition':'parallel-plane-requires-ground-current-sharing-review' if shunted else 'isolated-track-screen'}
        segments.append(row);netrows[name].append(row)
        if width<.16-1e-6:errors.append('Trace below 0.16 mm: '+e['pcb_trace_id'])
        if rise is not None and rise>30 and not shunted:errors.append('Thermal screening budget exceeded: '+e['pcb_trace_id'])
        if name in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2'] and width<.279-1e-6:
            errors.append('Motor/sense copper below reviewed 0.279 mm escape floor: '+e['pcb_trace_id'])
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
if board['num_layers']==4 and not any(p['layer']=='inner1' and p['areaMm2']>700 for p in ground_areas):
    errors.append('Large inner1 ground plane missing')
resistors={e['name']:e['resistance'] for e in g.j if e['type']=='source_component' and 'resistance' in e}
parallel=lambda a,b:a*b/(a+b)
adc_load=parallel(resistors['R_VM_L'],resistors['R_VM_BLEED'])
adc_load_max=parallel(resistors['R_VM_L']*1.01,resistors['R_VM_BLEED']*1.01)
adcmax=35*adc_load_max/(resistors['R_VM_H']*.99+adc_load_max)
vm_div_max=35*resistors['R_VM_L']*1.01/(resistors['R_VM_H']*.99+resistors['R_VM_L']*1.01)
if adcmax>3.3:errors.append('Motor voltage divider exceeds ADC review envelope')
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
report={'viaReview':vias,'sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'checksPassed':not errors,'errors':errors,
        'copperSpecification':{'externalUmMinimum':35,'internalUmMinimum':17.5,'boardThicknessMm':1.6,'viaPlatingUmMinimum':20},
        'temperatureRiseScreenLimitC':30,'method':'IPC-2221 k=0.048 external / 0.024 internal; area in square mils',
        'budgetsA':budgets,'physicallyVerifiedResistorBranchBudgets':branch_proofs,'singleBridgePdBranchTrace':one_bridge,'nets':summary,'segments':segments,
        'groundPours':ground_areas,'copperPours':pour_areas,'adcVoltageAt15V':15*adc_load/(resistors['R_VM_H']+adc_load),
        'switchInputWorstVoltageAt35V':vm_div_max,'enabledAdcNominalScale':(resistors['R_VM_H']+adc_load)/adc_load,
        'poweredOffDcVoltageBoundVolts':10e-6*resistors['R_VM_BLEED']*1.01,
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
