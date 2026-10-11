"""Replay native source mounting features into the reviewed saved routing.
Only board-owned holes and keepouts are regenerated. Pin/net identities, pads,
component placement and every trace/via must remain byte-equivalent as objects.
"""
import hashlib,itertools,json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json'
board=json.loads(path.read_text());source=json.loads((root/'artifacts/final-source.circuit.json').read_text())
def mounting(e):return e['type']=='pcb_keepout' or (e['type']=='pcb_hole' and not e.get('pcb_component_id'))
features=[e for e in source if mounting(e)];holes=[e for e in features if e['type']=='pcb_hole'];expected=set(itertools.product([-13,13],repeat=2))
assert len(holes)==4 and {(e['x'],e['y']) for e in holes}==expected and all(e['hole_diameter']==3.2 for e in holes)
keepouts=[e for e in features if e['type']=='pcb_keepout'];assert len(keepouts)==4
layers={'top','bottom'} if next(e for e in board if e['type']=='pcb_board')['num_layers']==2 else {'top','inner1','inner2','bottom'}
assert all(set(e['layers'])==layers for e in keepouts),'Mount keepouts must protect every copper layer'
byid={e[e['type']+'_id']:e for e in features};new=[byid[e[e['type']+'_id']] if mounting(e) else e for e in board]
assert [e for e in board if not mounting(e)]==[e for e in new if not mounting(e)]
path.write_text(json.dumps(new,indent=2)+'\n');(root/'index.circuit.json').write_text(json.dumps(new,separators=(',',':'))+'\n')
base=subprocess.check_output(['git','rev-parse','origin/main'],cwd=root,text=True).strip();old=json.loads(subprocess.check_output(['git','show',base+':artifacts/board.circuit.json'],cwd=root,text=True))
unchanged_types={'source_component','source_port','source_net','source_trace','pcb_component','pcb_smtpad','pcb_plated_hole','pcb_port','pcb_trace','pcb_via','cad_component','pcb_hole'}
assert [e for e in new if e['type'] in unchanged_types]==[e for e in old if e['type'] in unchanged_types],'Existing function, placement or signal copper changed'
proof={'baseline_github_commit':base,'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'native_source_mounting_replayed':True,'exact_mounts_mm':sorted(expected),'mount_drill_mm':3.2,'all_layer_keepouts':sorted(layers),'all_existing_source_pins_nets_components_pads_traces_vias_and_CAD_unchanged':True,'modified_geometry_types':sorted({e['type'] for e in old if e not in new}|{e['type'] for e in new if e not in old})}
(root/'artifacts/mounting-change-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
