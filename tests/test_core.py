import unittest
from idaho_public_projects.classify import classify
from idaho_public_projects.models import Opportunity
from idaho_public_projects.utils import parse_date, parse_money, stable_id


class CoreTests(unittest.TestCase):
    def test_date_parsing(self):
        self.assertEqual(parse_date("08-05-26"), "2026-08-05")
        self.assertEqual(parse_date("September 9, 2026"), "2026-09-09")
        self.assertEqual(parse_date("8/26/2026, 8:00 AM MDT"), "2026-08-26")

    def test_money(self):
        self.assertEqual(parse_money("$2,150,000"), 2150000.0)

    def test_stable_id(self):
        self.assertEqual(stable_id("x", "1", "A"), stable_id("x", "1", "A"))

    def test_classification(self):
        op = Opportunity(id="x", source="x", title="Boise City Hall HVAC Remodel", agency="x", location="Boise, Idaho")
        classify(op)
        self.assertEqual(op.category, "BUILDING")
        self.assertGreaterEqual(op.score, 70)


if __name__ == "__main__":
    unittest.main()
