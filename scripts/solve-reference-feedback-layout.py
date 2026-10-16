import json,re,math,pathlib,subprocess,sys,itertools
from ortools.sat.python import cp_model
from shapely.geometry import Polygon,box
from shapely.affinity import rotate,translate
root=pathlib.Path(sys.argv[1]);rp='rp2040' in root.name;cat=json.loads((root/'src/jlcpcb-catalog.json').read_text());place=json.loads((root/'src/supplier-placement.json').read_text());baseline=json.loads((root/'artifacts/reference-feedback/baseline.json').read_text())['baseline_github_commit'];old=json.loads(subprocess.check_output(['git','show',baseline+':src/supplier-placement.json'],cwd=root));bjson=json.loads(subprocess.check_output(['git','show',baseline+':artifacts/board.circuit.json'],cwd=root));src={e['source_component_id']:e['name'] for e in bjson if e['type']=='source_component'};pc={e['pcb_component_id']:e for e in bjson if e['type']=='pcb_component'}
local={}
for name,id in cat['components'].items():
 s=(root/cat['parts'][id]['importPath']).read_text();m=re.search(r'<courtyardoutline outline=\{(\[.*?\])\}',s,re.S);assert m,name;local[name]=Polygon([(p['x'],p['y']) for p in json.loads(m[1])])
# Keep the existing clock and a compact, physically local MCU bypass ring.
if rp:
 frozen={'C_IO1':(-.4,4.8,180),'C_IO10':(-4.1,-1.2,90),'C_IO22':(4,-5.4,270),'C_IO49':(2.2,5.035,90),'C_DV23':(5.2,-5.38,90),'C_DV50':(1.1,5.035,90),'C_USB':(3,7.4,90),'C_ADC':(6.7,5.3,90),'C_VREG_IN':(5.2,7.4,90),'C_VREG_OUT':(4.1,7.4,90),'R_DP':(4.3,5.3,90),'R_DM':(5.5,5.3,90),'U_ESD':(13.15,8.3,0),'R_CC1':(0,10.3,90),'R_CC2':(10.4,7.5,0),'Q_STATUS_R':(9,4.8,0),'Q_STATUS_G':(12.35,4.8,0),'Q_STATUS_B':(15.7,4.8,0),'D_STATUS':(.85,7.51,0),'D_PWR':(-1.65,6,0),'R_FLASH_CS':(-2,7.2,0),'R_BOOT':(-2,8.3,0)}
 for n,(x,y,r) in frozen.items():place[n]={'pcbX':x,'pcbY':y,'pcbRotation':r}
else:frozen={}
model=cp_model.CpModel();xi=[];yi=[];vars={};fixed_polys={};scale=100
hard={'J_PD','J_DATA','J_MOTOR','U_DRV','U_MCU','C_BULK','BZ1'}|({'Y_MCU','R_XOUT','C_XIN','C_XOUT','C_IO33','C_IO42'} if rp else set())
prefs={'U_TEMP':(9.4,-10.4,0),'C_TEMP':(10.6,-11.5,0),'Q_BUZZER':(12.35,-8.5,0),'D_BUZZER':(8.7,-7.6,0),'C_BUZZER':(11,-7.5,90),'D_STATUS':(1.75,7.525,0),'D_PWR':(-1.1,6,0),'Q_STATUS_R':(9,4.8,0),'Q_STATUS_G':(12.35,4.8,0),'Q_STATUS_B':(15.7,4.8,0),'R_STATUS_R':(-1.4,7.8,90),'R_STATUS_G':(-2.8,7.8,90),'R_STATUS_B':(-4.2,7.8,90),'R_TEMP_SDA':(8,-10.9,90),'R_TEMP_SCL':(10.1,-10.9,90),'R_BUZZER_GATE':(13,-10.6,0),'R_BUZZER_PD':(15.9,-10.6,0),'U_BUCK':(-5.2,-2.1,180),'L_BUCK':(-5.5,-6.8,0),'C_BOOTSTRAP':(-3,-2,90),'C_BUCK_IN':(-7.7,1.4,90),'C_BUCK_OUT1':(-7.6,-10,0),'C_BUCK_OUT2':(-3.5,-10,0)}
objective=[]
# Bare debug/boot courtyards are fixed obstacles. Pads separately pass mount copper checks.
for e in bjson:
 if e['type']!='pcb_courtyard_rect':continue
 name=src[pc[e['pcb_component_id']]['source_component_id']];c=e['center'];poly=rotate(box(c['x']-e['width']/2,c['y']-e['height']/2,c['x']+e['width']/2,c['y']+e['height']/2),e.get('ccw_rotation',0),origin=(c['x'],c['y']))
 if name=='J_DEBUG' and rp:poly=translate(poly,xoff=.6,yoff=-7.8)
 if name=='J_BOOT':poly=translate(poly,xoff=.6,yoff=9 if rp else 9.5)
 fixed_polys[name]=poly
hard.update(frozen)
for name in hard:
 p=place[name];poly=translate(rotate(local[name],p['pcbRotation'],origin=(0,0)),xoff=p['pcbX'],yoff=p['pcbY']);fixed_polys[name]=poly
for name,poly in fixed_polys.items():
 a,b,c,d=poly.bounds;x=math.floor(a*scale+1e-6);y=math.floor(b*scale+1e-6);w=math.ceil(c*scale-1e-6)-x;h=math.ceil(d*scale-1e-6)-y;xi.append(model.new_fixed_size_interval_var(x,w,name+'_fixedx'));yi.append(model.new_fixed_size_interval_var(y,h,name+'_fixedy'))
for name in cat['components']:
 if name in hard:continue
 oldp=old.get(name);pref=(oldp['pcbX'],oldp['pcbY'],oldp['pcbRotation']) if oldp else prefs.get(name,(0,0,0));px,py,pr=pref
 if name in ['U_TEMP','C_TEMP','Q_BUZZER','D_BUZZER','C_BUZZER','D_STATUS','D_PWR']:px,py,pr=prefs[name]
 x=model.new_int_var(-1739,1739,name+'_x');y=model.new_int_var(-1739,1739,name+'_y');rot=model.new_bool_var(name+'_rot');opts=[]
 for ri,r in enumerate([pr,(pr+90)%360]):
  poly=rotate(local[name],r,origin=(0,0));a,b,c,d=poly.bounds;wa=math.ceil((c-a)*scale+.01)+2;ha=math.ceil((d-b)*scale+.01)+2;active=rot.Not() if ri==0 else rot;ix=model.new_optional_fixed_size_interval_var(x,wa,active,name+'_x'+str(r));iy=model.new_optional_fixed_size_interval_var(y,ha,active,name+'_y'+str(r));xi.append(ix);yi.append(iy);model.add(x+wa<=1740).only_enforce_if(active);model.add(y+ha<=1740).only_enforce_if(active)
  for hx in [-13,13]:
   for hy in [-13,13]:
    sides=[model.new_bool_var(name+'_head'+str(hx)+str(hy)+str(ri)+str(k)) for k in range(4)];model.add(x+wa<=round((hx-2.25)*scale)).only_enforce_if(sides[0]);model.add(x>=round((hx+2.25)*scale)).only_enforce_if(sides[1]);model.add(y+ha<=round((hy-2.25)*scale)).only_enforce_if(sides[2]);model.add(y>=round((hy+2.25)*scale)).only_enforce_if(sides[3]);model.add_bool_or(sides).only_enforce_if(active)
  dx=model.new_int_var(0,7000,name+'_dx'+str(r));dy=model.new_int_var(0,7000,name+'_dy'+str(r));model.add_abs_equality(dx,x-round((px+a)*scale));model.add_abs_equality(dy,y-round((py+b)*scale));objective.append((10 if oldp else 3)*dx*active if False else 0)
  # Conditional displacement variables preserve the chosen orientation's objective.
  cost=model.new_int_var(0,150000,name+'_cost'+str(r));model.add(cost==(dx+dy)*(10 if oldp else 3)).only_enforce_if(active);model.add(cost==0).only_enforce_if(active.Not());objective.append(cost)
  opts.append({'rotation':r,'bounds':[a,b,c,d],'width':wa,'height':ha})
 objective.append(rot*25);vars[name]=(x,y,rot,opts)
 # Sensor beside the driver, not near the USB edge.
 if name=='U_TEMP':
  model.add(x>=730 if rp else x>=340);model.add(x<=1150 if rp else x<=650);model.add(y<=-660 if rp else y<=-450);model.add(y>=-1370 if rp else y>=-1100)
hints={'U_ESD':(13.15,8.3,0),'R_CC1':(0,10.3,90),'R_CC2':(10.4,7.5,0),'C_ADC':(6.7,5.3,90),'C_DV50':(1.1,5.05,90),'R_FLASH_CS':(-.8,7.2,0),'D_STATUS':(1.75,7.525,0),'D_PWR':(-1.1,6,0),'Q_STATUS_R':(9,4.8,0),'Q_STATUS_G':(12.35,4.8,0),'Q_STATUS_B':(15.7,4.8,0),'C_BUCK_IN':(-7.75,2,90),'D_PD':(-5.5,1.75,90),'D_DATA':(-3.25,1.75,90),'C_IO10':(-3.3,-1.5,0),'C_VM':(-3.1,-3.9,90),'D_BUZZER':(13.4,-8.1,0),'U_TEMP':(9.6,-7.95,0),'C_TEMP':(7.3,-7.5,180)}
if rp:
 for n,(x,y,r,opts) in vars.items():
  if n not in hints:continue
  hx,hy,hr=hints[n];idx=next((i for i,o in enumerate(opts) if o['rotation']==hr),None)
  if idx is None:continue
  a,b,_,_=opts[idx]['bounds'];model.add_hint(x,round((hx+a)*scale));model.add_hint(y,round((hy+b)*scale));model.add_hint(r,idx)
model.add_no_overlap_2d(xi,yi)
# Compact supply groups use component anchors, not differing courtyard origins.
anchors={}
for name,(x,y,rot,opts) in vars.items():
 ax=model.new_int_var(-4000,4000,name+'_anchorx');ay=model.new_int_var(-4000,4000,name+'_anchory')
 for ri,opt in enumerate(opts):
  active=rot.Not() if ri==0 else rot;a,b,_,_=opt['bounds'];model.add(ax==x-round(a*scale)).only_enforce_if(active);model.add(ay==y-round(b*scale)).only_enforce_if(active)
 anchors[name]=(ax,ay)
for a,b,limit in [('U_TEMP','C_TEMP',250),('U_BUCK','L_BUCK',650),('U_BUCK','C_BOOTSTRAP',450),('U_BUCK','C_BUCK_IN',650),('L_BUCK','C_BUCK_OUT1',650),('L_BUCK','C_BUCK_OUT2',650),('Q_BUZZER','R_BUZZER_GATE',650),('Q_BUZZER','R_BUZZER_PD',650)]:
 if a not in anchors or b not in anchors:continue
 xa,ya=anchors[a];xb,yb=anchors[b];dx=model.new_int_var(0,7000,a+b+'dx');dy=model.new_int_var(0,7000,a+b+'dy');model.add_abs_equality(dx,xa-xb);model.add_abs_equality(dy,ya-yb);model.add(dx+dy<=limit)

# MCU supply bypasses must remain local to their actual physical power pins.
old_src={e['source_component_id']:e for e in bjson if e['type']=='source_component'};old_sp={e['source_port_id']:e for e in bjson if e['type']=='source_port'}
old_mcu=next(e for e in bjson if e['type']=='pcb_component' and old_src[e['source_component_id']]['name']=='U_MCU')
delta_x=place['U_MCU']['pcbX']-old['U_MCU']['pcbX'];delta_y=place['U_MCU']['pcbY']-old['U_MCU']['pcbY']
powers={old_sp[e['source_port_id']]['pin_number']:(e['x']+delta_x,e['y']+delta_y) for e in bjson if e['type']=='pcb_port' and e['pcb_component_id']==old_mcu['pcb_component_id']}
bypass={'C_IO1':1,'C_IO10':10,'C_IO22':22,'C_IO49':49,'C_DV23':23,'C_DV50':50,'C_USB':48,'C_ADC':43,'C_VREG_IN':44,'C_VREG_OUT':45} if rp else {'C_MCU':2,'C_LOGIC':2}
assumptions={}
def constrain_anchor(name,tx,ty,limit):
 if name not in vars:return
 x,y,rot,opts=vars[name]
 condition=model.new_bool_var('local_'+name);model.add_assumption(condition);assumptions[condition.index]=name
 for ri,opt in enumerate(opts):
  active=rot.Not() if ri==0 else rot;a,b,_,_=opt['bounds'];dx=model.new_int_var(0,7000,name+'_localdx'+str(ri));dy=model.new_int_var(0,7000,name+'_localdy'+str(ri));model.add_abs_equality(dx,x-round((tx+a)*scale));model.add_abs_equality(dy,y-round((ty+b)*scale));model.add(dx+dy<=limit).only_enforce_if([active,condition])
for name,pin in bypass.items():constrain_anchor(name,*powers[pin],500 if rp else 500)
# Keep motor charge-pump, bypass, current-sense and reference parts local.
driver=next(e for e in bjson if e['type']=='pcb_component' and old_src[e['source_component_id']]['name']=='U_DRV')
dpins={old_sp[e['source_port_id']]['pin_number']:(e['x'],e['y']) for e in bjson if e['type']=='pcb_port' and e['pcb_component_id']==driver['pcb_component_id']}
for name,pin,limit in [('C_CP',4,650),('C_VCP',6,650),('C_VREG',8,550),('C_DRV_LOGIC',15,550),('C_VM',28,750),('R_SA',23,650),('R_SB',27,650),('C_REF',17,650),('R_REF_H',17,650),('R_REF_L',17,650)]:constrain_anchor(name,*dpins[pin],limit)
# Local flyback/bypass loop around the physical buzzer terminals.
constrain_anchor('Q_BUZZER',15.949815,-5.299942,800)
constrain_anchor('D_BUZZER',15.949815,-5.299942,800)
constrain_anchor('C_BUZZER',8.750185,-5.299942,600)

model.minimize(sum(objective));solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=180;solver.parameters.num_search_workers=8;solver.parameters.log_search_progress=False;solver.parameters.stop_after_first_solution=True;solver.parameters.repair_hint=True;solver.parameters.hint_conflict_limit=50000;status=solver.solve(model);print(root.name,solver.status_name(status),'objective',solver.objective_value,flush=True);print('constraint core',[assumptions.get(i,i) for i in solver.sufficient_assumptions_for_infeasibility()] if status==cp_model.INFEASIBLE else []);assert status in [cp_model.OPTIMAL,cp_model.FEASIBLE], 'Native-courtyard placement has no verified solution'
changes=[]
for name,(x,y,r,opts) in vars.items():
 opt=opts[solver.value(r)];a,b,_,_=opt['bounds'];p={'pcbX':round((solver.value(x)+1)/scale-a,6),'pcbY':round((solver.value(y)+1)/scale-b,6),'pcbRotation':opt['rotation']};place[name]=p;changes.append({'reference':name,'placement':p})
polys={**fixed_polys,**{n:translate(rotate(local[n],p['pcbRotation'],origin=(0,0)),xoff=p['pcbX'],yoff=p['pcbY']) for n,p in place.items() if n in local and n not in hard}};overlap=[(a,b) for a,b in itertools.combinations(polys,2) if polys[a].intersection(polys[b]).area>1e-6];assert not overlap,overlap
(root/'src/supplier-placement.json').write_text(json.dumps(place,indent=2)+'\n');(root/'artifacts/reference-feedback/courtyard-placement.json').write_text(json.dumps({'uses_original_JLCPCB_courtyards':True,'solver':'OR-Tools CP-SAT NoOverlap2D','status':solver.status_name(status),'overlap_count':0,'reserved_buzzer':place['BZ1'],'placements':changes,'native_CAD_and_copper_checks_still_required':True},indent=2)+'\n');print('Placed',len(polys),'complete native courtyards with zero overlaps',flush=True)
