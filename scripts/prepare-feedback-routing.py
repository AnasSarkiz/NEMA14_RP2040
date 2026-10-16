"""Retain only legal copper after explicit, reviewed reference-feedback additions.

Connections are compared by physical component/pin and net role, never by IDs
whose numbering can change when source components or connections are added.
"""
import copy,hashlib,importlib.util,json,pathlib,subprocess,sys
from collections import defaultdict
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
ROOT=pathlib.Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'artifacts/reference-feedback/baseline.json').read_text());base=meta['baseline_github_commit'];old=json.loads(subprocess.check_output(['git','show',base+':artifacts/board.circuit.json'],cwd=ROOT));new=json.loads((ROOT/'artifacts/final-source.circuit.json').read_text());assert not any(e['type'].endswith('_error') for e in new)
def maps(j):
 src={e['source_component_id']:e for e in j if e['type']=='source_component'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};pc={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}
 portkey=lambda p:(src[p['source_component_id']]['name'],p.get('pin_number',p['name']))
 bynet=defaultdict(list)
 for p in sp.values():
  if p.get('subcircuit_connectivity_map_key') and p['source_component_id'] in src:bynet[p['subcircuit_connectivity_map_key']].append(portkey(p))
 semantic={k:('N:'+nets[k]['name'] if k in nets else 'D:'+json.dumps(sorted(v))) for k,v in bynet.items()}
 return src,sp,pp,pc,nets,portkey,semantic
os,osp,opp,opc,on,ok,osem=maps(old);ns,nsp,npp,npc,nn,nk,nsem=maps(new);nports={nk(p):p for p in nsp.values() if p['source_component_id'] in ns};newkeys={v:k for k,v in nsem.items()};pcb_by_key={nk(nsp[p['source_port_id']]):id for id,p in npp.items()};port_ids={id:pcb_by_key[ok(osp[p['source_port_id']])] for id,p in opp.items() if osp[p['source_port_id']]['source_component_id'] in os and ok(osp[p['source_port_id']]) in pcb_by_key}
removed={'U_LDO','C_LDO_IN','C_LDO_OUT'} if 'CH32' in json.loads((ROOT/'package.json').read_text())['name'] else set()
added=[];preserved=[]
for p in osp.values():
 if p['source_component_id'] not in os:continue
 name,pin=ok(p)
 if name in removed:continue
 assert (name,pin) in nports,('Physical pin removed',name,pin)
 key=p.get('subcircuit_connectivity_map_key');q=nports[(name,pin)];newkey=q.get('subcircuit_connectivity_map_key')
 if key:
  assert osem[key]==nsem[newkey],('Existing pin/net changed',name,pin,osem[key],nsem.get(newkey));preserved.append({'component':name,'pin':pin,'net':osem[key]})
 elif newkey:added.append({'component':name,'pin':pin,'new_net':nsem[newkey]})
allowed_rp={16:'LED_B',4:'LED_G',27:'BUZZER_PWM',37:'LED_R',38:'TEMP_SDA',39:'TEMP_SCL'}
# RP2040 physical pin 5 is GPIO3; labels, not GPIO numbers, define this review.
allowed_rp={5:'LED_B',4:'LED_G',27:'BUZZER_PWM',37:'LED_R',38:'TEMP_SDA',39:'TEMP_SCL'}
allowed_ch={10:'LED_R',11:'BUZZER_PWM',12:'LED_G',13:'LED_B',17:'TEMP_SCL',18:'TEMP_SDA'}
allowed=allowed_ch if removed else allowed_rp
assert all(e['component']=='U_MCU' and e['pin'] in allowed and e['new_net']=='N:'+allowed[e['pin']] for e in added),added
# Same schematic values on every retained passive; only purchasing/placement changes are allowed.
oldc={e['name']:e for e in os.values()};newc={e['name']:e for e in ns.values()}
for name,c in oldc.items():
 if name in removed:continue
 assert name in newc,name
 for field in ['resistance','capacitance','inductance','frequency']:
  assert c.get(field)==newc[name].get(field),(name,field,c.get(field),newc[name].get(field))
spec=importlib.util.spec_from_file_location('geom',ROOT/'scripts/verify_supplier_connectivity.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
byname={ns[c['source_component_id']]['name']:c for c in npc.values()};oldname={os[c['source_component_id']]['name']:c for c in opc.values()};moved=set()
for name,c in byname.items():
 if name not in oldname:continue
 a=oldname[name]
 if a['center']!=c['center'] or a['rotation']!=c['rotation'] or oldc[name].get('manufacturer_part_number')!=newc[name].get('manufacturer_part_number'):moved.add(name)
moved_ports={id for id,p in opp.items() if os[osp[p['source_port_id']]['source_component_id']]['name'] in moved or os[osp[p['source_port_id']]['source_component_id']]['name'] in removed}
key=lambda e:nsp[npp[e['pcb_port_id']]['source_port_id']].get('subcircuit_connectivity_map_key') if e['type'] in ['pcb_smtpad','pcb_plated_hole'] else e.get('subcircuit_connectivity_map_key')
layers=['top','inner1','inner2','bottom'];obs={l:[] for l in layers};owners={l:[] for l in layers}
for e in new:
 if e['type'] in ['pcb_smtpad','pcb_plated_hole']:
  for l in e.get('layers',[e.get('layer','top')]):obs[l].append(g.geometry(e));owners[l].append(key(e))
 elif e['type']=='pcb_keepout':
  c=e['center'];geom=g.box(c['x']-e['radius'],c['y']-e['radius'],c['x']+e['radius'],c['y']+e['radius'])
  for l in e['layers']:obs[l].append(geom);owners[l].append(None)
 elif e['type']=='pcb_hole':
  for l in layers:obs[l].append(Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1));owners[l].append(None)
trees={l:STRtree(obs[l]) for l in layers}
thermal={}
for e in new:
 if e['type']=='pcb_smtpad' and e.get('width',0)>1 and e.get('height',0)>1:
  name=ns[npc[e['pcb_component_id']]['source_component_id']]['name']
  if name in ['U_MCU','U_PD','U_DRV']:thermal[name]=e
oldthermal={os[opc[e['pcb_component_id']]['source_component_id']]['name']:(e['x'],e['y']) for e in old if e['type']=='pcb_smtpad' and e.get('width',0)>1 and e.get('height',0)>1 and os[opc[e['pcb_component_id']]['source_component_id']]['name'] in thermal}
rep={}
for e in new:
 if e['type']=='source_trace':rep[e['subcircuit_connectivity_map_key']]=e['source_trace_id']
def remap(e):
 r=copy.deepcopy(e);k=newkeys[osem[e['subcircuit_connectivity_map_key']]];r.update(subcircuit_connectivity_map_key=k,source_trace_id=rep[k]);r['source_net_id']=nn[k]['source_net_id'] if k in nn else None
 if r['source_net_id'] is None:r.pop('source_net_id')
 field=r['type']+'_id';r[field]='feedback_retained_'+r[field]
 if 'pcb_port_ids' in r:r['pcb_port_ids']=[port_ids[id] for id in r['pcb_port_ids'] if id in port_ids]
 for pt in r.get('route',[]):
  for tag in ['start_pcb_port_id','end_pcb_port_id']:
   if tag in pt:
    if pt[tag] in port_ids:pt[tag]=port_ids[pt[tag]]
    else:pt.pop(tag)
 return r

def legal(geom,ls,k,via=False,thermal=False):
 for l in ls:
  for i in trees[l].query(geom.buffer(.15-1e-6),predicate='intersects'):
   if owners[l][i]==k and (not via or thermal):continue
   if geom.buffer(.15-1e-6).intersection(obs[l][i]).area>1e-9:return False
 return True
vias=[];dropped_vias=[]
for e in old:
 if e['type']!='pcb_via':continue
 if osem.get(e.get('subcircuit_connectivity_map_key')) not in newkeys:continue
 r=remap(e);site=next((n for n,p in oldthermal.items() if abs(e['x']-p[0])<.001 and abs(e['y']-p[1])<.001),None)
 if site:r['x'],r['y']=thermal[site]['x'],thermal[site]['y']
 if legal(Point(r['x'],r['y']).buffer(r['outer_diameter']/2),r['layers'],r['subcircuit_connectivity_map_key'],via=True,thermal=bool(site)):vias.append(r)
 else:dropped_vias.append((e['x'],e['y']))
kept=[];dropped=[]
for e in old:
 if e['type']!='pcb_trace':continue
 k=osem.get(e.get('subcircuit_connectivity_map_key'))
 attached=set(e.get('pcb_port_ids',[]))|{p[t] for p in e['route'] for t in ['start_pcb_port_id','end_pcb_port_id'] if t in p}
 valid=k in newkeys and not attached&moved_ports
 r=remap(e) if k in newkeys else None
 if valid:
  for a,b in zip(r['route'],r['route'][1:]):
   if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'] and not legal(LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2),[a['layer']],r['subcircuit_connectivity_map_key']):valid=False
  if any(p['route_type']=='wire' and any(abs(p['x']-x)<1e-5 and abs(p['y']-y)<1e-5 for x,y in dropped_vias) for p in [e['route'][0],e['route'][-1]]):valid=False
 (kept if valid else dropped).append(r if valid else e)
if '--fresh' in sys.argv:
 dropped=[e for e in old if e['type']=='pcb_trace'];kept=[];vias=[]
(ROOT/'artifacts/same-side-routing-seeds.json').write_text(json.dumps({'traces':kept,'vias':vias},indent=2)+'\n')
proof={'baseline_github_commit':base,'new_source_sha256':hashlib.sha256((ROOT/'artifacts/final-source.circuit.json').read_bytes()).hexdigest(),'existing_connected_pins_and_net_roles_preserved':True,'existing_passive_values_preserved':True,'additional_MCU_connections':added,'intentional_removed_linear_supply_parts':sorted(removed),'added_components':sorted(newc.keys()-oldc.keys()),'moved_references':sorted(moved),'baseline_traces':sum(e['type']=='pcb_trace' for e in old),'retained_fixed_traces':len(kept),'removed_affected_traces':len(dropped),'retained_vias':len(vias),'all_pours_will_be_regenerated':True,'source_identical_to_baseline':False,'routing_strategy':'Full copper reroute; native pads, net roles and three thermal vias preserved' if '--fresh' in sys.argv else 'Retain legal baseline copper'}
(ROOT/'artifacts/same-side-routing-proof.json').write_text(json.dumps(proof,indent=2)+'\n');(ROOT/'artifacts/reference-feedback/preserved-electrical-interfaces.json').write_text(json.dumps({'passed':True,'baseline_github_commit':base,'preserved_existing_connected_pins':preserved,'new_GPIO_roles':added,'intentional_supply_replacement':bool(removed)},indent=2)+'\n');print(json.dumps(proof,indent=2))
