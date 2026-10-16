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
         'SENSE1':.4,'SENSE2':.4,'LOGIC_IN':.35,'DATA_VBUS':.40,
         'V3V3':.35,'V1V1':.10,'BUCK_SW':.45,'BUZZER_SINK':.15,'GND':.8,
         'LED_B':.001,'STATUS_B_K':.006}  # 3.3 V digital-NPN input; USB 5.5 V / 0.99 kohm LED sink bound with margin.
segments=[]; errors=[]; netrows=collections.defaultdict(list)
ground_geometry={}
for layer in ['top','inner1','inner2','bottom']:
    regions=[]
    for e in g.j:
        if e['type']!='pcb_copper_pour' or e['layer']!=layer:continue
        b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']]
        regions.append(Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]))
    ground_geometry[layer]=unary_union(regions)
# Review terminal PD branches from actual physical connectivity, not trace IDs.
# Removing a branch must isolate exactly one VBB input or the charge-pump bypass capacitor.
# The combined driver feeder retains the full 0.75 A budget.
one_bridge=None
terminal_pd={};pd_key=next(k for k,v in g.nets.items() if v=='PD_VBUS')
for trace in list(g.j):
    if trace['type']!='pcb_trace' or g.key(trace)!=pd_key:continue
    if not any(p.get('layer','').startswith('inner') and p.get('width',1)<.5 for p in trace['route']):continue
    index=g.j.index(trace);g.j.pop(index);elems,roots=g.groups(pd_key);islands={}
    for elem,r in zip(elems,roots):
        if elem.get('pcb_port_id'):
            port=g.ports[elem['pcb_port_id']];sp=g.sp[port['source_port_id']]
            islands.setdefault(r,set()).add(g.src[sp['source_component_id']]+'.'+sp['name'])
    g.j.insert(index,trace)
    terminals=[v for v in islands.values() if len(v)==1 and next(iter(v)) in ['U_DRV.VBB1','U_DRV.VBB2','C_VCP.pin2','R_PD.pin1','R_VM_H.pin1']]
    if len(islands)==2 and len(terminals)==1:
        terminal=next(iter(terminals[0]));budget={'R_PD.pin1':.04,'R_VM_H.pin1':.001}.get(terminal,.4)
        terminal_pd[trace['pcb_trace_id']]={'isolated_physical_terminal':terminal,'current_budget_A':budget,'cut_verified_against_actual_physical_copper':True}
# Physically cut each 3.3 V branch to screen its actual downstream load.
# Use the full rail budget whenever the cut does not isolate a single load side.
logic_loads={'U_MCU':.15,'U_FLASH':.03,'U_DRV':.02,'U_TEMP':.001,'BZ1':.12,'R_PWR_LED':.011,'R_TEMP_SDA':.001,'R_TEMP_SCL':.001}
logic_branches={}
v3_key=next(k for k,v in g.nets.items() if v=='V3V3')
for trace in list(g.j):
    if trace['type']!='pcb_trace' or g.key(trace)!=v3_key:continue
    index=g.j.index(trace);g.j.pop(index);elems,roots=g.groups(v3_key);islands={}
    for elem,r in zip(elems,roots):
        if elem.get('pcb_port_id'):
            port=g.ports[elem['pcb_port_id']];sp=g.sp[port['source_port_id']]
            islands.setdefault(r,set()).add(g.src[sp['source_component_id']])
    g.j.insert(index,trace)
    if len(islands)==2 and sum('L_BUCK' in group for group in islands.values())==1:
        downstream=next(group for group in islands.values() if 'L_BUCK' not in group)
        load=min(.35,max(.03,sum(logic_loads.get(ref,0) for ref in downstream)))
        logic_branches[trace['pcb_trace_id']]={'downstream_components':sorted(downstream),'current_budget_A':load,'cut_verified_against_actual_physical_copper':True}
# The RGB anode branch draws at most three 5 V / 1 kohm channels.
# Keep the full USB supply budget unless a physical cut isolates only D_STATUS.
data_branches={}
data_key=next(k for k,v in g.nets.items() if v=='DATA_VBUS')
for trace in list(g.j):
    if trace['type']!='pcb_trace' or g.key(trace)!=data_key:continue
    index=g.j.index(trace);g.j.pop(index);elems,roots=g.groups(data_key);islands={}
    for elem,r in zip(elems,roots):
        if elem.get('pcb_port_id'):
            port=g.ports[elem['pcb_port_id']];sp=g.sp[port['source_port_id']]
            islands.setdefault(r,set()).add(g.src[sp['source_component_id']])
    g.j.insert(index,trace)
    if len(islands)==2 and sum(group=={'R_USB_SENSE_H'} for group in islands.values())==1:
        assert next(e for e in g.j if e['type']=='source_component' and e['name']=='R_USB_SENSE_H')['resistance']==100000
        data_branches[trace['pcb_trace_id']]={'downstream_components':['R_USB_SENSE_H'],'current_budget_A':.001,'cut_verified_against_actual_physical_copper':True}
    if len(islands)==2 and sum(group=={'D_STATUS'} for group in islands.values())==1:
        data_branches[trace['pcb_trace_id']]={'downstream_components':['D_STATUS'],'current_budget_A':.02,'cut_verified_against_actual_physical_copper':True}
for e in g.j:
    if e['type']!='pcb_trace':continue
    name=g.nets.get(g.key(e),'direct')
    for a,b in zip(e['route'],e['route'][1:]):
        if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
        length=math.hypot(a['x']-b['x'],a['y']-b['y']);width=min(a['width'],b['width'])
        internal=a['layer'].startswith('inner');thickness=.0175 if internal else .035
        current=terminal_pd.get(e['pcb_trace_id'],logic_branches.get(e['pcb_trace_id'],data_branches.get(e['pcb_trace_id'],{}))).get('current_budget_A',budgets.get(name,0))
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
    pour_areas.append({'id':e['pcb_copper_pour_id'],'layer':e['layer'],'areaMm2':p.area})
if not pours:errors.append('Ground pours missing')
if board['num_layers']==4 and not any(p['layer']=='inner1' and p['areaMm2']>700 for p in pour_areas):
    errors.append('Large inner1 ground plane missing')
resistors={e['name']:e['resistance'] for e in g.j if e['type']=='source_component' and 'resistance' in e}
adcmax=35*resistors['R_VM_L']*1.01/(resistors['R_VM_H']*.99+resistors['R_VM_L']*1.01)
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
    if name in ['PD_VBUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','BUZZER_SINK'] and via['hole_diameter']<.25:
        errors.append('Power via drill below reviewed 0.25 mm: '+via['pcb_via_id'])
report={'viaReview':vias,'sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'checksPassed':not errors,'errors':errors,
        'copperSpecification':{'externalUmMinimum':35,'internalUmMinimum':17.5,'boardThicknessMm':1.6,'viaPlatingUmMinimum':20},
        'temperatureRiseScreenLimitC':30,'method':'IPC-2221 k=0.048 external / 0.024 internal; area in square mils',
        'budgetsA':budgets,'singleBridgePdBranchTrace':one_bridge,'physicalTerminalPdBranches':terminal_pd,'physicalLogicBranches':logic_branches,'physicalDataLedBranches':data_branches,'logicLoadBudgetsA':logic_loads,'nets':summary,'segments':segments,
        'groundPours':pour_areas,'adcVoltageAt15V':15*resistors['R_VM_L']/(resistors['R_VM_H']+resistors['R_VM_L']),
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
