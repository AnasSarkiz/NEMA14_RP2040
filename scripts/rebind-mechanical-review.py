"""Rebind a completed mechanical review to routed JSON only after geometry equivalence.
This does not claim to rerun copper/DRC or change any model. Fails on mechanical edits.
"""
import hashlib,json,pathlib,shutil,re
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/mechanical'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def normal(v):
 if isinstance(v,bool):return v
 if isinstance(v,(int,float)):return round(float(v),9)
 if isinstance(v,list):return [normal(x) for x in v]
 if isinstance(v,dict):return {k:normal(x) for k,x in sorted(v.items())}
 return v
def frame(j,cat):
 source={e['source_component_id']:e for e in j if e['type']=='source_component'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};pc={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'}
 name=lambda e:source[e['source_component_id']]['name'];rows=[]
 for e in j:
  t=e['type']
  if t=='pcb_board':rows.append({k:e.get(k) for k in ['type','center','thickness','width','height','material','num_layers','outline']})
  if t=='pcb_component':rows.append({'type':t,'name':name(e),**{k:e.get(k) for k in ['center','width','height','rotation','layer']}})
  if t in ['pcb_hole','pcb_plated_hole','pcb_smtpad']:
   keys=['type','shape','hole_shape','x','y','width','height','radius','hole_width','hole_height','hole_diameter','ccw_rotation','points','polygon','rect_border_radius','corner_radius','rotation','outer_width','outer_height','outer_diameter','layer','layers']
   rows.append({k:e.get(k) for k in keys})
  if t=='cad_component' and e.get('model_step_url'):
   n=name(e);cid=cat['components'][n];p=cat['parts'][cid];step=next(f for f in p['modelFiles'] if f.endswith('.step'))
   assert (e['model_step_url']==p['activeModelUrls']['step'] if 'activeModelUrls' in p else e['model_step_url'].endswith(step)),(n,'active model differs from catalog')
   assert source[e['source_component_id']]['manufacturer_part_number']==p['manufacturerPartNumber'],(n,'manufacturer mismatch')
   assert sha(ROOT/step)==p['sha256']['step'],(n,'native supplier model hash mismatch')
   rows.append({'type':t,'name':n,'supplier':cid,'mpn':p['manufacturerPartNumber'],'step':step,'step_sha256':p['sha256']['step'],**{k:e.get(k) for k in ['position','rotation','model_origin_position','model_unit_to_mm_scale_factor','model_object_fit']}})
  if t=='pcb_port':
   component=pc.get(e.get('pcb_component_id'));n=name(component) if component else None
   if n in ['J_BOOT','J_DEBUG','J_MOTOR']:
    port=sp[e['source_port_id']];rows.append({'type':'bare_interface_port','name':n,'pin_number':str(port.get('pin_number')),'x':e['x'],'y':e['y']})
 rows=[normal(e) for e in rows];return sorted(rows,key=lambda e:json.dumps(e,sort_keys=True,separators=(',',':')))
oldpath=OUT/'input-board.circuit.json';oldcatpath=OUT/'input-jlcpcb-catalog.json';newpath=ROOT/'artifacts/board.circuit.json';newcatpath=ROOT/'src/jlcpcb-catalog.json';reportpath=OUT/'mechanical-review.json'
old=json.loads(oldpath.read_text());oldcat=json.loads(oldcatpath.read_text());new=json.loads(newpath.read_text());newcat=json.loads(newcatpath.read_text());r=json.loads(reportpath.read_text())
assert not r.get('review_current_status','').startswith('SUPERSEDED'),'Mechanical review is superseded: rerun full native mechanical review.'
assert r['script_sha256']==sha(ROOT/'scripts/review-mechanical.py'),'Mechanical review script changed: rerun full native review.'
assert r['board_sha256']==sha(oldpath),'review does not match its input snapshot'
a,b=frame(old,oldcat),frame(new,newcat)
if a!=b:
 oldonly=[e for e in a if e not in b];newonly=[e for e in b if e not in a]
 print(json.dumps({'old_only':oldonly[:12],'new_only':newonly[:12]},indent=2));raise SystemExit('Mechanical geometry changed: rerun review-mechanical.py on final saved board.')
original=OUT/'audited-input.circuit.json'
if not original.exists() or not r.get('rebind_proof'):shutil.copyfile(oldpath,original)
oldsha=sha(oldpath);newsha=sha(newpath);finger=hashlib.sha256(json.dumps(a,sort_keys=True,separators=(',',':')).encode()).hexdigest()
shutil.copyfile(newpath,oldpath);shutil.copyfile(newcatpath,oldcatpath)
source={e['source_component_id']:e for e in new if e['type']=='source_component'};cad={source[e['source_component_id']]['name']:e for e in new if e['type']=='cad_component' and e.get('model_step_url')};pcb={e['pcb_component_id']:e for e in new if e['type']=='pcb_component'}
for m in r['component_models']:m['cad_record']=cad[m['reference']]
for d in r.get('usb_coordinate_datums',[]):
 m=cad[d['reference']];d.update({'native_pcb_component_center_mm':pcb[m['pcb_component_id']]['center'],'cad_anchor_mm':m['position'],'cad_model_origin_mm':m['model_origin_position'],'rotation_deg':m['rotation']})
for d in r.get('bare_interface_top_probe_access',[]):
 choices=[e for e in new if e['type']=='pcb_port' and source[pcb[e['pcb_component_id']]['source_component_id']]['name']==d['interface'] and normal([e['x'],e['y']])==normal(d['xy_mm'])];assert len(choices)==1;d['pcb_port_id']=choices[0]['pcb_port_id']
# Native pad IDs may change when routing/export refreshes records; rebind by
# original-audit reference and complete unchanged geometric pad identity.
original_json=json.loads(original.read_text());original_source={e['source_component_id']:e for e in original_json if e['type']=='source_component'};original_pc={e['pcb_component_id']:e for e in original_json if e['type']=='pcb_component'}
padkeys=['type','shape','x','y','width','height','radius','ccw_rotation','points','polygon','rect_border_radius','corner_radius','rotation','outer_width','outer_height','outer_diameter','layer','layers']
def pad_key(e,ss,pcs):
 ref=ss[pcs[e['pcb_component_id']]['source_component_id']]['name'];return json.dumps(normal({'reference':ref,**{k:e.get(k) for k in padkeys}}),sort_keys=True,separators=(',',':'))
original_pads={e.get('pcb_smtpad_id',e.get('pcb_plated_hole_id')):e for e in original_json if e['type'] in ['pcb_smtpad','pcb_plated_hole']};new_pad_ids={}
for e in new:
 if e['type'] in ['pcb_smtpad','pcb_plated_hole']:new_pad_ids.setdefault(pad_key(e,source,pcb),[]).append(e.get('pcb_smtpad_id',e.get('pcb_plated_hole_id')))
for d in r.get('native_pad_to_fastener_keepout_screen',[]):
 d.setdefault('audited_native_pad_id',d['native_pad_id']);orig=original_pads[d['audited_native_pad_id']];choices=new_pad_ids[pad_key(orig,original_source,original_pc)];assert len(choices)==1,'ambiguous native pad ID rebind';d['native_pad_id']=choices[0]
r.update({'input_file':'artifacts/board.circuit.json','mechanical_frame_kind':'final routed board; mechanical geometry equivalence to completed audit proven','board_sha256':newsha,'catalog_sha256':sha(newcatpath),'input_current_at_finish':True,'rebind_proof':{'audited_input_sha256':sha(original),'previous_input_sha256':oldsha,'saved_board_sha256':newsha,'mechanical_fingerprint_sha256':finger,'coordinate_comparison_resolution_mm':1e-9,'geometry_equivalent':True,'verified_geometry':['board outline/thickness/stack','component footprint centers/rotations/bounds','all native pad/hole shapes','all native supplier model hashes/positions/rotations/origins','bare programming/motor contact coordinates'],'scope':'Existing mechanical intersections, clearance, adapter and render results remain valid because their physical inputs are unchanged. Copper/DRC must be checked separately.'}})
r.pop('review_in_progress',None);r['artifact_hashes']={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p!=reportpath};reportpath.write_text(json.dumps(r,indent=2)+'\n')
# Keep the final-board hash displayed in our own review document synchronized.
# Only this exact provenance sentence is changed; substantive findings stay intact.
doc=ROOT/'docs/mechanical-fit.md'
if doc.exists():
 text=doc.read_text();text=re.sub(r'(?:Final saved-board|Reviewed frozen physical-source) SHA256 is `[0-9a-f]{64}`',f'Final saved-board SHA256 is `{newsha}`',text);text=text.replace('> Physical placement review complete; final saved copper-board hash rebinding is pending.\n\n','');text=text.replace('Physical placement is frozen; root routing/export has not yet supplied the final saved-board copper revision.','The frozen physical-source audit is rebound to the final saved board with physical-fingerprint equality proof retained in the machine-readable report.');text=text.replace('The finished review must be rebound to `artifacts/board.circuit.json` with `python scripts/rebind-mechanical-review.py` after routing; a physical change requires a full rerun.','Any later copper/metadata refresh must be rebound with `python scripts/rebind-mechanical-review.py`; a physical change requires a full rerun.');doc.write_text(text)
proof={'board_sha256':newsha,'geometry_equivalent':True,'mechanical_fingerprint_sha256':finger};print(json.dumps(proof,indent=2))
