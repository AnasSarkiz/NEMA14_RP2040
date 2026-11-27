"""Compare real placement distances without representing them as routed loops."""
from pathlib import Path
import json,sys
from model import *
current=read('artifacts/iteration-7/full-authored.circuit.json');ns=source_owner_names(current);ss={e['source_port_id']:e for e in current if e['type']=='source_port'};cp={(ns[ss[e['source_port_id']]['source_component_id']],ss[e['source_port_id']]['name']):e for e in current if e['type']=='pcb_port'}
def l1(a,z):return abs(a['x']-z['x'])+abs(a['y']-z['y'])
rows=[]
for n,p,to,pinname,label in [('D_BUZZER','anode','BZ1','_NEG','Buzzer flyback connection'),('C_BUZZER','pin1','BZ1','_POS','Buzzer bulk supply connection'),('C_BOOTSTRAP','pin1','U_BUCK','BST','Buck bootstrap'),('C_BOOTSTRAP','pin2','U_BUCK','SW','Buck switched bootstrap'),('C_TEMP','pin1','U_TEMP','V_POS','Temperature supply bypass')]:
 rows.append({'from':n+'.'+p,'to':to+'.'+pinname,'function':label,'previous_compact_pin_L1_mm':l1(ports[n,p],ports[to,pinname]),'new_pin_L1_mm':l1(cp[n,p],cp[to,pinname]),'actual_copper_loop_verified':False})
r={'distances':rows,'placement_only':True,'buzzer_auxiliary_loop_tradeoff_requires_further_layout_before_promotion':True,'not_a_proof_all_top_impossible':True};Path('artifacts/iteration-7/placement-tradeoffs.json').write_text(json.dumps(r,indent=2)+'\n');print(rows)
