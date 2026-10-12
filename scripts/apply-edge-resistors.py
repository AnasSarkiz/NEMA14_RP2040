"""Translate complete native resistor records; rip up copper physically affected by the moved lands."""
import copy,json,pathlib,subprocess
from shapely.geometry import Point,LineString,box
root=pathlib.Path(__file__).resolve().parents[1];out=root/'artifacts/edge-resistors';plan=json.loads((out/'placement-plan.json').read_text());assert plan['moves']
meta=json.loads((out/'baseline.json').read_text());baseline=meta['baseline_git_revision'];board=json.loads(subprocess.check_output(['git','show',baseline+':artifacts/board.circuit.json'],cwd=root));fresh=json.loads(subprocess.check_output(['git','show',baseline+':artifacts/final-source.circuit.json'],cwd=root))
mov={e['pcb_component_id']:e for e in plan['moves']};names={e['reference'] for e in plan['moves']}
src={e['source_component_id']:e for e in board if e['type']=='source_component'};cs={e['pcb_component_id']:e for e in board if e['type']=='pcb_component'};sp={e['source_port_id']:e for e in board if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in board if e['type']=='pcb_port'}
def net(p):return sp[pp[p['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key')
def shift(e,m):
 angle=m.get('angle_delta',0);old=m['old_center'];new=m['new_center'];theta=angle*3.141592653589793/180;co,si=round(__import__('math').cos(theta)),round(__import__('math').sin(theta))
 def q(p):
  x,y=p['x']-old['x'],p['y']-old['y'];p['x']=new['x']+co*x-si*y;p['y']=new['y']+si*x+co*y
 if 'x' in e and 'y' in e:q(e)
 for k in ['center','anchor_position','position']:
  if k in e:q(e[k])
 for k in ['outline','route','points']:
  for p in e.get(k,[]):q(p)
 if angle%180:
  if 'width' in e and 'height' in e:e['width'],e['height']=e['height'],e['width']
 if e['type']=='pcb_component':e['rotation']=m['rotation'];e['display_offset_x']=new['x'];e['display_offset_y']=new['y']
 if e['type']=='cad_component':e['rotation']['z']=(e['rotation']['z']+angle)%360
 if e['type']=='pcb_silkscreen_text':e['ccw_rotation']=(e.get('ccw_rotation',0)+angle)%360
for records in [board,fresh]:
 for e in records:
  m=mov.get(e.get('pcb_component_id'))
  if m and (e['type'].startswith('pcb_') or e['type']=='cad_component'):shift(e,m)
place=json.loads(subprocess.check_output(['git','show',baseline+':src/supplier-placement.json'],cwd=root))
for m in plan['moves']:place[m['reference']]['pcbX']=m['new_center']['x'];place[m['reference']]['pcbY']=m['new_center']['y'];place[m['reference']]['pcbRotation']=m['rotation']
old=json.loads(subprocess.check_output(['git','show',baseline+':artifacts/board.circuit.json'],cwd=root));oldpads=[e for e in old if e['type']=='pcb_smtpad' and e.get('pcb_component_id') in mov];newpads=[e for e in board if e['type']=='pcb_smtpad' and e.get('pcb_component_id') in mov];changedports={p['pcb_port_id'] for p in oldpads}
def geom(p):return box(p['x']-p['width']/2,p['y']-p['height']/2,p['x']+p['width']/2,p['y']+p['height']/2)
kept=[];removed=[]
for e in board:
 t=e['type'];hit=False
 if t=='pcb_copper_pour':continue
 if t=='pcb_trace':
  hit=bool(set(e.get('pcb_port_ids',[]))&changedports)
  for a,b in zip(e['route'],e['route'][1:]):
   if hit:break
   if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
   line=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
   hit=any(p['layer']==a['layer'] and net(p)==e.get('subcircuit_connectivity_map_key') and line.intersects(geom(p)) for p in oldpads) or any(p['layer']==a['layer'] and net(p)!=e.get('subcircuit_connectivity_map_key') and line.distance(geom(p))<.155 for p in newpads)
 elif t=='pcb_via':
  line=Point(e['x'],e['y']).buffer(e['outer_diameter']/2)
  hit=any(line.distance(geom(p))<(.004 if net(p)==e.get('subcircuit_connectivity_map_key') else .155) for p in newpads)
 if hit:removed.append({'type':t,'id':e.get(t+'_id'),'net_key':e.get('subcircuit_connectivity_map_key')})
 else:kept.append(e)
for t in ['source_component','source_port','source_net','source_trace']:
 assert [e for e in old if e['type']==t]==[e for e in kept if e['type']==t],t+' electrical records changed'
(root/'src/supplier-placement.json').write_text(json.dumps(place,indent=2)+'\n');(root/'artifacts/final-source.circuit.json').write_text(json.dumps(fresh,indent=2)+'\n');(root/'artifacts/board.circuit.json').write_text(json.dumps(kept,indent=2)+'\n')
receipt={'baseline_git_revision':baseline,'moved_resistors':sorted(names),'native_footprints_courtyards_models_translated_without_resizing':True,'electrical_source_identical':True,'removed_physically_affected_copper':removed,'retained_trace_records':sum(e['type']=='pcb_trace' for e in kept),'retained_vias':sum(e['type']=='pcb_via' for e in kept),'ground_pours_require_refill':True}
(out/'translation-and-ripup.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Moved',len(names),'native resistor footprints; ripped up',len(removed),'affected copper records; retained',receipt['retained_trace_records'],'traces')
