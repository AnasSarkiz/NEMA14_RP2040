"""Generate native paths solely from a fresh copper-free transformed placement and named-pad topology."""
from pathlib import Path
import json,math,sys,hashlib,importlib.util
sys.path.insert(0,'scripts');from native_sources import source_owner_names
from shapely.geometry import Point
from shapely.ops import nearest_points
spec=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
p=Path(sys.argv[1]);raw=p.read_bytes();b=json.loads(raw);assert not any(e['type'] in ['pcb_trace','pcb_via'] for e in b),'Placement input must be freshly generated without copper';t=json.load(open('experiments/placement/anchor-template.json'));names=source_owner_names(b);sp={e['source_port_id']:e for e in b if e['type']=='source_port'};ports={names[sp[e['source_port_id']]['source_component_id']]+'.'+sp[e['source_port_id']]['name']:e for e in b if e['type']=='pcb_port'};co={names[e['source_component_id']]:e for e in b if e['type']=='pcb_component'};pads={e['pcb_port_id']:e for e in b if e['type']=='pcb_smtpad'}
for name,rotation in t['reference_rotations'].items():assert co[name]['rotation']==rotation,'New orientation needs a newly checked breakout topology: '+name
def pad(ref):return g.pad_shape(pads[ports[ref]['pcb_port_id']])
def xy(ref):return [ports[ref]['x'],ports[ref]['y']]
def edge(ref):c=co[ref.split('.')[0]]['center'];a,z=nearest_points(Point(c['x'],c['y']),pad(ref));return [z.x,z.y]
via=[];positions={k:xy(k) for k in ports};edges={}
for v in t['vias']:
 if 'star_ground_pad' in v:
  eg=pad(v['driver']+'.EP');gg=pad(v['driver']+'.'+v['star_ground_pad']);x=(eg.bounds[0]+gg.bounds[2])/2 if gg.centroid.x<eg.centroid.x else (eg.bounds[2]+gg.bounds[0])/2;y=gg.centroid.y
 else:pt=xy(v['anchor_pad']);x,y=[pt[i]+v['offset_world_mm'][i] for i in range(2)]
 via.append({'name':v['name'],'net':v['net'],'x':x,'y':y});positions[v['name']]=[x,y]
def local(comp,world):
 c=co[comp];a=math.radians(-c['rotation']);x,y=world[0]-c['center']['x'],world[1]-c['center']['y'];return {'x':x*math.cos(a)-y*math.sin(a),'y':x*math.sin(a)+y*math.cos(a)}
paths={}
for name,v in t['paths'].items():
 comp=v['anchor'].split(' > ')[0][1:];parts=[]
 for path in v['paths']:
  points=[]
  for q in path:
   if isinstance(q,str):points.append(q);continue
   if 'actual_body_facing_pad_edge' in q:world=edge(q['actual_body_facing_pad_edge']);edges[name]=world
   elif 'actual_driver_outward_pad_tip' in q:ref=q['actual_driver_outward_pad_tip'];world=[xy(ref)[0],pad(ref).bounds[1]]
   else:world=[positions[q[axis]['anchor']][i]+q[axis]['offset_mm'] for i,axis in enumerate('xy')]
   points.append(local(comp,world))
  parts.append(points)
 paths[name]={'anchor':v['anchor'],'paths':parts,'logical_terminal_pair':v['logical_terminal_pair'],'width_mm':v['width_mm']}
# Fresh native pad coordinates determine both short signal escapes; no old port IDs.
sense=[]
name='R_SA';start=xy(name+'.pin1');target=xy('U_DRV.SENSE1');row=(pad('C_VM.pin1').bounds[3]+pad('U_DRV.VBB1').bounds[1])/2
sense.append({'name':'AUTHORED_SENSE_A','from':'.R_SA > .pin1','to':'.U_DRV > .SENSE1','anchor':'.R_SA > .pin1','width_mm':.16,'paths':[['.R_SA > .pin1',local(name,[start[0],row]),local(name,[target[0]-.05,row]),'.U_DRV > .SENSE1']]})
# Route SENSE2 on inner1 to avoid crossing the actual winding-current breakout.
name='R_SB';start=xy(name+'.pin1');target=xy('U_DRV.SENSE2');driver_via=[target[0]+.399113,pad('U_DRV.VBB2').bounds[1]-.5];resistor_via=[pad('R_SB.pin1').bounds[2]+.4114949,start[1]]
via.extend([{'name':'V_SENSE_B_D','net':'SENSE2','x':driver_via[0],'y':driver_via[1]},{'name':'V_SENSE_B_R','net':'SENSE2','x':resistor_via[0],'y':resistor_via[1]}])
sense.append({'name':'AUTHORED_SENSE_B','from':'.R_SB > .pin1','to':'.U_DRV > .SENSE2','anchor':'.R_SB > .pin1','width_mm':.16,'paths':[['.R_SB > .pin1','.V_SENSE_B_R > .top'],['.V_SENSE_B_R > .inner1','.V_SENSE_B_D > .inner1'],['.V_SENSE_B_D > .top',local(name,[target[0],pad('U_DRV.SENSE2').bounds[1]]),'.U_DRV > .SENSE2']]})
returns=json.loads(json.dumps(t['returns']))
# Terminate the wide top wire on the source-facing annulus, not over the drill axis.
# The 5mm metric must also count this 0.20mm access distance to the via axis.
gb=next(v for v in via if v['name']=='V_GB')
for r in returns:
 if r['name']=='RETURN_B_TOP':r['anchor']='.R_SB > .pin2';r['paths']=[['.R_SB > .pin2',local('R_SB',[gb['x']+.2,gb['y']])]];r['via_axis_access_mm']=.2
positions.update({v['name']:[v['x'],v['y']] for v in via})
def selector_position(selector):
 owner,pin=selector[1:].split(' > .');return positions[owner] if owner.startswith('V_') else xy(owner+'.'+pin)
def world_from_local(comp,q):
 c=co[comp];a=math.radians(c['rotation']);return [c['center']['x']+q['x']*math.cos(a)-q['y']*math.sin(a),c['center']['y']+q['x']*math.sin(a)+q['y']*math.cos(a)]
def anchor_local(selector,world):
 owner=selector[1:].split(' > .')[0]
 return {'x':world[0]-positions[owner][0],'y':world[1]-positions[owner][1]} if owner.startswith('V_') else local(owner,world)
def sel(ref):owner,pin=ref.split('.');return '.'+owner+' > .'+pin
fragments=[]
for group,r in list(paths.items())+[(v['name'],v) for v in returns]+[(v['name'],v) for v in sense]:
 oldcomp=r.get('anchor',r.get('from','')).split(' > ')[0][1:]
 for i,path in enumerate(r['paths']):
  assert isinstance(path[0],str);start=path[0];clipped=not isinstance(path[-1],str)
  target=(sel(next(x for x in r['logical_terminal_pair'] if x.startswith('U_DRV.'))) if group.startswith('POWER_') and group.endswith('_DRV') else r.get('to')) if clipped else path[-1]
  assert target;numeric=[q if isinstance(q,str) else anchor_local(start,world_from_local(oldcomp,q)) for q in path];mid=numeric[1:-1] if not clipped else numeric[1:]
  fragments.append({'name':group if len(r['paths'])==1 else group+'__'+str(i),'group':group,'from':start,'to':target,'anchor':start,'width_mm':r.get('width_mm',.6),'representation':'plural-clipped' if clipped else 'singular','path':mid or [start],'paths':[numeric]})
result={'fresh_placement_sha256':hashlib.sha256(raw).hexdigest(),'anchor_template_sha256':hashlib.sha256(Path('experiments/placement/anchor-template.json').read_bytes()).hexdigest(),'anchor_port_positions_mm':{k:xy(k) for k in ports if k.split('.')[0] in t['reference_rotations']},'paths':paths,'fragments':fragments,'sense_paths':sense,'vias':via,'returns':returns,'actual_pad_edges':edges,'manufacturing_qualified':False};target=Path(sys.argv[2] if len(sys.argv)>2 else 'experiments/placement/generated.json');target.write_text(json.dumps(result,indent=2)+'\n');print('Regenerated',len(paths),'logical paths from fresh physical pad anchors',result['fresh_placement_sha256'])
