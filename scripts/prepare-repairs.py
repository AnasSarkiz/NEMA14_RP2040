"""Open MCU escape corridors and reserve explicit inner QFN fanouts."""
import pathlib,json,math
ROOT=pathlib.Path(__file__).resolve().parents[1];path=ROOT/'artifacts/board.circuit.json';j=json.loads((ROOT/'artifacts/freerouted-before-repairs.circuit.json').read_text())
src={e['source_component_id']:e for e in j if e['type']=='source_component'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};comp={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'};traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
# This ENABLE_N vertical blocks both missing STEP and DIR top escapes.
e=next(e for e in j if e.get('pcb_trace_id')=='freerouted_trace_383');assert nets[e['subcircuit_connectivity_map_key']]['name']=='ENABLE_N';j.remove(e)
for tid in ['freerouted_trace_374','freerouted_trace_375','freerouted_trace_378']:
 e=next(e for e in j if e.get('pcb_trace_id')==tid);assert nets[e['subcircuit_connectivity_map_key']]['name']=='SLEEP';j.remove(e)
e=next(e for e in j if e.get('pcb_via_id')=='freerouted_via_51');assert nets[e['subcircuit_connectivity_map_key']]['name']=='SLEEP';j.remove(e)
# Rebuild the incomplete 1.1V core rail, which obstructed the fixed clock pins.
j[:]=[e for e in j if not(e['type'] in ['pcb_trace','pcb_via'] and nets.get(e.get('subcircuit_connectivity_map_key'),{}).get('name')=='V1V1')]
for tid,netname in [('freerouted_trace_253','V3V3'),('freerouted_trace_254','V3V3'),('freerouted_trace_255','V3V3'),('freerouted_trace_272','V3V3'),('freerouted_trace_62','GND'),('freerouted_trace_321','QSPI_SD3'),('freerouted_trace_322','QSPI_SD3'),('freerouted_trace_373','SLEEP')]:
 e=next(e for e in j if e.get('pcb_trace_id')==tid);assert nets[e['subcircuit_connectivity_map_key']]['name']==netname;j.remove(e)
e=next(e for e in j if e.get('pcb_via_id')=='freerouted_via_31');assert nets[e['subcircuit_connectivity_map_key']]['name']=='V3V3';j.remove(e)
j[:]=[e for e in j if not(e['type'] in ['pcb_trace','pcb_via'] and nets.get(e.get('subcircuit_connectivity_map_key'),{}).get('name') in ['SWDIO','RUN','QSPI_SD3'])]
# Replace the cramped USB DP dogleg with a shorter left-hand trunk.
for tid in ['freerouted_trace_333','freerouted_trace_334','freerouted_trace_335']:
 e=next(e for e in j if e.get('pcb_trace_id')==tid);assert nets[e['subcircuit_connectivity_map_key']]['name']=='MCU_DP';j.remove(e)
def port(cname,pname):return next(p for p in ports.values() if src[comp[p['pcb_component_id']]['source_component_id']]['name']==cname and sp[p['source_port_id']]['name']==pname)
for pname,rname,bends in [('USB_DP','R_DP',[(4.4,4.15),(4.48,4.35),(4.48,4.79)]),('USB_DM','R_DM',[(4.8,4.15),(5.4,4.15)])]:
 p=port('U_MCU',pname);target=port(rname,'pin1');k=sp[p['source_port_id']]['subcircuit_connectivity_map_key'];name=nets[k]['name'];route=[{'route_type':'wire','x':x,'y':y,'layer':'top','width':.16} for x,y in [(p['x'],p['y'])]+bends+[(target['x'],target['y'])]]
 route[0]['start_pcb_port_id']=p['pcb_port_id'];route[-1]['end_pcb_port_id']=target['pcb_port_id'];j.append({'type':'pcb_trace','pcb_trace_id':'manual_usb_'+name,'route':route,'source_net_id':nets[k]['source_net_id'],'source_trace_id':traces[k],'subcircuit_connectivity_map_key':k,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[p['pcb_port_id'],target['pcb_port_id']]})
# Lower the shared ADC/VREG 3V3 stub to clear the USB DM approach.
for e in j:
 if e['type']=='pcb_trace' and nets.get(e.get('subcircuit_connectivity_map_key'),{}).get('name')=='V3V3':
  for pt in e['route']:
   if pt.get('layer')=='top' and abs(pt['y']-4.1018)<.0001 and 5.5998<pt['x']<6.0001:pt['y']=3.8
# Connect TESTEN vertically to the MCU exposed ground pad, freeing the clock area.
p=port('U_MCU','TESTEN');target=port('U_MCU','GND');k=sp[p['source_port_id']]['subcircuit_connectivity_map_key'];route=[{'route_type':'wire','x':x,'y':y,'layer':'top','width':.16} for x,y in [(p['x'],p['y']),(p['x'],-1.45),(target['x'],target['y'])]];route[0]['start_pcb_port_id']=p['pcb_port_id'];route[-1]['end_pcb_port_id']=target['pcb_port_id'];j.append({'type':'pcb_trace','pcb_trace_id':'manual_TESTEN_ground','route':route,'source_net_id':nets[k]['source_net_id'],'source_trace_id':traces[k],'subcircuit_connectivity_map_key':k,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[p['pcb_port_id'],target['pcb_port_id']]})
fanouts={('U_MCU','GPIO6'):(.9,.1),('U_MCU','GPIO7'):(1.35,-.6),('U_MCU','GPIO8'):(.9,-1.2),('U_MCU','GPIO9'):(1.35,-1.8),('U_MCU','GPIO10'):(.9,-2.5),('U_MCU','XOUT'):(3,-2.5),('U_MCU','IOVDD22'):(3.6,-2),('U_MCU','DVDD23'):(4.1,-2.55),('U_MCU','SWCLK'):(4.6,-2),('U_MCU','SWDIO'):(5,-2.55),('U_MCU','RUN'):(5.5,-2),('U_MCU','QSPI_SD3'):(2.9,2.5),('U_MCU','QSPI_SD0'):(1.7,2.55),('U_MCU','QSPI_SD1'):(.8,2),('U_MCU','QSPI_SCLK'):(2.35,2),('U_MCU','DVDD50'):(3.5,2),('U_MCU','VREG_OUT'):(5.2,2.55)}
import routing_grid as grid
import heapq
# Select legal 0.5/0.25 mm fanout vias using both copper layers and all pads.
grid.j=j
records=[]
for (cname,pname),seed in fanouts.items():
 p=port(cname,pname);k=sp[p['source_port_id']]['subcircuit_connectivity_map_key'];name=nets[k]['name'];tid='reserved_fanout_'+name
 blocked=grid.obstacle(k,.16);vb=grid.obstacle(k,.16,True);start=grid.xy(p['x'],p['y'])
 if p['y']>3:bounds=(p['x']-.9,p['x']+.9,1.95,4.7)
 elif p['y']<-3:bounds=(p['x']-.9,p['x']+.9,-4.7,-1.95)
 else:bounds=(-1.5,1.65,p['y']-.8,p['y']+.8)
 def allowed(point):
  xx,yy=grid.world(point);return bounds[0]<=xx<=bounds[1] and bounds[2]<=yy<=bounds[3] and not vb[0][point[1],point[0]] and not vb[1][point[1],point[0]]
 heap=[(0,start)];best={start:0};prev={};end=None;best_score=float('inf')
 while heap:
  cost,node=heapq.heappop(heap)
  if cost!=best.get(node):continue
  if cost>best_score:break
  if allowed(node):
   wx,wy=grid.world(node);score=cost+2.5*math.hypot(wx-seed[0],wy-seed[1])/grid.STEP
   if score<best_score:end=node;best_score=score
  xx,yy=grid.world(node)
  if math.hypot(xx-p['x'],yy-p['y'])>2.5:continue
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   q=(node[0]+dx,node[1]+dy)
   if not(0<=q[0]<grid.N and 0<=q[1]<grid.N) or blocked[0][q[1],q[0]]:continue
   if dx and dy and (blocked[0][node[1],q[0]] or blocked[0][q[1],node[0]]):continue
   nc=cost+(1.41421356 if dx and dy else 1)
   if nc<best.get(q,float('inf')):best[q]=nc;prev[q]=node;heapq.heappush(heap,(nc,q))
 if end is None:
  print('No reserved fanout for',pname,'leave to selected repair',flush=True);continue
 nodes=[end]
 while nodes[-1]!=start:nodes.append(prev[nodes[-1]])
 nodes.reverse();slim=[nodes[0]]
 for i in range(1,len(nodes)-1):
  u,v,w=nodes[i-1:i+2]
  if (v[0]-u[0],v[1]-u[1])!=(w[0]-v[0],w[1]-v[1]):slim.append(v)
 slim.append(nodes[-1]);x,y=grid.world(end)
 route=[{'route_type':'wire','x':xx,'y':yy,'layer':'top','width':.16} for xx,yy in map(grid.world,slim)];route[0]['x'],route[0]['y']=p['x'],p['y'];route[0]['start_pcb_port_id']=p['pcb_port_id'];route += [{'route_type':'via','x':x,'y':y,'from_layer':'top','to_layer':'bottom','via_diameter':.5,'via_hole_diameter':.25},{'route_type':'wire','x':x,'y':y,'layer':'bottom','width':.16}]
 j.append({'type':'pcb_trace','pcb_trace_id':tid,'route':route,'source_net_id':nets[k]['source_net_id'],'source_trace_id':traces[k],'subcircuit_connectivity_map_key':k,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[p['pcb_port_id']]})
 j.append({'type':'pcb_via','pcb_via_id':tid+'_via','x':x,'y':y,'hole_diameter':.25,'outer_diameter':.5,'layers':['top','bottom'],'source_net_id':nets[k]['source_net_id'],'subcircuit_connectivity_map_key':k,'subcircuit_id':'subcircuit_source_group_0'})
 records.append({'connection':cname+'.'+pname,'net':name,'via':[x,y],'route':route});print(pname,'reserved via',x,y,flush=True)
path.write_text(json.dumps(j,indent=2)+'\n');(ROOT/'artifacts/reserved-fanouts.json').write_text(json.dumps(records,indent=2)+'\n')
