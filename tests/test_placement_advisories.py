import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from placement_advisories import orientation_advisories_only


class PlacementAdvisoryGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = (ROOT / 'artifacts/validation-resume/native_placement.txt').read_text()

    def test_current_known_advisories_remain_reviewable(self):
        self.assertTrue(orientation_advisories_only(self.log))

    def test_summary_cannot_hide_real_drc_error(self):
        self.assertFalse(orientation_advisories_only(self.log.replace('Errors: 0', 'Errors: 1')))

    def test_summary_cannot_hide_drc_warning(self):
        self.assertFalse(orientation_advisories_only(self.log.replace('Warnings: 0', 'Warnings: 1')))

    def test_unrecognized_issue_requires_review(self):
        self.assertFalse(orientation_advisories_only(self.log.replace('Suggested move: rotate C_DV23 180 degrees.', 'Unexpected placement defect.')))

    def test_trailing_diagnostics_are_not_ignored(self):
        self.assertFalse(orientation_advisories_only(self.log + 'Unexpected diagnostic\n'))

    def test_missing_drc_section_requires_review(self):
        self.assertFalse(orientation_advisories_only(self.log.split('placement drc:')[0]))


if __name__ == '__main__':
    unittest.main()
