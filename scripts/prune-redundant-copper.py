"""Remove redundant ordinary copper only on physically complete nets."""
import json,math,hashlib
import verify_supplier_connectivity as g
removed=[];skipped=[]
def signature(net):
 es,rs=g.groups(net);sets={}
 for e,r in zip(es,rs):
  if e.get('pcb_port_id'):sets.setdefault(r,set()).add(e['pcb_port_id'])
 return sorted(tuple(sorted(v)) for v in sets.values())
def length(t,layer=None):
 return sum(math.dist((a['x'],a['y']),(b['x'],b['y'])) for a,b in zip(t['route'],t['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'] and (layer is None or a['layer']==layer))
for net,name in g.nets.items():
 if name in ['GND','USB_DP','USB_DM','MCU_DP','MCU_DM','XIN','XOUT','XTAL_OUT']:continue
 sig=signature(net)
 if len(sig)!=1:skipped.append(name);continue
 candidates=[e for e in g.j if e['type']=='pcb_trace' and g.key(e)==net and not e['pcb_trace_id'].startswith(('usb_','oscillator_','reviewed_local_','review_escape_'))]
 for e in sorted(candidates,key=lambda t:(length(t,'inner1'),length(t)),reverse=True):
  i=g.j.index(e);g.j.pop(i)
  if signature(net)==sig:removed.append({'trace':e['pcb_trace_id'],'net':name,'length_mm':length(e),'inner1_mm':length(e,'inner1')})
  else:g.j.insert(i,e)
g.path.write_text(json.dumps(g.j,indent=2)+'\n');out=g.ROOT/'artifacts/opposite-edge/redundant-copper-pruning.json';history=json.loads(out.read_text()) if out.exists() else [];history.append({'removed':removed,'open_nets_left_untouched':skipped,'actual_pad_partitions_preserved':True,'board_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest()});out.write_text(json.dumps(history,indent=2)+'\n');print('Removed redundant traces',len(removed),'sum mm',sum(e['length_mm'] for e in removed),'inner1',sum(e['inner1_mm'] for e in removed),flush=True)
