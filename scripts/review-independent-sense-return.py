"""DC sense-wire / conservative single-ground-plane return screen, not a router."""
import sys,json,pathlib,hashlib,math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.ndimage import label
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from shapely import contains_xy
import verify_supplier_connectivity as g
rho=.01724 # ohm mm2/m, equivalently mOhm*mm at the mm units below.
key=next(k for k,n in g.nets.items()if n=='GND');geom=[]
for e in g.j:
 if e['type']=='pcb_copper_pour'and e['layer']=='inner1'and g.key(e)==key:
  b=e['brep_shape'];xy=lambda r:[(p['x'],p['y'])for p in r['vertices']];geom.append(Polygon(xy(b['outer_ring']),[xy(r)for r in b.get('inner_rings',[])]))
plane=unary_union(geom);assert plane.area>700
# Remove real drilled voids. Same-net via pads remain part of the conductive plane.
voids=[]
for e in g.j:
 if e['type']=='pcb_via':voids.append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2,quad_segs=64))
 elif e['type']=='pcb_hole':voids.append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2,quad_segs=64))
 elif e['type']=='pcb_plated_hole':voids.append(Point(e['x'],e['y']).buffer(e.get('hole_diameter',0)/2,quad_segs=64))
plane=plane.difference(unary_union(voids))
driver=next(p for p in g.ports.values()if g.src[g.comp[p['pcb_component_id']]['source_component_id']]=='U_DRV'and g.sp[p['source_port_id']]['name']=='EP')
sinkvia=next(v for v in g.j if v['type']=='pcb_via'and g.key(v)==key and math.hypot(v['x']-driver['x'],v['y']-driver['y'])<.01)
wire=[]
for n in ['SENSE1','SENSE2']:
 ts=[e for e in g.j if e['type']=='pcb_trace'and g.nets.get(g.key(e))==n];length=0;resistance=0
 for t in ts:
  for a,b in zip(t['route'],t['route'][1:]):
   if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']:
    assert a['layer']=='top' and a['width']>=.3 and b['width']>=.3
    l=math.dist((a['x'],a['y']),(b['x'],b['y']));length+=l;resistance+=rho*l/(min(a['width'],b['width'])*.035)
 assert not any(e['type']=='pcb_via'and g.nets.get(g.key(e))==n for e in g.j)
 wire.append({'net':n,'lengthMm':length,'widthFloorMm':.3,'resistanceAt20C_mOhm':resistance,'senseViaCount':0})
meshes=[]
for step in [.15,.10]:
 x=np.arange(-17.5+step/2,17.5,step);y=np.arange(-17.5+step/2,17.5,step);xx,yy=np.meshgrid(x,y)
 mask=contains_xy(plane,xx,yy);labs,n=label(mask);sink=(np.hypot(xx-sinkvia['x'],yy-sinkvia['y'])<=sinkvia['outer_diameter']/2)&mask
 assert sink.any();lab=int(labs[sink][0]);mask&=labs==lab;sink&=mask
 idx=np.full(mask.shape,-1,int);idx[mask]=np.arange(mask.sum());N=int(mask.sum());edges=[]
 for a,b in [(idx[:,:-1],idx[:,1:]),(idx[:-1,:],idx[1:,:])]:
  good=(a>=0)&(b>=0);edges.append((a[good],b[good]))
 ea=np.concatenate([e[0]for e in edges]);eb=np.concatenate([e[1]for e in edges]);deg=np.bincount(np.r_[ea,eb],minlength=N)
 mat=coo_matrix((np.r_[deg,-np.ones(len(ea)*2)],(np.r_[np.arange(N),ea,eb],np.r_[np.arange(N),eb,ea])),shape=(N,N)).tocsr();fixed=idx[sink];free=np.ones(N,bool);free[fixed]=False;M=mat[free][:,free];cases=[]
 for name in ['R_SA','R_SB']:
  v=next(v for v in g.j if v.get('pcb_via_id')=='independent_star_'+name);feed=(np.hypot(xx-v['x'],yy-v['y'])<=v['outer_diameter']/2)&mask;assert feed.any();rhs=np.zeros(N);rhs[idx[feed]]=1/feed.sum();solution=spsolve(M,rhs[free]);potential=np.zeros(N);potential[free]=solution
  # Sheet resistance rho/t at20C. A unit1A drive produces mV, numerically mOhm.
  spreading=float(np.mean(potential[idx[feed]]))*rho/.0175
  barrel=rho*1.6/(math.pi*.020*v['hole_diameter'])+rho*1.6/(math.pi*.020*sinkvia['hole_diameter'])
  cases.append({'shunt':name,'spreadingResistanceAt20C_mOhm':spreading,'groundBarrelsFull1p6mmConservative_mOhm':barrel,'feedCells':int(feed.sum()),'sinkCells':int(sink.sum())})
 meshes.append({'cellPitchMm':step,'conductiveCells':N,'cases':cases})
for i,row in enumerate(wire):
 values=[m['cases'][i]['spreadingResistanceAt20C_mOhm']for m in meshes];barrel=meshes[-1]['cases'][i]['groundBarrelsFull1p6mmConservative_mOhm'];row.update({'planeReturnScreenAt20C_mOhm':max(values),'groundBarrelsScreenAt20C_mOhm':barrel,'totalWirePlaneAndBarrelScreenAt20C_mOhm':row['resistanceAt20C_mOhm']+max(values)+barrel,'meshVariationPercent':100*abs(values[1]-values[0])/max(values)})
 row['screenAt125C_mOhm']=row['totalWirePlaneAndBarrelScreenAt20C_mOhm']*(1+.00393*(125-20));row['screenAt20C_percentOf240mOhmShunt']=100*row['totalWirePlaneAndBarrelScreenAt20C_mOhm']/.24/1000
report={'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest(),'method':'Finite-volume DC resistor mesh of actual inner1 GND copper minus drilled voids. Four-neighbor cells;1A distributed over shunt via annulus, zero volts at one driver EP via annulus. Only one17.5um inner plane used; other parallel planes/pins excluded. Full1.6mm lengths for both20um plated barrels screen unknown stack spacing. Cell-center mesh convergence is a screen, not a mathematically rigorous bound.','rho20_mOhm_mm':rho,'copperMinimumUm':{'outer':35,'inner':17.5,'barrel':20},'meshes':meshes,'sense':wire,'groundReferenceVia':sinkvia['pcb_via_id'],'hardwareMeasured':False,'limitations':['No pad/contact/solder resistance','No regulator/phase shared-current field or switching inductance/ground bounce','No thermal or current accuracy qualification','Cell centers approximate polygon boundaries; supplier actual stackup/plate thickness and Kelvin measurement required'],'prototypeAcceptance':'Measure effective sense/return resistance and differential ground bounce; phase peaks<=0.25A with required balance across microsteps/temperature.'}
(g.ROOT/'artifacts/engineering/independent-sense-return-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(wire,indent=2))
