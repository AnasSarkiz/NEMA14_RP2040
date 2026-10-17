"""Verify electrical migration, manufacturer pin mapping and preserved mechanics."""
import hashlib,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
path=ROOT/'artifacts/board.circuit.json';a=json.loads(path.read_text())
baseline_commit=subprocess.check_output(['git','rev-list','--max-parents=0','HEAD'],cwd=ROOT,text=True).strip()
old=json.loads(subprocess.check_output(['git','show',baseline_commit+':index.circuit.json'],cwd=ROOT))
src={e['name']:e for e in a if e['type']=='source_component'}
ports={e['source_port_id']:e for e in a if e['type']=='source_port'}
nets={e['subcircuit_connectivity_map_key']:e['name'] for e in a if e['type']=='source_net'}
def pin(ref,num):return next(e for e in ports.values() if e['source_component_id']==src[ref]['source_component_id'] and e['pin_number']==num)
def net(ref,num):return nets.get(pin(ref,num).get('subcircuit_connectivity_map_key'))
assert src['U_PD']['manufacturer_part_number']=='CH224A'
assert src['U_PD']['supplier_part_numbers']['jlcpcb']==['C42459160']
expected={1:'PD_VHV',6:'PD_CC2',7:'PD_CC1',8:'PD_VBUS',9:'PD_CFG',10:'PD_GOOD',11:'GND'}
assert {p:net('U_PD',p) for p in expected}==expected
assert pin('U_PD',1)['name']=='VHV'
assert pin('U_PD',2)['name']=='CFG2' and pin('U_PD',3)['name']=='CFG3'
for p in [2,3,4,5]:
    assert net('U_PD',p) is None and pin('U_PD',p).get('do_not_connect'),('Unconnected CH224A pin',p)
assert src['R_PD']['resistance']==0 and src['R_PD']['supplier_part_numbers']['jlcpcb']==['C21189']
assert {net('R_PD',1),net('R_PD',2)}=={'PD_VBUS','PD_VHV'}
assert src['R_PD_CFG']['resistance']==56000 and src['R_PD_CFG']['supplier_part_numbers']['jlcpcb']==['C25796']
assert net('R_PD_CFG',1)=='PD_CFG' and net('R_PD_CFG',2)=='GND'
assert sum(nets.get(p.get('subcircuit_connectivity_map_key'))=='PD_CFG' for p in ports.values())==2
assert src['C_PD']['capacitance']==1e-6 and src['C_PD']['max_voltage_rating']==50
assert src['C_PD']['supplier_part_numbers']['jlcpcb']==['C15849']
assert net('C_PD',1)=='PD_VHV' and net('C_PD',2)=='GND'
assert src['R_PG']['resistance']==10000 and {net('R_PG',1),net('R_PG',2)}=={'V3V3','PD_GOOD'}
mcu_pg=[p['pin_number'] for p in ports.values() if p['source_component_id']==src['U_MCU']['source_component_id'] and nets.get(p.get('subcircuit_connectivity_map_key'))=='PD_GOOD']
assert len(mcu_pg)==1,'POWER_GOOD must remain MCU readable.'
index=lambda records,typ:{e[typ+'_id']:e for e in records if e['type']==typ}
for typ in ['pcb_board','pcb_hole','pcb_keepout','pcb_component','pcb_smtpad','pcb_plated_hole','pcb_courtyard_outline']:
    before=index(old,typ);after=index(a,typ)
    for key,e in before.items():
        assert key in after,(typ,key)
        # Port label metadata may change; pad shapes and coordinates may not.
        q=after[key]
        fields=['center','x','y','width','height','rotation','ccw_rotation','layer','layers','shape','radius','outline','hole_diameter','outer_diameter']
        assert {f:e.get(f) for f in fields}=={f:q.get(f) for f in fields},('Existing geometry changed',typ,key)
oldsrc={e['source_component_id']:e for e in old if e['type']=='source_component'}
oldnets={e['subcircuit_connectivity_map_key']:e['name'] for e in old if e['type']=='source_net'}
for p in [e for e in old if e['type']=='source_port']:
    ref=oldsrc[p['source_component_id']]['name'];num=p['pin_number']
    if ref=='U_PD' and num in [2,3,9]:continue
    before=oldnets.get(p.get('subcircuit_connectivity_map_key'))
    assert net(ref,num)==('PD_VHV' if before=='PD_VDD' else before),(ref,num)
for ref,c in src.items():
    if ref in ['U_PD','R_PD','C_PD','R_PD_CFG']:continue
    prev=next(e for e in oldsrc.values() if e['name']==ref)
    for key in ['manufacturer_part_number','supplier_part_numbers','resistance','capacitance','inductance']:
        assert c.get(key)==prev.get(key),('Unrelated component changed',ref,key)
newimport=(ROOT/'imports/supplier/CH224A/CH224A.tsx').read_text()
oldimport=(ROOT/'imports/supplier/CH224K/CH224K.tsx').read_text()
assert re.findall(r'<smtpad[^>]+/>',newimport)==re.findall(r'<smtpad[^>]+/>',oldimport)
for ext in ['obj','step']:
    assert (ROOT/f'imports/supplier/CH224A/CH224A.{ext}').read_bytes()==(ROOT/f'imports/supplier/CH224K/CH224K.{ext}').read_bytes()
report={'passed':True,'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'baseline_commit':baseline_commit,
        'controller':'CH224A C42459160','voltage_before_V':15,'voltage_after_requested_V':15,'configuration':'56 kohm CFG1 to GND; CFG2/SCL and CFG3/SDA NC',
        'manufacturer_pin_map':{'1':'VHV','2':'CFG2/SCL NC','3':'CFG3/SDA NC','4':'DP NC','5':'DM NC','6':'CC2','7':'CC1','8':'VBUS','9':'CFG1','10':'PG','0':'GND EP (native supplier model uses logical pin11)'},
        'PG_mcu_physical_pin':mcu_pg[0],'PG_external_pullup_V':3.3,'PG_active_low':True,
        'existing_component_placements_and_pad_geometry_preserved':True,'board_outline_mounts_and_USB_positions_preserved':True,
        'CH224A_imported_pads_and_exposed_pad_equal_CH224K':True,'downloaded_3d_model_bytes_equal':True,
        'VHV_bypass_capacitance_uF':1,'VHV_bypass_voltage_rating_V':50,
        'VBUS_series_sense_resistor_present_in_original':False,'hardware_operation_verified':False,'manufacturing_release':False}
(ROOT/'artifacts/ch224a-migration/electrical-and-preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print('CH224A migration: pin map, 15 V configuration, PG/MCU connection, bypass rating and all existing mechanical geometry PASS.')
