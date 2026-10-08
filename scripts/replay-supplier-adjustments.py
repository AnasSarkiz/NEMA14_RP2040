"""Replay accepted native C_CP/J_BOOT pose deltas, then saved supplier copper changes.

Every baseline record must match its reviewed before image exactly. This never
transforms supplier land patterns: after images are complete fresh source-native
records. All other PCB records remain byte-value-identical before copper replay.
"""
import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json';base=root/'artifacts/supplier.circuit.json'
j=json.loads(base.read_text());proof=json.loads((root/'artifacts/supplier-routing-adjustments.json').read_text());idkey=lambda e:e.get(e['type']+'_id')
physical_path=root/'artifacts/rp-native-physical-delta.json';delta=json.loads(physical_path.read_text());fresh=json.loads((root/'artifacts/final-source.circuit.json').read_text());freshids={idkey(e):e for e in fresh};ids={idkey(e):e for e in j};physical_ids={c['id'] for c in delta['changes']}
assert delta['references']==['C_CP','J_BOOT'] and delta['nativeFootprintsUnchanged'] and delta['sourcePinsAndNetsUnchanged']
assert len(physical_ids)==len(delta['changes']) and physical_ids
before_other=[e for e in j if idkey(e) not in physical_ids]
for change in delta['changes']:
 assert ids.get(change['id'])==change['before'],change['id']+' source-native physical baseline mismatch'
 expected_after=dict(freshids.get(change['id'],{}))
 for field in change['delegatedMetadataFields']:
  assert change['reference']=='J_BOOT' and change['after']['type']=='pcb_component' and field=='insertion_direction' and expected_after[field]=='from_above'
  expected_after.pop(field)
 assert expected_after==change['after'],change['id']+' reviewed physical after image differs from current fresh source'
 assert change['reference'] in delta['references']
 assert change['after'].get('pcb_component_id')==change['pcbComponentId'] or (change['after']['type']=='cad_component' and change['after'].get('source_component_id')==change['sourceComponentId'])
 if change['after']['type']=='pcb_smtpad':
  for field in ['shape','width','height','radius','ccw_rotation','layer','pcb_port_id','port_hints']:
   assert change['before'].get(field)==change['after'].get(field),change['id']+' raw pad shape/pin identity changed'
replacement={c['id']:c['after'] for c in delta['changes']};j=[replacement.get(idkey(e),e) for e in j]
assert [e for e in j if idkey(e) not in physical_ids]==before_other,'Unrelated source-native PCB base changed'
ids={idkey(e):e for e in j}
for c in proof['changes']:
 assert ids.get(c['id'])==c['before'],c['id']+' input mismatch'
 if c['before'] is not None:j.remove(ids[c['id']])
 if c['after'] is not None:j.append(c['after'])
# These seven source-native records differ only in reviewed semantic fields.
# Apply after copper replay so no copper route can be changed by this step.
metadata_path=root/'artifacts/rp-source-metadata-physical-delta.json';metadata=json.loads(metadata_path.read_text());ids={idkey(e):e for e in j};metadata_ids={c['id'] for c in metadata['changes']};assert len(metadata_ids)==7
unchanged=[e for e in j if idkey(e) not in metadata_ids]
for change in metadata['changes']:
 assert ids.get(change['id'])==change['before'],change['id']+' reviewed metadata baseline mismatch'
 assert freshids.get(change['id'])==change['after'],change['id']+' accepted metadata differs from fresh source'
 field=change['field'];assert field in ['layers','insertion_direction']
 assert {k:v for k,v in change['before'].items() if k!=field}=={k:v for k,v in change['after'].items() if k!=field},change['id']+' unreviewed physical geometry change'
 if field=='layers':
  assert change['after']['type']=='pcb_keepout' and change['after']['shape']=='circle' and change['after']['radius']==2.7
  assert change['before']['layers']==['top','bottom'] and change['after']['layers']==['top','inner1','inner2','bottom']
 else:
  assert change['after']['type']=='pcb_component' and change['reference'] in ['J_MOTOR','J_DEBUG','J_BOOT']
  assert change['before'].get(field) is None and change['after'][field]=='from_above'
metadata_replacements={c['id']:c['after'] for c in metadata['changes']};j=[metadata_replacements.get(idkey(e),e) for e in j]
assert [e for e in j if idkey(e) not in metadata_ids]==unchanged,'Unrelated records/Cu changed during metadata update'
path.write_text(json.dumps(j,indent=2)+'\n')
manifest={'supplierBaseSha256':hashlib.sha256(base.read_bytes()).hexdigest(),'physicalDeltaFile':str(physical_path.relative_to(root)),'physicalDeltaSha256':hashlib.sha256(physical_path.read_bytes()).hexdigest(),'references':delta['references'],'placementOnlyDeltas':delta['groups'],'fullFreshNativePhysicalRecordIds':sorted(physical_ids),'allPhysicalBeforeImagesMatchedExactly':True,'allReviewedAfterImagesMatchedCurrentSourceExactly':True,'unrelatedNativePcbBaseUnchanged':True,'copperAdjustmentsReplayed':len(proof['changes']),'resultBeforePresentationSyncSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'requiresUsualPresentationSyncAndFinalChecks':True,'metadataDeltaFile':str(metadata_path.relative_to(root)),'metadataDeltaSha256':hashlib.sha256(metadata_path.read_bytes()).hexdigest(),'mountCircleLayerRecordIds':[c['id'] for c in metadata['changes'] if c['field']=='layers'],'bareInsertionRecordIds':[c['id'] for c in metadata['changes'] if c['field']=='insertion_direction'],'onlyReviewedMetadataFieldsChanged':True,'metadataStepCuUnchanged':True}
(root/'artifacts/adjustment-replay-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Replayed',len(physical_ids),'reviewed C_CP native physical records and',len(proof['changes']),'PCB copper adjustments; refresh presentation and run checks.')
