"""Verify the delivered reference feedback and connector standards by physical pins."""
import hashlib,itertools,json,pathlib,re,sys
from shapely.geometry import Polygon,box
from shapely.affinity import rotate
ROOT=pathlib.Path(__file__).resolve().parents[1];p=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'artifacts/board.circuit.json';j=json.loads(p.read_text());s=json.loads((ROOT/'artifacts/final-source.circuit.json').read_text());cat=json.loads((ROOT/'src/jlcpcb-catalog.json').read_text());src={e['name']:e for e in j if e['type']=='source_component'};net={e['subcircuit_connectivity_map_key']:e['name'] for e in j if e['type']=='source_net'};ports={}
for e in j:
 if e['type']=='source_port':ports.setdefault(e['source_component_id'],{})[e['pin_number']]=e
expected={'U_TEMP':{1:'TEMP_SCL',2:'GND',3:None,4:'GND',5:'V3V3',6:'TEMP_SDA'},'BZ1':{1:'V3V3',2:'BUZZER_SINK',3:None,4:None},'Q_BUZZER':{1:'BUZZER_GATE',2:'GND',3:'BUZZER_SINK'},'D_BUZZER':{1:'V3V3',2:'BUZZER_SINK'},'D_PWR':{1:'GND',2:'PWR_LED_A'},'R_PWR_LED':{1:'V3V3',2:'PWR_LED_A'},'D_STATUS':{1:'STATUS_R_K',2:'STATUS_G_K',3:'STATUS_B_K',4:'DATA_VBUS'},'R_TEMP_SDA':{1:'TEMP_SDA',2:'V3V3'},'R_TEMP_SCL':{1:'TEMP_SCL',2:'V3V3'},'C_TEMP':{1:'V3V3',2:'GND'},'C_BUZZER':{1:'V3V3',2:'GND'},'R_BUZZER_GATE':{1:'BUZZER_PWM',2:'BUZZER_GATE'},'R_BUZZER_PD':{1:'BUZZER_GATE',2:'GND'},'J_MOTOR':{1:'A_PLUS',2:'A_MINUS',3:'B_PLUS',4:'B_MINUS',5:None,6:None}}
for color in ['R','G','B']:
 expected['Q_STATUS_'+color]={1:'GND',2:'LED_'+color,3:'STATUS_'+color+'_C'};expected['R_STATUS_'+color]={1:'STATUS_'+color+'_K',2:'STATUS_'+color+'_C'}
mcu={5:'LED_B',4:'LED_G',27:'BUZZER_PWM',37:'LED_R',38:'TEMP_SDA',39:'TEMP_SCL'} if src['U_MCU']['manufacturer_part_number']=='RP2040' else {10:'LED_R',11:'BUZZER_PWM',12:'LED_G',13:'LED_B',17:'TEMP_SCL',18:'TEMP_SDA'};expected['U_MCU']=mcu
checks=[]
for name,pins in expected.items():
 for pin,goal in pins.items():
  e=ports[src[name]['source_component_id']][pin];actual=net.get(e.get('subcircuit_connectivity_map_key'));assert actual==goal,(name,pin,actual,goal);checks.append({'component':name,'physical_pin':pin,'pin_name':e['name'],'net':actual})
for name in ['J_PD','J_DATA']:
 ps=ports[src[name]['source_component_id']]
 for e in ps.values():
  role=e['name'];goal=None
  if role.startswith('EH') or role in ['GND1','GND2']:goal='GND'
  elif role.startswith('VBUS'):goal='PD_VBUS' if name=='J_PD' else 'DATA_VBUS'
  elif role in ['CC1','CC2']:goal=('PD_' if name=='J_PD' else 'DATA_')+role
  elif role in ['DP1','DP2']:goal='USB_DP' if name=='J_DATA' else None
  elif role in ['DM1','DM2']:goal='USB_DM' if name=='J_DATA' else None
  else:assert role in ['SBU1','SBU2'],(name,'Unreviewed USB physical port',role)
  actual=net.get(e.get('subcircuit_connectivity_map_key'));assert actual==goal,(name,role,actual,goal);checks.append({'component':name,'physical_pin':e['pin_number'],'pin_name':role,'net':actual})
for name,ohms in {'R_PWR_LED':330,'R_STATUS_R':1000,'R_STATUS_G':1000,'R_STATUS_B':1000,'R_TEMP_SDA':4700,'R_TEMP_SCL':4700,'R_BUZZER_GATE':100,'R_BUZZER_PD':100000,'R_CC1':5100,'R_CC2':5100}.items():assert src[name]['resistance']==ohms,(name,'Incorrect resistor value')
for name,value in [('C_TEMP',100e-9),('C_BUZZER',10e-6)]:assert abs(src[name]['capacitance']-value)<1e-12
for name,id in {'U_TEMP':'C99269','BZ1':'C7544813','Q_BUZZER':'C20917','D_STATUS':'C458749','D_PWR':'C965799','D_BUZZER':'C478000','J_MOTOR':'C160390','J_PD':'C165948','J_DATA':'C165948'}.items():assert src[name]['supplier_part_numbers']['jlcpcb']==[id],(name,'Incorrect supplier identity')
if src['U_MCU']['manufacturer_part_number']!='RP2040':assert src['U_BUCK']['manufacturer_part_number']=='AP63203WU-7' and 'U_LDO' not in src,'Buzzer supply must use reviewed buck regulator'
# Original native land patterns/courtyards and assets; compare current saved data to compiled source.
record=lambda a,t:sorted(json.dumps(e,sort_keys=True) for e in a if e['type']==t)
for typ in ['pcb_component','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_courtyard_outline','pcb_courtyard_rect','cad_component','pcb_hole','pcb_keepout']:assert record(j,typ)==record(s,typ),typ+' differs from compiled native source'
for part in cat['parts'].values():
 path=ROOT/part['importPath'];original=pathlib.Path(str(path)+'.original');assert hashlib.sha256(original.read_bytes()).hexdigest()==part['originalImportSha256'];fp=lambda text:re.search(r'<footprint[^>]*>.*?</footprint>',text,re.S).group(0).replace(' insertionDirection="from_above"','');assert fp(path.read_text())==fp(original.read_text())
 for kind in ['obj','step']:assert hashlib.sha256((ROOT/next(f for f in part['modelFiles'] if f.endswith('.'+kind))).read_bytes()).hexdigest()==part['sha256'][kind]
pc={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};byid={e['source_component_id']:e['name'] for e in j if e['type']=='source_component'};polys={};sides={}
for e in j:
 if e['type']=='pcb_courtyard_outline':poly=Polygon([(p['x'],p['y']) for p in e['outline']])
 elif e['type']=='pcb_courtyard_rect':
  c=e['center'];poly=rotate(box(c['x']-e['width']/2,c['y']-e['height']/2,c['x']+e['width']/2,c['y']+e['height']/2),e.get('ccw_rotation',0),origin=(c['x'],c['y']))
 else:continue
 name=byid[pc[e['pcb_component_id']]['source_component_id']];polys[name]=poly;sides[name]=e.get('layer',pc[e['pcb_component_id']]['layer'])
ov=[(a,b) for a,b in itertools.combinations(polys,2) if sides[a]==sides[b] and polys[a].intersection(polys[b]).area>1e-7];assert not ov,ov
report={'passed':True,'board_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reference':json.loads((ROOT/'artifacts/reference-feedback/baseline.json').read_text())['reference_release_id'],'physical_pin_checks':checks,'TMP102_address':'0x48','TMP102_ALERT':'NC; firmware polls temperature and defines alarms','temperature_bus':'RP2040 I2C1 GPIO26/27' if src['U_MCU']['manufacturer_part_number']=='RP2040' else 'Software I2C PB7 SDA / PB6 SCL; USB and WCH debug retained','RGB_anode':'DATA_VBUS fixed programming-USB 5 V','buzzer_reset_default':'100 kohm gate-to-ground pull-down; off at reset','buzzer_flyback':'PMEG6020ELRX C478000, 60 V / 2 A reference power diode used as compatible flyback replacement','original_imported_footprints_and_courtyards_unchanged':True,'original_OBJ_and_STEP_bytes_hash_verified':True,'native_courtyard_overlap_count':0,'JST_order':['A_PLUS','A_MINUS','B_PLUS','B_MINUS'],'USB_port_roles_match_reference':True,'hardware_operation_verified':False}
(ROOT/'artifacts/reference-feedback/circuit-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('Reference feedback and connector physical pins PASS:',len(checks),'pins;',len(polys),'native courtyards')
