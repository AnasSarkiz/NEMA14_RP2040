"""Import freerouting's SES with its declared units; preserve actual pad geometry."""
import json,pathlib,re,math,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
prefix=sys.argv[1] if len(sys.argv)>1 else ''
ses=prefix+'-board.ses' if prefix else 'board.ses'
mapfile=prefix+'-map.json' if prefix else 'freerouting-map.json'
outfile=prefix+'.circuit.json' if prefix else 'board.circuit.json'
def parse(s):
 toks=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s);stack=[];out=[]
 for t in toks:
  if t=='(': stack.append([])
  elif t==')':
   v=stack.pop()
   (stack[-1] if stack else out).append(v)
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 if stack:raise ValueError('Truncated SES file')
 return out[0]
def children(n,tag):return [c for c in n if isinstance(c,list) and c and c[0]==tag]
s=parse((ROOT/'artifacts'/ses).read_text());routes=children(s,'routes')[0];res=children(routes,'resolution')[0]
assert res[1]=='um';scale=1000*float(res[2])
inputfile=ROOT/'artifacts'/(prefix+'-unrouted.circuit.json')
if not prefix or not inputfile.exists():inputfile=ROOT/'artifacts/unrouted.circuit.json'
j=json.loads(inputfile.read_text())
j=[e for e in j if e['type'] not in ['pcb_trace','pcb_via','pcb_copper_pour'] and not e['type'].endswith('_error')]
meta=json.loads((ROOT/'artifacts'/mapfile).read_text());netids=meta['netids']
sourceports={e['source_port_id']:e for e in j if e['type']=='source_port'};ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'}
netkeys=meta['netkeys']
for n in set(x['net'] for x in meta['pinmap'].values()):
 if n.startswith('SIGNAL_'):
  k=next(p.get('subcircuit_connectivity_map_key') for p in sourceports.values() if p.get('subcircuit_connectivity_map_key','').endswith('_'+n[7:]));netkeys[n]=k
traceids={}
for e in j:
 if e['type']=='source_trace' :traceids[e.get('subcircuit_connectivity_map_key')]=e['source_trace_id']
pads=[e for e in j if e['type'] in ['pcb_smtpad','pcb_plated_hole']]
def endpoint(x,y,key):
 from shapely.geometry import Point,Polygon
 for p in pads:
  pp=ports.get(p.get('pcb_port_id'),{});source=sourceports.get(pp.get('source_port_id'),{})
  if source.get('subcircuit_connectivity_map_key')!=key:continue
  if p.get('shape')=='polygon':
   if Polygon([(v['x'],v['y']) for v in p['points']]).buffer(.01).covers(Point(x,y)):return p.get('pcb_port_id')
   continue
  w=p.get('width',p.get('outer_width',p.get('outer_diameter',p.get('radius',0)*2)));h=p.get('height',p.get('outer_height',p.get('outer_diameter',p.get('radius',0)*2)))
  if abs(p.get('ccw_rotation',0)%180-90)<.01:w,h=h,w
  if abs(x-p['x'])<=w/2+.01 and abs(y-p['y'])<=h/2+.01:return p.get('pcb_port_id')
 return None
count=0;vcount=0
for net in children(children(routes,'network_out')[0],'net'):
 name=net[1];key=netkeys.get(name);netid=netids.get(name)
 if name.startswith('NC_'):continue
 for wire in children(net,'wire'):
  path=children(wire,'path')[0];layer={'F.Cu':'top','In2.Cu':'inner2','B.Cu':'bottom'}[path[1]];width=float(path[2])/scale;coords=list(map(float,path[3:]));assert len(coords)%2==0
  route=[{'route_type':'wire','x':coords[i]/scale,'y':coords[i+1]/scale,'width':width,'layer':layer} for i in range(0,len(coords),2)]
  if len(route)<2:continue
  count+=1;elem={'type':'pcb_trace','pcb_trace_id':f'freerouted_trace_{count}','route':route,'subcircuit_id':'subcircuit_source_group_0'}
  if key:elem['subcircuit_connectivity_map_key']=key
  if netid:elem['source_net_id']=netid
  if key in traceids:elem['source_trace_id']=traceids[key]
  for point,tag in [(route[0],'start_pcb_port_id'),(route[-1],'end_pcb_port_id')]:
   pid=endpoint(point['x'],point['y'],key) if layer=='top' else None
   if pid:point[tag]=pid
  elem['pcb_port_ids']=list({point[k] for point in route for k in ['start_pcb_port_id','end_pcb_port_id'] if k in point})
  j.append(elem)
 for via in children(net,'via'):
  vcount+=1;elem={'type':'pcb_via','pcb_via_id':f'freerouted_via_{vcount}','x':float(via[2])/scale,'y':float(via[3])/scale,'hole_diameter':(.25 if via[1]=='via500' else .3),'outer_diameter':(.5 if via[1]=='via500' else .6),'layers':['top','bottom'],'from_layer':'top','to_layer':'bottom','subcircuit_id':'subcircuit_source_group_0','subcircuit_connectivity_map_key':key}
  if netid:elem['source_net_id']=netid
  if key in traceids:elem['source_trace_id']=traceids[key]
  j.append(elem)
# Make layer transitions explicit at true exposed-pad endpoints. SES stores vias separately.
for t in meta['thermalVias']:
 for e in j:
  if e['type']=='pcb_trace' and e.get('source_net_id')==netids['GND']:
   route=e['route'];pt=route[0]
   if pt['layer']=='bottom' and math.hypot(pt['x']-t['x'],pt['y']-t['y'])<.01:
    pid=endpoint(t['x'],t['y'],netkeys['GND'])
    top={'route_type':'wire','x':t['x'],'y':t['y'],'layer':'top','width':pt['width']}
    if pid:top['start_pcb_port_id']=pid
    e['route']=[top,{'route_type':'via','x':t['x'],'y':t['y'],'from_layer':'top','to_layer':'bottom','via_diameter':(.5 if prefix else .6),'via_hole_diameter':(.25 if prefix else .3)}]+route
# Thermal vias are explicit engineering choices and permitted only inside grounded exposed pads.
for t in meta['thermalVias']:
 if not any(e['type']=='pcb_via' and math.hypot(e['x']-t['x'],e['y']-t['y'])<.01 for e in j):
  vcount+=1;j.append({'type':'pcb_via','pcb_via_id':f'freerouted_via_{vcount}','x':t['x'],'y':t['y'],'hole_diameter':(.25 if prefix else .3),'outer_diameter':(.5 if prefix else .6),'layers':['top','bottom'],'from_layer':'top','to_layer':'bottom','source_net_id':netids['GND'],'subcircuit_id':'subcircuit_source_group_0','subcircuit_connectivity_map_key':netkeys['GND']})
if prefix and (ROOT/'artifacts'/(prefix+'-seeds.circuit.json')).exists():
 seeds=json.loads((ROOT/'artifacts'/(prefix+'-seeds.circuit.json')).read_text())
 j.extend(e for e in seeds if e['type'] in ['pcb_trace','pcb_via'])
if next(e for e in j if e['type']=='pcb_board')['num_layers']==4:
 for e in j:
  if e['type']=='pcb_via':e['layers']=['top','inner1','inner2','bottom']
for e in j:
 if e['type']=='pcb_board':e['is_via_in_pad_allowed']=True
for e in j:
 if e['type']=='pcb_via':e['tented_on_top']=True;e['tented_on_bottom']=True
(ROOT/'artifacts'/outfile).write_text(json.dumps(j,indent=2)+'\n')
print(f'Imported {count} traces and {vcount} vias. Declared SES scale: {scale:g} units/mm.')
