"""Regression guards for the full-controller experiment verifier."""
from pathlib import Path
import json,copy,unittest,importlib.util
spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-integrated-kelvin.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Guards(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.b=json.loads(Path('artifacts/iteration-3/authored.circuit.json').read_text())
 def test_native_port_annotations_do_not_change_copper(self):
  b=copy.deepcopy(self.b);next(e for e in b if e['type']=='pcb_trace')['route'][0]['start_pcb_port_id']='native_annotation';self.assertEqual(v.geometry(self.b),v.geometry(b))
 def test_changed_copper_is_not_hidden(self):
  b=copy.deepcopy(self.b);next(e for e in b if e['type']=='pcb_trace')['route'][1]['x']+=.001;self.assertNotEqual(v.geometry(self.b),v.geometry(b))
 def test_driver_pad_or_component_cannot_move(self):
  b=copy.deepcopy(self.b);next(e for e in b if e['type']=='pcb_component')['center']['x']+=.001
  with self.assertRaises(AssertionError):v.assert_fixed(self.b,b)
 def test_driver_pad_tip_stays_physically_joined(self):
  # The native contiguity check is separate from polygon overlap. Both are mandatory.
  for file in ['authored-native.json','normal-native.json']:
   checks=json.loads(Path('artifacts/iteration-3',file).read_text());self.assertEqual(checks['checkTracesAreContiguous']['count'],0)
if __name__=='__main__':unittest.main()
