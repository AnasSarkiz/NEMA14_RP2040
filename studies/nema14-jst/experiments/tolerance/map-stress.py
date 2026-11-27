"""Exact segment ownership for all 24 existing stress findings; no threshold edits."""
from model import *
from shapely.ops import nearest_points
j=b;st={e['source_trace_id']:e.get('name','') for e in j if e['type']=='source_trace'};records={}
for e in j:
 typ=e['type']
 if typ in ['pcb_smtpad','pcb_plated_hole','pcb_via']:records[e[typ+'_id']]=[{'segment_index':None,'path':None,'terminal':next(('.'.join(k) for k,z in ports.items() if z['pcb_port_id']==e.get('pcb_port_id')),None),'nominal':g.pad_shape(e),'stress':g.pad_shape(e),'layers':e.get('layers',[e.get('layer','top')])}]
 elif typ=='pcb_trace':
  records[e['pcb_trace_id']]=[]
  for i,(a,z) in enumerate(zip(e['route'],e['route'][1:])):
   if a['route_type']==z['route_type']=='wire' and a['layer']==z['layer']:
    line=LineString([(a['x'],a['y']),(z['x'],z['y'])]);w=max(a['width'],z['width']);records[e['pcb_trace_id']].append({'segment_index':i,'path':st[e['source_trace_id']],'centerline_mm':list(line.coords),'nominal_width_mm':w,'stress_width_mm':w*1.2,'nominal':line.buffer(w/2,quad_segs=128),'stress':line.buffer(w*.6,quad_segs=128),'layers':[a['layer']]})
rows=[]
for i,f in enumerate(read('artifacts/iteration-8/width-stress-causes.json')['findings']):
 pairs=[]
 for a in records[f['a']]:
  for z in records[f['b']]:
   if f['layer'] not in set(a['layers'])&set(z['layers']):continue
   gap=a['stress'].distance(z['stress'])
   if abs(gap-f['clearance_mm'])<1e-6:
    u,v=nearest_points(a['stress'],z['stress']);pairs.append({'a':{k:v for k,v in a.items() if k not in ['nominal','stress']},'b':{k:v for k,v in z.items() if k not in ['nominal','stress']},'nominal_gap_mm':a['nominal'].distance(z['nominal']),'stress_gap_mm':gap,'nearest_stress_edges_mm':[[u.x,u.y],[v.x,v.y]]})
 assert pairs,('unmapped',i);rows.append({'finding_index':i,**f,'matching_primitive_pairs':pairs})
Path('artifacts/iteration-9/stress-segment-map.json').write_text(json.dumps({'width_multiplier_unchanged':1.2,'clearance_rule_unchanged_mm':.15,'preexisting':11,'introduced':13,'findings':rows},indent=2)+'\n');print('Mapped all24 findings including all ambiguous equal-distance primitive pairs')
