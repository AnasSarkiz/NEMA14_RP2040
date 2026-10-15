"""Reject real or unknown findings while recognizing native informational voids."""
import pathlib,unittest
from placement_advisories import orientation_advisories_only
ROOT=pathlib.Path(__file__).resolve().parents[1]
LOG=(ROOT/'tests/fixtures/native-orientation-advisories.txt').read_text()
class PublicationAdvisoryTests(unittest.TestCase):
 def test_real_native_fixture(self):self.assertTrue(orientation_advisories_only(LOG))
 def test_real_drc_error_is_blocked(self):self.assertFalse(orientation_advisories_only(LOG.replace('Errors: 0','Errors: 1')))
 def test_real_warning_is_blocked(self):self.assertFalse(orientation_advisories_only(LOG.replace('Warnings: 0','Warnings: 1')))
 def test_unknown_utilization_finding_is_blocked(self):self.assertFalse(orientation_advisories_only(LOG.replace('- empty spaces over 5% of board area:', '- unsafe placement:')))
 def test_missing_flagged_component_is_blocked(self):self.assertFalse(orientation_advisories_only(LOG.replace('placement summary: 8','placement summary: 9')))
 def test_unknown_orientation_issue_is_blocked(self):self.assertFalse(orientation_advisories_only(LOG.replace('Suggested move: rotate C_PD 180 degrees.', 'Pin polarity is wrong.')))
if __name__=='__main__':unittest.main()
