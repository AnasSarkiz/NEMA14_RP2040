import ctypes,hashlib,pathlib,subprocess,numpy as np
source=pathlib.Path(__file__).with_suffix('.cpp')
library=pathlib.Path('/tmp')/('nema14-grid-'+hashlib.sha256(source.read_bytes()).hexdigest()[:16]+'.so')
if not library.exists():subprocess.run(['g++','-O3','-shared','-fPIC',str(source),'-o',str(library)],check=True)
lib=ctypes.CDLL(str(library));fun=lib.fast_route
ptr=ctypes.c_void_p
fun.argtypes=[ctypes.c_int,ctypes.c_int,ptr,ptr,ptr,ptr,ptr,ptr,ctypes.c_int,ptr,ctypes.c_double,ctypes.c_double,ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_int,ptr,ctypes.c_int,ptr];fun.restype=ctypes.c_int

def route(wire,soft,vias,existing,distance,starts,goals,weight,softcost,phase,layers,limit=5000000,inner_cost=1):
 assert 1<=inner_cost<=50
 n=wire[0].shape[0];plane=n*n;wire=np.ascontiguousarray(wire,dtype=np.uint8);soft=np.ascontiguousarray(soft,dtype=np.uint8);viafree=np.ascontiguousarray(np.logical_not(np.logical_or.reduce(vias)),dtype=np.uint8);old=np.zeros((n,n),dtype=np.uint8)
 for x,y in existing:old[y,x]=1
 h=np.ascontiguousarray(distance,dtype=np.float64);ss=np.array([z*plane+y*n+x for x,y,z in starts],dtype=np.int32);goal=np.zeros(wire.shape,dtype=np.uint8)
 for x,y,z in goals:goal[z,y,x]=1
 out=np.empty(plane*len(layers),dtype=np.int32);expanded=ctypes.c_int();arrays=[wire,soft,viafree,old,h,ss,goal]
 code=fun(n,len(layers),*[a.ctypes.data for a in arrays[:5]],ss.ctypes.data,len(ss),goal.ctypes.data,weight,softcost,int(phase),layers.index('inner1') if 'inner1' in layers else -1,inner_cost,limit,out.ctypes.data,len(out),ctypes.byref(expanded))
 if code<0:raise RuntimeError('Insufficient route output buffer')
 if code==0:return None,expanded.value
 return [(int(q%plane%n),int(q%plane//n),int(q//plane)) for q in out[:code]],expanded.value
