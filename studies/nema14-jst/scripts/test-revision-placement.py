"""Exercise the independent gate with the prior native-clean but screw-invalid board."""
import copy, importlib.util, json, unittest
from pathlib import Path
p=Path(__file__).with_name('check-revision-placement.py');spec=importlib.util.spec_from_file_location('screen',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
root=p.resolve().parents[1]/'tests/fixtures'
class ScreenRegression(unittest.TestCase):
 def setUp(self):
  self.board=json.loads((root/'known-screw-intrusions.circuit.json').read_text());self.contract=json.loads(p.with_name('mechanical-contract.json').read_text())
 def test_rejects_screw_intrusions_even_with_zero_native_errors(self):
  r=m.screen(self.board,self.contract)
  self.assertFalse(r['screen_pass']);self.assertEqual(r['native_errors'],[])
  self.assertEqual(len([e for e in r['findings'] if e['kind']=='screw_reserve']),20)
  self.assertEqual({tuple(e['mount']) for e in r['findings'] if e['kind']=='screw_reserve'},{(-13,-13),(-13,13),(13,-13),(13,13)})
 def test_checks_usb_and_mount_contract_independently(self):
  board=copy.deepcopy(self.board)
  next(e for e in board if e['type']=='pcb_board')['width']=36
  next(e for e in board if e['type']=='pcb_hole' and not e.get('pcb_component_id'))['x']+=1
  r=m.screen(board,self.contract);kinds={e['kind'] for e in r['findings']}
  self.assertIn('board_contract',kinds);self.assertIn('mount_contract',kinds)
 def test_rejects_top_entry_or_missing_courtyard(self):
  board=copy.deepcopy(self.board);source=next(e for e in board if e['type']=='source_component' and e['name']=='J_MOTOR')
  comp=next(e for e in board if e['type']=='pcb_component' and e['source_component_id']==source['source_component_id']);comp['insertion_direction']='from_above'
  board=[e for e in board if not(e['type']=='pcb_courtyard_outline' and e.get('pcb_component_id')==comp['pcb_component_id'])]
  kinds={e['kind'] for e in m.screen(board,self.contract)['findings']}
  self.assertIn('connector_direction',kinds);self.assertIn('missing_courtyard',kinds)
 def test_clear_mechanical_subset_can_pass(self):
  # This is a unit fixture of the two USBs, the side header and bottom sensor,
  # not a proposed populated board. Their exact real courtyards clear the heads.
  names={'J_PD','J_DATA','J_MOTOR','U_ENCODER'}
  ids={e['source_component_id'] for e in self.board if e['type']=='source_component' and e['name'] in names}
  pcb_ids={e['pcb_component_id'] for e in self.board if e['type']=='pcb_component' and e['source_component_id'] in ids}
  board=[copy.deepcopy(e) for e in self.board if e['type'] in {'pcb_board','pcb_hole','pcb_keepout'} or (e['type'] in {'source_component','pcb_component'} and e.get('source_component_id') in ids) or (e['type']=='pcb_courtyard_outline' and e.get('pcb_component_id') in pcb_ids)]
  for e in board:
   if e['type']=='pcb_keepout':e['allow_placements']=False
  self.assertTrue(m.screen(board,self.contract)['screen_pass'])
  next(e for e in board if e['type']=='pcb_keepout')['allow_placements']=True
  self.assertIn('screw_keepout_contract',{e['kind'] for e in m.screen(board,self.contract)['findings']})
if __name__=='__main__':unittest.main()
