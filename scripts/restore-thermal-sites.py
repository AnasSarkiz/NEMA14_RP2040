"""Restore the three intended grounded EP barrels against actual native copper.
Any ordinary traces displaced by a restored barrel require rerouting and full
requalification. Never remove protected USB, oscillator or critical buck copper.
"""
import json,math,hashlib
from shapely.geometry import Point,LineString
import verify_supplier_connectivity as g
j=g.j;ground=next(k for k,n in g.nets.items() if n=='GND');sn=next(e for e in j if e['type']=='source_net' and e['name']=='GND');rows=[]
for ref in ['U_MCU','U_DRV','U_PD']:
 c=next(c for c in g.comp.values() if g.src[c['source_component_id']]==ref)
 pad=next(e for e in j if e['type']=='pcb_smtpad' and e.get('pcb_component_id')==c['pcb_component_id'] and e.get('width',0)>1 and e.get('height',0)>1)
 assert g.key(pad)==ground
 offset=json.loads((g.ROOT/'src/thermal-via-offsets.json').read_text())[ref];x,y=pad['x']+offset['x'],pad['y']+offset['y'];existing=[e for e in j if e['type']=='pcb_via' and math.dist([e['x'],e['y']],[x,y])<.001]
 if existing:
  assert len(existing)==1 and g.key(existing[0])==ground
  continue
 diameter=.5
 assert g.geometry(pad).covers(Point(x,y).buffer(diameter/2)),(ref,"Thermal land must remain inside native ground EP")
 shape=Point(x,y).buffer(diameter/2);bad=[];ripped=[]
 for e in list(j):
  typ=e['type'];same=g.key(e)==ground
  if typ in ['pcb_smtpad','pcb_plated_hole'] and not same and shape.distance(g.geometry(e))<.153:bad.append(e[typ+'_id'])
  elif typ=='pcb_via':
   distance=math.dist([x,y],[e['x'],e['y']])
   if same and distance < (.3+e['hole_diameter'])/2+.203:
    j.remove(e);ripped.append({'id':e['pcb_via_id'],'net':'GND','reason':'replace nearby ground barrel with EP barrel'})
   elif not same and shape.distance(Point(e['x'],e['y']).buffer(e['outer_diameter']/2))<.153:bad.append(e['pcb_via_id'])
  elif typ=='pcb_trace' and not same:
   hit=any(a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'] and shape.distance(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))<.153 for a,b in zip(e['route'],e['route'][1:]))
   if hit:
    uid=e['pcb_trace_id'];assert not uid.startswith(('usb_','oscillator_','reviewed_local_critical_')),uid
    j.remove(e);ripped.append({'id':uid,'net':g.nets[g.key(e)]})
 assert not bad,(ref,bad)
 port=g.ports[pad['pcb_port_id']];st=next(e for e in j if e['type']=='source_trace' and port['source_port_id'] in e.get('connected_source_port_ids',[]))
 j.append(dict(type='pcb_via',pcb_via_id='thermal_via_'+ref,x=x,y=y,outer_diameter=diameter,hole_diameter=.3,layers=['top','inner1','inner2','bottom'],from_layer='top',to_layer='bottom',source_net_id=sn['source_net_id'],source_trace_id=st['source_trace_id'],subcircuit_connectivity_map_key=ground,subcircuit_id='subcircuit_source_group_0',tented_on_top=True,tented_on_bottom=True))
 rows.append(dict(reference=ref,centre_mm=[x,y],drill_mm=.3,pad_mm=diameter,displaced_copper=ripped))
g.path.write_text(json.dumps(j,indent=2)+'\n')
(g.ROOT/'artifacts/upright-revision/thermal-restoration.json').write_text(json.dumps(dict(sites=rows,requires_full_requalification=True,board_sha256=hashlib.sha256(g.path.read_bytes()).hexdigest()),indent=2)+'\n')
print(json.dumps(rows,indent=2))
