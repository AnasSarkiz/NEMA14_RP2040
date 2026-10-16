"""Open MCU escape corridors and reserve explicit inner QFN fanouts."""
import pathlib,json,math
ROOT=pathlib.Path(__file__).resolve().parents[1];path=ROOT/'artifacts/fixed8-seeds.circuit.json';j=json.loads((ROOT/'artifacts/final-source.circuit.json').read_text())
src={e['source_component_id']:e for e in j if e['type']=='source_component'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};comp={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'};traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
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
fanouts={('U_MCU','GPIO6'):(.9,.1),('U_MCU','GPIO7'):(1.35,-.6),('U_MCU','GPIO8'):(.9,-1.2),('U_MCU','GPIO9'):(1.35,-1.8),('U_MCU','GPIO10'):(.9,-2.5),('U_MCU','XOUT'):(2.8,-2.6),('U_MCU','IOVDD22'):(3.35,-2),('U_MCU','DVDD23'):(4,-2.6),('U_MCU','SWCLK'):(4.55,-2),('U_MCU','SWDIO'):(5.05,-2.6),('U_MCU','RUN'):(5.5,-2),('U_MCU','QSPI_SD3'):(2.9,2.5),('U_MCU','QSPI_SD0'):(1.55,4.275),('U_MCU','QSPI_SD1'):(.8,2),('U_MCU','QSPI_SCLK'):(2.2,4.275),('U_MCU','DVDD50'):(3.5,2),('U_MCU','VREG_OUT'):(5.2,2.55)}
fanouts.update({('U_MCU','QSPI_SD2'):(1.55,2),('U_MCU','QSPI_SS'):(.8,4.275),('U_MCU','GPIO28'):(5.8,1.8),('U_MCU','GPIO29'):(6.3,2.55),('U_MCU','XIN'):(2.4,-4.275),('U_DRV','OUT1A'):(.5,-8.05),('U_DRV','OUT2A'):(-.5,-8.05),('U_DRV','SENSE1'):(1.55,-8.05),('U_DRV','SENSE2'):(-1.55,-8.05),('U_DRV','STEP'):(3.45,-12.5),('U_DRV','SLEEP'):(2.3,-14.9)})
fanouts.update({('U_DRV','OUT2B'):(-3.45,-10),('U_DRV','ENABLE_N'):(-4,-10.5),('U_DRV','CP1'):(-3.45,-11.5),('U_DRV','CP2'):(-4,-12),('U_DRV','VCP'):(-3.45,-12.5),('U_DRV','VREG'):(-2.4,-14.6),('U_DRV','MS3'):(0,-14.95),('U_DRV','VBB1'):(2.5,-8.3),('U_DRV','VBB2'):(-2.5,-8.3),('U_DRV','REF'):(4,-12),('U_DRV','VDD'):(4,-13),('U_DRV','DIR'):(3.45,-11.2),('U_DRV','OUT1B'):(3.45,-9)})

p=port('U_DRV','ENABLE_N');assert abs(p['x']+2.4)<.001 and abs(p['y']+10.5)<.001
k=sp[p['source_port_id']]['subcircuit_connectivity_map_key'];tid='reserved_fanout_U_DRV_ENABLE_N';x,y=-4,-10.7
rr=[{'route_type':'wire','x':xx,'y':yy,'width':.16,'layer':'top'} for xx,yy in [(p['x'],p['y']),(-2.95,-10.6),(-3.25,-10.625),(-3.4,-10.7),(x,y)]]
rr[0]['start_pcb_port_id']=p['pcb_port_id'];rr.extend([{'route_type':'via','x':x,'y':y,'from_layer':'top','to_layer':'bottom','via_diameter':.5,'via_hole_diameter':.25},{'route_type':'wire','x':x,'y':y,'width':.16,'layer':'bottom'}])
j.append({'type':'pcb_trace','pcb_trace_id':tid,'route':rr,'source_net_id':nets[k]['source_net_id'],'source_trace_id':traces[k],'subcircuit_connectivity_map_key':k,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[p['pcb_port_id']]})
j.append({'type':'pcb_via','pcb_via_id':tid+'_via','x':x,'y':y,'hole_diameter':.25,'outer_diameter':.5,'layers':['top','bottom'],'source_net_id':nets[k]['source_net_id'],'subcircuit_connectivity_map_key':k,'subcircuit_id':'subcircuit_source_group_0'})
predefined={'connection':'U_DRV.ENABLE_N','net':'ENABLE_N','via':[x,y],'route':rr}

fanouts.pop(('U_DRV','ENABLE_N'))
fanouts.update({('R_CC2','pin1'):(11.4,16.4),('R_USB_SENSE_H','pin1'):(3,15.7)})
fanouts.update({('J_PD','CC1'):(-8.55,5.75),('U_PD','CC1'):(.5,7.2)})
import routing_grid as grid
import heapq
# Select legal 0.5/0.25 mm fanout vias using both copper layers and all pads.
grid.j=j
records=[predefined]
for (cname,pname),seed in sorted(fanouts.items(),key=lambda kv:0 if kv[0][1] in ['SWCLK','DVDD50'] else 1):
 p=port(cname,pname);k=sp[p['source_port_id']]['subcircuit_connectivity_map_key'];name=nets[k]['name'];tid='reserved_fanout_'+cname+'_'+pname
 blocked=grid.obstacle(k,.16);vb=grid.obstacle(k,.16,True);start=grid.xy(p['x'],p['y'])
 if cname=='J_PD':bounds=(p['x'],p['x']+2,p['y']-.8,p['y']+.8)
 elif cname=='U_PD':bounds=(p['x']-1.5,p['x']+1.5,p['y']-.8,p['y']+.8)
 elif cname in ['R_CC2','R_USB_SENSE_H']:bounds=(p['x']-1.5,p['x']+1.5,p['y']-1.2,p['y']+1.2)
 elif cname=='U_DRV':
  if p['y']<-13:bounds=(p['x']-1.5,p['x']+1.5,-15.1,-13.9)
  elif p['x']<-2:bounds=(-4.6,-2.4,p['y']-.9,p['y']+.9)
  elif p['x']>2:bounds=(2.4,4.7,p['y']-.9,p['y']+1.5)
  else:bounds=(p['x']-1.5,p['x']+1.5,-9.4,-7.8)
 elif p['y']>3:bounds=(p['x']-.9,p['x']+.9,1.95,4.7)
 elif p['y']<-3:bounds=(p['x']-.9,p['x']+.9,-4.7,-1.95)
 elif p['x']>6:bounds=(5.35,8.5,p['y']-.8,p['y']+.8)
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
path.write_text(json.dumps(j,indent=2)+'\n');(ROOT/'artifacts/fixed8-fanouts.json').write_text(json.dumps(records,indent=2)+'\n')
