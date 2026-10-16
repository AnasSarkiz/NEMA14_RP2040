"""Compare the SMT JST physical terminals and actual Gerber copper flashes."""
import pathlib,json,hashlib,csv,zipfile
from gerbonara import GerberFile
from gerbonara.graphic_objects import Flash
from gerbonara.utils import MM
root=pathlib.Path(__file__).resolve().parents[1];rows=[];expected=None
for name in ['artifacts/final-source.circuit.json','artifacts/board.circuit.json','index.circuit.json']:
 raw=(root/name).read_bytes();j=json.loads(raw);s=next(e for e in j if e['type']=='source_component' and e['name']=='J_MOTOR');assert s['manufacturer_part_number']=='BM04B-SRSS-TB(LF)(SN)' and s['supplier_part_numbers']=={'jlcpcb':['C160390']}
 c=next(e for e in j if e['type']=='pcb_component' and e['source_component_id']==s['source_component_id']);assert c['layer']=='top' and not c['do_not_place'];cad=next(e for e in j if e['type']=='cad_component' and e['source_component_id']==s['source_component_id']);assert cad['model_obj_url'] and cad['model_step_url']
 pp={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};nets={e['subcircuit_connectivity_map_key']:e['name'] for e in j if e['type']=='source_net'};pads=[e for e in j if e['type']=='pcb_smtpad' and e['pcb_component_id']==c['pcb_component_id']];assert len(pads)==6 and not any(e['type']=='pcb_plated_hole' and e['pcb_component_id']==c['pcb_component_id'] for e in j)
 contacts=[]
 for p in pads:
  port=sp[pp[p['pcb_port_id']]['source_port_id']];pin=port['pin_number'];net=nets.get(port.get('subcircuit_connectivity_map_key'));assert net==(['A_PLUS','A_MINUS','B_PLUS','B_MINUS'][pin-1] if pin<=4 else None)
  contacts.append({'pin':pin,'net':net,'x':p['x'],'y':p['y'],'width':p['width'],'height':p['height']})
 contacts.sort(key=lambda p:p['pin'])
 if expected is None:expected=contacts
 assert contacts==expected, 'JST SMT coordinates differ between native source and delivered board'
 rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'pins_and_native_pads':contacts})
flashes=[o for o in GerberFile.open(root/'artifacts/manufacturing/F_Cu.gbr').objects if isinstance(o,Flash)];matches=[]
for p in expected:
 bounds=(p['x']-p['width']/2,p['y']-p['height']/2,p['x']+p['width']/2,p['y']+p['height']/2);hit=[]
 for f in flashes:
  if abs(f.x-p['x'])>2e-5 or abs(f.y-p['y'])>2e-5:continue
  (a,b),(d,e)=f.bounding_box(unit=MM)
  if max(abs(x-y) for x,y in zip(bounds,(a,b,d,e)))<2e-5:hit.append((a,b,d,e))
 assert len(hit)==1,('Missing or incorrect actual JST copper flash',p);matches.append({'pin':p['pin'],'net':p['net'],'actual_Gerber_bounds_mm':hit[0]})
cat=json.loads((root/'src/jlcpcb-catalog.json').read_text());part=cat['parts']['C160390']
for ext in ['step','obj']:
 f=root/next(f for f in part['modelFiles'] if f.endswith('.'+ext));assert hashlib.sha256(f.read_bytes()).hexdigest()==part['sha256'][ext]
report={'passed':True,'manufacturer_part_number':s['manufacturer_part_number'],'supplier_id':'C160390','mating_housing':'SHR-04V-S','pins_1_through_4':['A_PLUS','A_MINUS','B_PLUS','B_MINUS'],'source_saved_delivered_checks':rows,'actual_JST_copper_matches':matches,'actual_JST_drill_matches':[],'JST_drilled_terminals':0,'original_STEP_and_OBJ_hashes_verified':True,'rear_motor_compatibility_verified':False}
(root/'artifacts/jst-restoration/connector-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Native SMT JST and all six actual Gerber lands PASS')
