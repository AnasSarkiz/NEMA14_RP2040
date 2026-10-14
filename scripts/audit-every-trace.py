"""Inventory and validate every delivered trace and segment against actual source nets.

Geometry DRC, physical connectivity, width screening and independent Gerber
checks are separate required audits, not inferred from this metadata inventory.
"""
import csv,hashlib,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];path=ROOT/'artifacts/board.circuit.json';j=json.loads(path.read_text());board=next(e for e in j if e['type']=='pcb_board');layers={'top','bottom'} if board['num_layers']==2 else {'top','inner1','inner2','bottom'}
src={e['source_component_id']:e for e in j if e['type']=='source_component'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};st={e['source_trace_id']:e for e in j if e['type']=='source_trace'};sn={e['source_net_id']:e for e in j if e['type']=='source_net'};names={e['subcircuit_connectivity_map_key']:e['name'] for e in sn.values()}
for p in sp.values():
 k=p.get('subcircuit_connectivity_map_key')
 if k and k not in names:names[k]='DIRECT_'+k.rsplit('_',1)[-1]
policy=json.loads((ROOT/'src/layer-routing-policy.json').read_text());allowed_inner1=set(policy['inner1_allowed_nets'])
errors=[];rows=[];segments=[];seen=set()
def reference(pid):
 p=pp[pid];s=sp[p['source_port_id']];return src[s['source_component_id']]['name']+'.'+str(s.get('pin_number',s['name']))+' ('+s['name']+')'
for t in [e for e in j if e['type']=='pcb_trace']:
 tid=t['pcb_trace_id'];k=t.get('subcircuit_connectivity_map_key');sid=t.get('source_trace_id');issues=[]
 if tid in seen:issues.append('duplicate trace identity')
 seen.add(tid)
 if k not in names:issues.append('unknown source connectivity group')
 if sid not in st:issues.append('missing source trace identity')
 elif st[sid].get('subcircuit_connectivity_map_key')!=k:issues.append('source trace belongs to another net')
 if t.get('source_net_id') is not None:
  if t['source_net_id'] not in sn or sn[t['source_net_id']].get('subcircuit_connectivity_map_key')!=k:issues.append('source net ID belongs to another net')
 ports=set(t.get('pcb_port_ids',[]));length=0.;widths=[];used=set();route=t['route']
 for index,node in enumerate(route):
  if node['route_type'] not in ['wire','via']:issues.append('unsupported route node')
  for tag in ['start_pcb_port_id','end_pcb_port_id']:
   if tag in node:ports.add(node[tag])
   if tag in node and node[tag] in pp and node.get('layer') not in pp[node[tag]]['layers']:issues.append('port endpoint is on the wrong copper layer')
  if node['route_type']=='wire':
   if node['layer'] not in layers:issues.append('undefined copper layer')
   if node['layer']=='inner1' and names.get(k) not in allowed_inner1:issues.append('unreviewed signal net on inner1 ground plane')
   if not math.isfinite(node['width']) or node['width']<board['min_trace_width']-1e-6:issues.append('trace below board width rule')
   widths.append(node['width']);used.add(node['layer'])
 for a,b in zip(route,route[1:]):
  if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
   distance=math.hypot(b['x']-a['x'],b['y']-a['y']);length+=distance;segments.append({'trace':tid,'net':names.get(k),'layer':a['layer'],'start_mm':[a['x'],a['y']],'end_mm':[b['x'],b['y']],'length_mm':distance,'width_mm':max(a['width'],b['width'])})
 inner1_length=sum(math.hypot(b['x']-a['x'],b['y']-a['y']) for a,b in zip(route,route[1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='inner1')
 limit=policy['maximum_A_MINUS_inner1_section_mm'] if names.get(k)=='A_MINUS' else policy['maximum_clock_or_flash_inner1_section_mm'] if names.get(k,'').startswith('QSPI_') or names.get(k) in ['XIN','XOUT','XTAL_OUT'] else policy['maximum_inner1_trace_section_length_mm']
 if inner1_length>limit:issues.append('inner1 route exceeds reviewed section-length bound')
 if names.get(k)=='A_MINUS' and any(n.get('layer')=='inner1' and n.get('width',0)<policy['minimum_A_MINUS_inner1_width_mm'] for n in route):issues.append('inner1 phase bridge below reviewed width')
 if names.get(k) in ['USB_DP','USB_DM','MCU_DP','MCU_DM'] and any(n.get('layer') in ['inner1','inner2'] for n in route):issues.append('USB signal uses forbidden inner routing layer')
 for pid in ports:
  if pid not in pp:issues.append('unknown physical port '+pid)
  elif sp[pp[pid]['source_port_id']].get('subcircuit_connectivity_map_key')!=k:issues.append('trace attached to a port of another net')
 row={'trace':tid,'net':names.get(k),'source_trace':sid,'layers':sorted(used),'length_mm':length,'minimum_width_mm':min(widths) if widths else None,'physical_ports':[reference(p) for p in sorted(ports) if p in pp],'issues':sorted(set(issues))};rows.append(row)
 if issues:errors.append({'trace':tid,'issues':row['issues']})
for phase in ['A_PLUS','A_MINUS','B_PLUS','B_MINUS']:
 total=sum(r['length_mm'] for r in segments if r['net']==phase and r['layer']=='inner1')
 if total>policy['maximum_total_phase_inner1_length_mm']+1e-6:errors.append({'net':phase,'issues':['Total inner1 motor phase copper exceeds 8 mm'],'actual_mm':total})
 for r in segments:
  if r['net']==phase and r['layer']=='inner1' and r['width_mm']<policy['minimum_phase_inner1_width_mm']-1e-6:errors.append({'net':phase,'issues':['Inner1 motor phase below 0.30 mm'],'segment':r})
for t in [e for e in j if e['type']=='pcb_via']:
 k=t.get('subcircuit_connectivity_map_key')
 if k not in names:errors.append({'via':t['pcb_via_id'],'issues':['unknown source connectivity group']})
report={'passed':not errors,'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'traces_reviewed':len(rows),'wire_segments_reviewed':len(segments),'vias_reviewed':sum(e['type']=='pcb_via' for e in j),'errors':errors,'trace_inventory':rows,'segment_inventory':segments,'scope':'Every saved copper trace, wire segment, via net, source identity, attached physical port and layer; geometric DRC/physical/CAM/width reports required separately.','hardware_operation_verified':False}
out=ROOT/'artifacts/reference-feedback';out.mkdir(exist_ok=True);(out/'every-trace-review.json').write_text(json.dumps(report,indent=2)+'\n')
with (out/'every-trace-review.csv').open('w') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['Trace','Net','Source trace','Layers','Length mm','Minimum width mm','Physical ports','Issues'])
 for r in rows:w.writerow([r['trace'],r['net'],r['source_trace'],'/'.join(r['layers']),r['length_mm'],r['minimum_width_mm'],'; '.join(r['physical_ports']),'; '.join(r['issues'])])
print(json.dumps({k:report[k] for k in ['passed','traces_reviewed','wire_segments_reviewed','vias_reviewed','errors']},indent=2));raise SystemExit(bool(errors))
