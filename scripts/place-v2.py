"""Pack intact supplier courtyards on the 34 mm V2 draft.

This is a placement screen, not a copper, 3D, wire-access or manufacturing signoff.
The ordered V1 geometry is never rewritten by this script.
"""
import json, math, re, sys
from pathlib import Path
from ortools.sat.python import cp_model
from shapely.geometry import Polygon, box
from shapely.affinity import rotate, translate

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT/'src/jlcpcb-catalog.json').read_text())
placement = json.loads((ROOT/'src/supplier-placement.json').read_text())
baseline = json.loads((ROOT/'artifacts/v1-ordered/index.circuit.json').read_text())
sources = {e['source_component_id']:e for e in baseline if e['type']=='source_component'}
components = {e['pcb_component_id']:e for e in baseline if e['type']=='pcb_component'}
ports = {e['source_port_id']:e for e in baseline if e['type']=='source_port'}
local = {}
for name,code in catalog['components'].items():
    if name == 'U_ENCODER': continue
    text = (ROOT/catalog['parts'][code]['importPath']).read_text()
    match = re.search(r'<courtyardoutline outline=\{(\[.*?\])\}',text,re.S)
    if not match: raise ValueError('Missing original courtyard: '+name)
    local[name] = Polygon([(p['x'],p['y']) for p in json.loads(match[1])])
# Physical test pads must also be respected.
for name in placement:
    if name.startswith('TP_'): local[name] = box(-.7,-.7,.7,.7)

telemetry_bottom='--telemetry-bottom' in sys.argv
bottom_names={n+p for n in ['U_I','R_SHUNT_','C_I','R_I','C_IADC_'] for p in ['A','B']} if telemetry_bottom else set()
if telemetry_bottom:
    bottom_names.update(['C_IO1','C_IO10','C_IO22','C_IO33','C_IO42','C_IO49','C_DV23','C_DV50','C_USB','C_ADC','C_VREG_IN','C_VREG_OUT'])
model = cp_model.CpModel()
scale = 100
xs,ys,objective,variables,anchors = [],[],[],{},{}
bx,by=[],[]
fixed = {'U_MCU','U_DRV','J_PD','J_DATA','Y_MCU'}
boundary = 16.75
def obstacle(xlist,ylist,x,y,w,h,name):
    xlist.append(model.new_fixed_size_interval_var(round(x*scale),math.ceil(w*scale),name+'x'))
    ylist.append(model.new_fixed_size_interval_var(round(y*scale),math.ceil(h*scale),name+'y'))
if telemetry_bottom:
    # Retain the optional encoder IC's bottom courtyard; its capacitors are top-side.
    for name in ['U_ENCODER']:
        text=(ROOT/catalog['parts'][catalog['components'][name]]['importPath']).read_text()
        match=re.search(r'<courtyardoutline outline=\{(\[.*?\])\}',text,re.S)
        p=placement[name];poly=translate(rotate(Polygon([(v['x'],v['y']) for v in json.loads(match[1])]),p['pcbRotation'],origin=(0,0)),xoff=p['pcbX'],yoff=p['pcbY'])
        a,b,c,d=poly.bounds;obstacle(bx,by,a,b,c-a,d-b,'bottom_'+name)
    # Both USB shell stakes and locating holes go through the board.
    for name in ['J_PD','J_DATA']:
        p=placement[name]
        for x in [-3.8474968,4.1524872]:
            for y in [-1.429893,1.429893]:
                obstacle(bx,by,p['pcbX']+x-1.05,p['pcbY']+y-.8,2.1,1.6,f'{name}{x}{y}')
        for x in [-3.8474968,4.1524872]:
            obstacle(bx,by,p['pcbX']+x-1,p['pcbY']-.61,2,1.22,f'{name}loc{x}')
for hx in [-13,13]:
    for hy in [-13,13]:
        # Conservative stepped cover of the full radius-3.2 mm head circle.
        # Adjacent strips meet without overlap or gaps, preserving NoOverlap2D.
        for y0 in range(-320,320,40):
            near=0 if y0<=0<=y0+40 else min(abs(y0),abs(y0+40))
            half=math.ceil(math.sqrt(320**2-near**2))
            xs.append(model.new_fixed_size_interval_var(hx*scale-half,2*half,f'hx{hx}{hy}{y0}'))
            ys.append(model.new_fixed_size_interval_var(hy*scale+y0,40,f'hy{hx}{hy}{y0}'))
            if telemetry_bottom:
                bx.append(model.new_fixed_size_interval_var(hx*scale-half,2*half,f'bhx{hx}{hy}{y0}'))
                by.append(model.new_fixed_size_interval_var(hy*scale+y0,40,f'bhy{hx}{hy}{y0}'))
for name,poly in local.items():
    p=placement[name]; ox,oy,pr=p['pcbX'],p['pcbY'],p['pcbRotation']
    if name in fixed:
        a,b,c,d=translate(rotate(poly,pr,origin=(0,0)),xoff=ox,yoff=oy).bounds
        xs.append(model.new_fixed_size_interval_var(math.floor(a*scale),math.ceil((c-a)*scale),name+'fx'))
        ys.append(model.new_fixed_size_interval_var(math.floor(b*scale),math.ceil((d-b)*scale),name+'fy'))
        anchors[name]=(round(ox*scale),round(oy*scale));continue
    ax=model.new_int_var(-1700,1700,name+'ax');ay=model.new_int_var(-1700,1700,name+'ay')
    gx=model.new_int_var(-340,340,name+'gridx');gy=model.new_int_var(-340,340,name+'gridy')
    model.add(ax==5*gx);model.add(ay==5*gy)
    options=[]; active=[]
    for r in [pr,(pr+90)%360]:
        a,b,c,d=rotate(poly,r,origin=(0,0)).bounds
        enabled=model.new_bool_var(name+str(r));active.append(enabled)
        left=model.new_int_var(-1700,1700,name+str(r)+'left');bottom=model.new_int_var(-1700,1700,name+str(r)+'bottom')
        w=math.ceil((c-a)*scale)+4;h=math.ceil((d-b)*scale)+4
        model.add(left==ax+round(a*scale)-2);model.add(bottom==ay+round(b*scale)-2)
        model.add(left>=round(-boundary*scale)).only_enforce_if(enabled)
        model.add(bottom>=round(-boundary*scale)).only_enforce_if(enabled)
        model.add(left+w<=round(boundary*scale)).only_enforce_if(enabled)
        model.add(bottom+h<=round(boundary*scale)).only_enforce_if(enabled)
        tx,ty=(bx,by) if name in bottom_names else (xs,ys)
        tx.append(model.new_optional_fixed_size_interval_var(left,w,enabled,name+str(r)+'x'))
        ty.append(model.new_optional_fixed_size_interval_var(bottom,h,enabled,name+str(r)+'y'))
        objective.append(enabled*(0 if r==pr else 20));options.append(r)
    model.add_exactly_one(active)
    dx=model.new_int_var(0,4000,name+'dx');dy=model.new_int_var(0,4000,name+'dy')
    model.add_abs_equality(dx,ax-round(ox*scale));model.add_abs_equality(dy,ay-round(oy*scale))
    objective.extend([dx,dy]);variables[name]=(ax,ay,active,options);anchors[name]=(ax,ay)
model.add_no_overlap_2d(xs,ys)
if telemetry_bottom:
    # Prevent the bottom circuitry from colliding with the motor terminal's
    # two rows of soldered pins, even while the terminal is being repositioned.
    mx,my=anchors['J_MOTOR']
    if 'J_MOTOR' in variables:
        _,_,ma,mr=variables['J_MOTOR']
    else:
        ma,mr=[model.new_constant(1)],[placement['J_MOTOR']['pcbRotation']]
    for r,en in zip(mr,ma):
        for x in [-3.81,-1.27,1.27,3.81]:
            for y in [-2.54,2.54]:
                angle=math.radians(r);dx=x*math.cos(angle)-y*math.sin(angle);dy=x*math.sin(angle)+y*math.cos(angle)
                ix=model.new_int_var(-2000,2000,f'motor{x}{y}{r}x');iy=model.new_int_var(-2000,2000,f'motor{x}{y}{r}y')
                model.add(ix==mx+round((dx-1.1)*scale));model.add(iy==my+round((dy-1.1)*scale))
                bx.append(model.new_optional_fixed_size_interval_var(ix,220,en,f'motor{x}{y}{r}bx'))
                by.append(model.new_optional_fixed_size_interval_var(iy,220,en,f'motor{x}{y}{r}by'))
    model.add_no_overlap_2d(bx,by)

assumptions={}
def require(name):
    literal=model.new_bool_var('require_'+name)
    model.add(literal==int('--geometry-only' not in sys.argv));assumptions[literal.index]=name
    return literal

def local_to(name, x, y, limit, weight=2):
    ax,ay=anchors[name];dx=model.new_int_var(0,7000,name+'localx'+str(x));dy=model.new_int_var(0,7000,name+'localy'+str(y))
    model.add_abs_equality(dx,ax-round(x*scale));model.add_abs_equality(dy,ay-round(y*scale))
    model.add(dx+dy<=round(limit*scale)).only_enforce_if(require(name+'_local'));objective.extend([dx*weight,dy*weight])

def together(a,b,limit,weight=2):
    xa,ya=anchors[a];xb,yb=anchors[b]
    dx=model.new_int_var(0,7000,a+b+'x');dy=model.new_int_var(0,7000,a+b+'y')
    model.add_abs_equality(dx,xa-xb);model.add_abs_equality(dy,ya-yb)
    model.add(dx+dy<=round(limit*scale)).only_enforce_if(require(a+'_'+b));objective.extend([dx*weight,dy*weight])

mcupins={ports[e['source_port_id']]['pin_number']:(e['x'],e['y']) for e in baseline if e['type']=='pcb_port' and sources[components[e['pcb_component_id']]['source_component_id']]['name']=='U_MCU'}
old_mcu=next(e for e in components.values() if sources[e['source_component_id']]['name']=='U_MCU')
dx=placement['U_MCU']['pcbX']-old_mcu['center']['x'];dy=placement['U_MCU']['pcbY']-old_mcu['center']['y']
mcupins={n:(x+dx,y+dy) for n,(x,y) in mcupins.items()}
for name,pin in {'C_IO1':1,'C_IO10':10,'C_IO22':22,'C_IO33':33,'C_IO42':42,'C_IO49':49,'C_DV23':23,'C_DV50':50,'C_USB':48,'C_ADC':43,'C_VREG_IN':44,'C_VREG_OUT':45}.items():
    local_to(name,*mcupins[pin],4.5,5)
for a,b,l in [('U_BUCK','C_BOOTSTRAP',3.5),('U_BUCK','L_BUCK',7),('U_BUCK','C_BUCK_IN',7),('L_BUCK','C_BUCK_OUT1',6),('L_BUCK','C_BUCK_OUT2',6),('U_TEMP','C_TEMP',3),('U_TEMP','U_DRV',10),('U_FLASH','U_MCU',10),('U_FLASH','C_FLASH',3),('Q_BUZZER','BZ1',10),('Q_BUZZER','D_BUZZER',6)]:
    together(a,b,l)
for n in ['R_XOUT','C_XIN','C_XOUT']:together('Y_MCU',n,3,5)
for phase in ['A','B']:
    for a,b,l in [('U_I','C_I',4),('U_I','R_I',6),('R_I','C_IADC_',3),('U_I','R_SHUNT_',12)]:
        together(a+phase,b+phase,l,4)
for name in ['C_CP','C_VCP','C_VREG','C_DRV_LOGIC','R_SA','R_SB','C_REF','R_REF_H','R_REF_L','C_VM']:
    together('U_DRV',name,9,3)

model.minimize(sum(objective))
if "--feasibility-only" in sys.argv:model.clear_objective()
for name,(ax,ay,active,options) in variables.items():
    p=placement[name]
    model.add_hint(ax,round(p['pcbX']*scale));model.add_hint(ay,round(p['pcbY']*scale))
    for r,v in zip(options,active):model.add_hint(v,int(r==p['pcbRotation']))
solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=120;solver.parameters.num_search_workers=8
solver.parameters.stop_after_first_solution='--geometry-only' not in sys.argv
solver.parameters.repair_hint=False
solver.parameters.log_search_progress=True
model.export_to_file("/tmp/nema14-v2-placement-model.pbtxt")
status=solver.solve(model)
result={'solver':'CP-SAT','status':solver.status_name(status),'board_mm':[34,34],
        'original_supplier_courtyards':True,'conservative_head_circle_diameter_mm':6.4,
        'telemetry_bottom':telemetry_bottom,
        'bottom_components':sorted(bottom_names),
        'local_placement_constraints_enforced':'--geometry-only' not in sys.argv,
        'scope':'2D placement only; not routing or 3D/wire-access qualification'}
if status==cp_model.INFEASIBLE:
    result['infeasibility_core']=[assumptions.get(i,str(i)) for i in solver.sufficient_assumptions_for_infeasibility()]
if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
    for name,(ax,ay,active,options) in variables.items():
        placement[name]={'pcbX':solver.value(ax)/scale,'pcbY':solver.value(ay)/scale,
                         'pcbRotation':next(r for r,v in zip(options,active) if solver.value(v))}
        if name in bottom_names:placement[name]['layer']='bottom'
    (ROOT/'src/supplier-placement.json').write_text(json.dumps(placement,indent=2)+'\n')
    result['placements']=placement
(ROOT/'artifacts/v2/placement-screen.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='placements'}),flush=True)
if status not in [cp_model.OPTIMAL,cp_model.FEASIBLE]:raise SystemExit(1)
