"""Select unresolved physical pad islands requiring local ordinary-via access."""
import json
import verify_supplier_connectivity as g
rows=[];opens=[]
for net,name in g.nets.items():
 if name in ['XIN','XOUT','XTAL_OUT','CP1','CP2','USB_DP','USB_DM','MCU_DP','MCU_DM']:continue
 es,rs=g.groups(net);islands={}
 for e,r in zip(es,rs):
  if e.get('pcb_port_id'):islands.setdefault(r,[]).append(e)
 if len(islands)<=1:continue
 opens.append((name,len(islands)));main=max(islands,key=lambda r:len(islands[r]));selected=[r for r in islands if name!='GND' or r!=main]
 for r in selected:
  if name!='GND' and any(e['type']=='pcb_via' and rr==r for e,rr in zip(es,rs)):continue
  pad=min(islands[r],key=lambda e:len(e.get('port_hints',[])));p=g.ports[pad['pcb_port_id']];sp=g.sp[p['source_port_id']];width=.20 if name=='V3V3' else .30 if name in ['PD_VBUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','DATA_VBUS','LOGIC_IN','BUCK_SW'] else .16
  rows.append(dict(ref=g.src[sp['source_component_id']],role=sp['name'],width=width,radius=5))
(g.ROOT/'artifacts/opposite-edge/escape-requests.json').write_text(json.dumps(rows,indent=2)+'\n');print('Unresolved physical groups',opens);print('Local escape requests',rows)
