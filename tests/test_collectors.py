import unittest

from idaho_public_projects.collectors.achd import parse_html as parse_achd
from idaho_public_projects.collectors.boise import parse_html as parse_boise
from idaho_public_projects.collectors.dpw import parse_html as parse_dpw
from idaho_public_projects.collectors.purchasing import parse_html as parse_purchasing


class CollectorTests(unittest.TestCase):
    def test_boise(self):
        html = """<table><tr><td><a href=\"https://app01.jaggaer.com/x\">City Hall Elevator Modernization</a>
        Modernize elevators Open 8/11/2026, 5:00 PM MDT Close 9/30/2026, 10:00 AM MDT Type FB- Number FB-2026-081
        Contact buyer@cityofboise.org <a href=\"https://example.com/detail.pdf\">View as PDF</a></td></tr></table>"""
        rows = parse_boise(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].solicitation_number, "FB-2026-081")
        self.assertEqual(rows[0].due_date, "2026-09-30")

    def test_dpw(self):
        html = """<h3>Advertisement for Bid</h3><table>
        <tr><th>Bid Date</th><th>Project Number</th><th>Project Name</th></tr>
        <tr><td>09-03-26</td><td>26570</td><td>D4 Admin Bldg. Upgrade, Idaho Transportation Department, Shoshone, Idaho</td></tr>
        </table><h3>Recent Construction Bid Results</h3><table>
        <tr><th>Date</th><th>Project Number</th><th>Project Name</th><th>Contractor</th><th>Base Bid</th></tr>
        <tr><td>07-28-26</td><td>25320</td><td>Paving, Liquor Division, Boise, Idaho</td><td>Gentry Civil</td><td>$630,539</td></tr>
        <tr><td>Paul Construction</td><td>$868,000</td></tr></table>"""
        rows = parse_dpw(html)
        self.assertEqual(len(rows), 2)
        result = [r for r in rows if r.stage == "BID_RESULTS"][0]
        self.assertEqual(len(result.bidders), 2)

    def test_purchasing(self):
        html = """<table><tr><th>Name</th><th>Agency</th><th>Overview</th><th>Created Date</th><th>Start Date</th><th>Due Date</th><th>Updated Date</th><th>Completed Date</th><th>Status</th></tr>
        <tr><td>Roof Replacement</td><td>Agency A</td><td>Replace roof</td><td>August 1, 2026</td><td>September 1, 2026</td><td>October 1, 2026</td><td>August 20, 2026</td><td></td><td>On Track</td></tr></table>"""
        rows = parse_purchasing(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].stage, "UPCOMING")

    def test_achd(self):
        html = """<div class=\"accordion-item\"><h3>August 18, 2026 - September 2, 2026 - McMillan Signal Rebid</h3>
        <p>Invitation to Bid Contract Number: CT226-29 Project Location: Meridian, Idaho. Bids received until Wednesday, September 2, 2026.</p>
        <a href=\"https://procurement.opengov.com/portal/achdidaho/projects/1\">Bid portal</a></div>"""
        rows = parse_achd(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].solicitation_number, "CT226-29")
        self.assertEqual(rows[0].location, "Meridian, Idaho")
        self.assertEqual(rows[0].due_date, "2026-09-02")


if __name__ == "__main__":
    unittest.main()
