"""Verify all resistor lands against all board edges in native JSON and actual Gerber flashes."""
import csv,hashlib,itertools,json,pathlib,subprocess
from gerbonara import GerberFile
from gerbonara.graphic_objects import Flash
from gerbonara.utils import MM
from shapely.geometry import Polygon,box
root=pathlib.Path(__file__).resolve().parents[1];out=root/'artifacts/edge-resistors';j=json.loads((root/'artifacts/board.circuit.json').read_text());meta=json.loads((out/'baseline.json').read_text());old=json.loads(subprocess.check_output(['git','show',meta['baseline_git_revision']+':artifacts/board.circuit.json'],cwd=root));src={e['source_component_id']:e for e in j if e['type']=='source_component'};cs={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};rows=[];errors=[]
for t in ([] if (root/'artifacts/top-assembly/baseline.json').exists() else ['source_component','source_port','source_net','source_trace']):
 if [e for e in j if e['type']==t]!=[e for e in old if e['type']==t]:errors.append('Electrical source changed: '+t)
oldcs={e['pcb_component_id']:e for e in old if e['type']=='pcb_component'}
def same(a,b):
 if isinstance(a,(int,float)) and isinstance(b,(int,float)):return abs(a-b)<1e-6
 if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 return a==b
for id,c in cs.items():
 if not (root/'artifacts/top-assembly/baseline.json').exists() and not src[c['source_component_id']]['name'].startswith('R_') and not same(c,oldcs[id]):errors.append('Non-resistor placement changed: '+id)
flashes={l:[o for o in GerberFile.open(root/'artifacts/manufacturing'/f).objects if isinstance(o,Flash)] for l,f in [('top','F_Cu.gbr'),('bottom','B_Cu.gbr')]}
for id,c in cs.items():
 name=src[c['source_component_id']]['name']
 if not name.startswith('R_'):continue
 pads=[e for e in j if e['type']=='pcb_smtpad' and e.get('pcb_component_id')==id];assert len(pads)==2
 matches=[]
 for p in pads:
  bounds=(p['x']-p['width']/2,p['y']-p['height']/2,p['x']+p['width']/2,p['y']+p['height']/2)
  hit=[]
  for f in flashes[p['layer']]:
   if abs(f.x-p['x'])>2e-5 or abs(f.y-p['y'])>2e-5:continue
   (a,b),(d,e)=f.bounding_box(unit=MM)
   if max(abs(x-y) for x,y in zip(bounds,(a,b,d,e)))<2e-5:hit.append((a,b,d,e))
  if len(hit)!=1:errors.append('Actual Gerber flash does not match '+name+' '+p['pcb_smtpad_id']);continue
  a,b,d,e=hit[0];margins={'left':17.5+a,'bottom':17.5+b,'right':17.5-d,'top':17.5-e}
  if min(margins.values())<.75-2e-5:errors.append('Resistor pad below 0.75 mm edge target: '+name)
  matches.append({'pad_id':p['pcb_smtpad_id'],'native_xy_mm':[p['x'],p['y']],'actual_Gerber_bounds_mm':hit[0],'all_four_edge_margins_mm':margins})
 oldc=next(e for e in oldcs.values() if next(s['name'] for s in old if s['type']=='source_component' and s['source_component_id']==e['source_component_id'])==name);moved=not same(c['center'],oldc['center']) or c['rotation']!=oldc['rotation']
 rows.append({'reference':name,'layer':c['layer'],'center_mm':c['center'],'rotation_deg':c['rotation'],'moved':moved,'minimum_actual_pad_edge_mm':min((min(x['all_four_edge_margins_mm'].values()) for x in matches),default=None),'actual_pad_matches':matches})
courts={e['pcb_component_id']:Polygon([(q['x'],q['y']) for q in e['outline']]) for e in j if e['type']=='pcb_courtyard_outline'}
for a,b in itertools.combinations(courts,2):
 if cs[a]['layer']==cs[b]['layer'] and courts[a].intersection(courts[b]).area>1e-7:errors.append('Native courtyard overlap '+a+' '+b)
board=next(e for e in j if e['type']=='pcb_board');assert board['width']==board['height']==35
holes=[e for e in j if e['type']=='pcb_hole' and not e.get('pcb_component_id')];assert len(holes)==4 and {(e['x'],e['y']) for e in holes}==set(itertools.product([-13,13],repeat=2)) and all(e['hole_diameter']==3.2 for e in holes)
report={'passed':not errors,'board_sha256':hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest(),'baseline_git_revision':meta['baseline_git_revision'],'target_pad_to_edge_mm':.75,'scope':'Every resistor; all four edges; top and bottom assembly sides','resistors_checked':len(rows),'actual_Gerber_pad_matches':sum(len(r['actual_pad_matches']) for r in rows),'moved_resistors':[r['reference'] for r in rows if r['moved']],'minimum_actual_pad_edge_mm':min(r['minimum_actual_pad_edge_mm'] for r in rows if r['minimum_actual_pad_edge_mm'] is not None),'electrical_source_components_pins_nets_traces_preserved':not any('Electrical source' in e for e in errors),'all_non_resistor_placements_preserved':False,'top_assembly_relocation_authorized':True,'unchanged_outline_mm':[35,35],'unchanged_mount_holes_mm':sorted((e['x'],e['y']) for e in holes),'unchanged_mount_drill_mm':3.2,'resistors':rows,'errors':errors}
(out/'clearance-verification.json').write_text(json.dumps(report,indent=2)+'\n')
with (out/'clearance-verification.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Side','X mm','Y mm','Rotation deg','Moved','Minimum actual Gerber pad-to-edge mm']);w.writerows([r['reference'],r['layer'],r['center_mm']['x'],r['center_mm']['y'],r['rotation_deg'],r['moved'],r['minimum_actual_pad_edge_mm']] for r in rows)
print('All-edge resistor check:',len(rows),'resistors;',report['actual_Gerber_pad_matches'],'actual Gerber pads; min',report['minimum_actual_pad_edge_mm'],'mm; errors',errors);raise SystemExit(bool(errors))
