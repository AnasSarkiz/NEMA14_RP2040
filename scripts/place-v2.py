"""Pack full catalog courtyards on the 34.5 mm V2 draft.

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
anchor_plan=json.loads((ROOT/'src/v2-placement-anchors.json').read_text()) if '--anchor-plan' in sys.argv else {}
placement.update(anchor_plan)
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
    if name.startswith('TP_'):
        half=.5 if name in ['TP_BOOT','TP_BOOT_GND'] else .7
        local[name] = box(-half,-half,half,half)

telemetry_bottom='--telemetry-bottom' in sys.argv
bottom_names={n+p for n in ['U_I','R_SHUNT_','C_I','R_I','C_IADC_'] for p in ['A','B']} if telemetry_bottom else set()
if telemetry_bottom:
    bottom_names.update(['C_IO1','C_IO10','C_IO22','C_IO33','C_IO42','C_IO49','C_DV23','C_DV50','C_USB','C_ADC','C_VREG_IN','C_VREG_OUT'])
bottom_names.update(n for n,v in placement.items() if n.startswith('TP_') and v.get('layer')=='bottom')
model = cp_model.CpModel()
scale = 100
xs,ys,objective,variables,anchors = [],[],[],{},{}
bx,by=[],[]
fixed = {'U_MCU','J_PD','J_DATA'} | set(anchor_plan)
boundary = 17.0
def obstacle(xlist,ylist,x,y,w,h,name):
    xlist.append(model.new_fixed_size_interval_var(round(x*scale),math.ceil(w*scale),name+'x'))
    ylist.append(model.new_fixed_size_interval_var(round(y*scale),math.ceil(h*scale),name+'y'))
if bottom_names:
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
def avoid_heads(name,ax,ay,gx,bounds,enabled):
    # A rectangle is clear when one of 32 supporting lines separates its entire
    # courtyard from the head circle. Integer normals use their actual length:
    # this conservatively excludes the complete circle, never an inscribed one.
    # Finite directions may reject a valid near-tangent corner (<0.016 mm), but
    # avoid the large per-X lookup encoding. Native geometry is audited again.
    a,b,c,d=bounds
    lo_x,hi_x=math.floor(a*scale),math.ceil(c*scale)
    lo_y,hi_y=math.floor(b*scale),math.ceil(d*scale)
    for hx in [-1300,1300]:
        for hy in [-1300,1300]:
            choices=[]
            for i in range(32):
                theta=2*math.pi*i/32;nx=round(1000*math.cos(theta));ny=round(1000*math.sin(theta))
                side=model.new_bool_var(f'{name}_head_{hx}_{hy}_{i}');choices.append(side)
                offset=min(nx*lo_x,nx*hi_x)+min(ny*lo_y,ny*hi_y)
                limit=math.ceil(320*math.hypot(nx,ny))
                model.add(nx*(ax-hx)+ny*(ay-hy)+offset>=limit).only_enforce_if([enabled,side])
            model.add_bool_or(choices).only_enforce_if(enabled)

for name,poly in local.items():
    p=placement[name]; ox,oy,pr=p['pcbX'],p['pcbY'],p['pcbRotation']
    if name in fixed:
        a,b,c,d=translate(rotate(poly,pr,origin=(0,0)),xoff=ox,yoff=oy).bounds
        target_x,target_y=(bx,by) if name in bottom_names else (xs,ys)
        target_x.append(model.new_fixed_size_interval_var(math.floor(a*scale),math.ceil((c-a)*scale),name+'fx'))
        target_y.append(model.new_fixed_size_interval_var(math.floor(b*scale),math.ceil((d-b)*scale),name+'fy'))
        for hx in [-13,13]:
            for hy in [-13,13]:
                gap=math.hypot(max(a-hx,0,hx-c),max(b-hy,0,hy-d))
                if gap<3.2-1e-6:raise ValueError(f'Fixed courtyard {name} intersects screw-head envelope at {(hx,hy)}: {gap:.6f} mm')
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
        avoid_heads(name+str(r),ax,ay,gx,(a,b,c,d),enabled)
        tx,ty=(bx,by) if name in bottom_names else (xs,ys)
        tx.append(model.new_optional_fixed_size_interval_var(left,w,enabled,name+str(r)+'x'))
        ty.append(model.new_optional_fixed_size_interval_var(bottom,h,enabled,name+str(r)+'y'))
        objective.append(enabled*(0 if r==pr else 20));options.append(r)
    model.add_exactly_one(active)
    dx=model.new_int_var(0,4000,name+'dx');dy=model.new_int_var(0,4000,name+'dy')
    model.add_abs_equality(dx,ax-round(ox*scale));model.add_abs_equality(dy,ay-round(oy*scale))
    objective.extend([dx,dy]);variables[name]=(ax,ay,active,options);anchors[name]=(ax,ay)
model.add_no_overlap_2d(xs,ys)
if bottom_names:
    # Prevent the bottom circuitry from colliding with the motor terminal's
    # two rows of soldered pins, even while the terminal is being repositioned.
    for name in ['J_MOTOR_A','J_MOTOR_B']:
        mx,my=anchors[name]
        if name in variables:
            _,_,ma,mr=variables[name]
        else:
            ma,mr=[model.new_constant(1)],[placement[name]['pcbRotation']]
        for r,en in zip(mr,ma):
            for x in [-.4,2.1]:
                for y in [-1.6,1.5]:
                    angle=math.radians(r);dx=x*math.cos(angle)-y*math.sin(angle);dy=x*math.sin(angle)+y*math.cos(angle)
                    ix=model.new_int_var(-2000,2000,f'{name}{x}{y}{r}x');iy=model.new_int_var(-2000,2000,f'{name}{x}{y}{r}y')
                    model.add(ix==mx+round((dx-1.1)*scale));model.add(iy==my+round((dy-1.1)*scale))
                    bx.append(model.new_optional_fixed_size_interval_var(ix,220,en,f'{name}{x}{y}{r}bx'))
                    by.append(model.new_optional_fixed_size_interval_var(iy,220,en,f'{name}{x}{y}{r}by'))
    model.add_no_overlap_2d(bx,by)

assumptions={}
def require(name):
    literal=model.new_bool_var('require_'+name)
    if '--geometry-only' in sys.argv:model.add(literal==0)
    elif '--explain-infeasible' in sys.argv:model.add_assumption(literal)
    else:model.add(literal==1)
    assumptions[literal.index]=name
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
    local_to(name,*mcupins[pin],6 if name=='C_VREG_IN' else 4.5,5)
for a,b,l in [('U_BUCK','C_BOOTSTRAP',3.5),('U_BUCK','L_BUCK',7),('U_BUCK','C_BUCK_IN',7),('L_BUCK','C_BUCK_OUT1',6),('L_BUCK','C_BUCK_OUT2',6),('U_TEMP','C_TEMP',3),('U_TEMP','U_DRV',12),('U_FLASH','U_MCU',10),('Q_BUZZER','BZ1',10),('BZ1','D_BUZZER',6)]:
    together(a,b,l)
def near_pin(child,parent,pin,limit):
    # Measure from the actual physical pin rather than the IC/crystal centre.
    old=next((e for e in components.values() if sources[e['source_component_id']]['name']==parent),None)
    if old:
        old_port=next(e for e in baseline if e['type']=='pcb_port' and e['pcb_component_id']==old['pcb_component_id'] and ports[e['source_port_id']]['pin_number']==pin)
        theta=-math.radians(old['rotation']);vx=old_port['x']-old['center']['x'];vy=old_port['y']-old['center']['y']
        lx=vx*math.cos(theta)-vy*math.sin(theta);ly=vx*math.sin(theta)+vy*math.cos(theta)
    else:
        text=(ROOT/catalog['parts'][catalog['components'][parent]]['importPath']).read_text()
        tag=next(tag for tag in re.findall(r'<smtpad\b[^>]+>',text) if 'portHints={["pin'+str(pin)+'"]}' in tag)
        lx=float(re.search(r'pcbX="([\d.eE+-]+)mm"',tag)[1]);ly=float(re.search(r'pcbY="([\d.eE+-]+)mm"',tag)[1])
    cx,cy=anchors[child];px,py=anchors[parent]
    if parent in variables:_,_,active,options=variables[parent]
    else:active,options=[model.new_constant(1)],[placement[parent]['pcbRotation']]
    required=require(child+'_near_'+parent+'_pin'+str(pin))
    for i,(en,r) in enumerate(zip(active,options)):
        theta=math.radians(r);ox=round(scale*(lx*math.cos(theta)-ly*math.sin(theta)));oy=round(scale*(lx*math.sin(theta)+ly*math.cos(theta)))
        dx=model.new_int_var(0,7000,f'{child}pin{i}dx');dy=model.new_int_var(0,7000,f'{child}pin{i}dy')
        model.add_abs_equality(dx,cx-px-ox);model.add_abs_equality(dy,cy-py-oy)
        model.add(dx+dy<=round(limit*scale)).only_enforce_if([required,en])
        cost=model.new_int_var(0,14000,f'{child}pin{i}cost');model.add(cost==dx+dy).only_enforce_if(en);model.add(cost==0).only_enforce_if(en.negated());objective.append(cost*5)
near_pin('C_XIN','Y_MCU',1,2.5)
near_pin('C_XOUT','Y_MCU',3,2.5)
near_pin('R_XOUT','U_MCU',21,3.5)
near_pin('C_FLASH','U_FLASH',8,2.5)
for phase in ['A','B']:
    together('R_I'+phase,'C_IADC_'+phase,3.8,4)
    near_pin('C_I'+phase,'U_I'+phase,5,2.5)
    near_pin('R_SHUNT_'+phase,'U_I'+phase,2,4)
    near_pin('R_SHUNT_'+phase,'U_I'+phase,3,4)
    near_pin('C_IADC_'+phase,'U_MCU',38 if phase=='A' else 39,3)
for name in ['C_CP','C_VCP','C_VREG','C_DRV_LOGIC','R_SA','R_SB','C_REF','R_REF_H','R_REF_L','C_VM']:
    together('U_DRV',name,15 if name.startswith('R_REF_') else 12 if name in ['R_SA','R_SB'] else 9,3)
for child,pin,limit in [('C_CP',4,3.5),('C_CP',5,3.5),('C_VCP',6,4.5),('C_VREG',8,4.5),('C_DRV_LOGIC',15,4.5),('C_REF',17,4.5),('C_VM',22,3.5),('R_SA',23,8),('R_SB',27,8)]:
    near_pin(child,'U_DRV',pin,limit)
local_to('C_ENCODER',1.905,-2.7051,6)
local_to('C_ENCODER_BULK',.635,-2.7051,6)

model.minimize(sum(objective))
if "--feasibility-only" in sys.argv:model.clear_objective()
for name,(ax,ay,active,options) in variables.items():
    p=placement[name]
    model.add_hint(ax,round(p['pcbX']*scale));model.add_hint(ay,round(p['pcbY']*scale))
    for r,v in zip(options,active):model.add_hint(v,int(r==p['pcbRotation']))
solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=180;solver.parameters.num_search_workers=8
solver.parameters.stop_after_first_solution='--geometry-only' not in sys.argv
solver.parameters.repair_hint=False
solver.parameters.log_search_progress=True
model.export_to_file("/tmp/nema14-v2-placement-model.pbtxt")
status=solver.solve(model)
result={'solver':'CP-SAT','status':solver.status_name(status),'board_mm':[34.5,34.5],
        'preserved_full_catalog_courtyards':True,'conservative_head_circle_diameter_mm':6.4,
        'head_check':'32 conservative supporting-line directions versus full rectangles; fixed anchors checked against exact circle',
        'telemetry_bottom':telemetry_bottom,
        'fixed_anchor_plan':bool(anchor_plan),
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
