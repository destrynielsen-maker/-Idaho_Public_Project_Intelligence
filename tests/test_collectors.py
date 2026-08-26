import unittest

from idaho_public_projects.collectors.achd import parse_html as parse_achd
from idaho_public_projects.collectors.ada_county import parse_report as parse_ada_county_report
from idaho_public_projects.collectors.boise import parse_html as parse_boise
from idaho_public_projects.collectors.dpw import parse_html as parse_dpw
from idaho_public_projects.collectors.purchasing import (
    parse_html as parse_purchasing,
    parse_report as parse_purchasing_report,
)


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

    def test_purchasing_report(self):
        payload = {
            "data": [
                {
                    "agency": "IDFG",
                    "latest_update_date": "2026-08-24T17:11:29.749Z",
                    "name": "RFP 717 - IDFG Website Rebuild",
                    "project_completed_date": "",
                    "project_created_date": "2024-12-06T23:10:55.668Z",
                    "project_description": "Post Date: 06/05/2025 Close Date: 08/06/2025",
                    "project_due_date": "2025-06-27",
                    "project_start_date": "2024-12-06",
                    "status": "Off track",
                }
            ]
        }
        rows = parse_purchasing_report(payload)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.source, "Idaho Purchasing")
        self.assertEqual(row.solicitation_type, "RFP")
        self.assertEqual(row.solicitation_number, "RFP 717")
        self.assertEqual(row.posted_date, "2024-12-06")
        self.assertEqual(row.updated_date, "2026-08-24")
        self.assertEqual(row.stage, "UPCOMING")

    def test_ada_county_report(self):
        payload = {
            "success": 1,
            "payload": {
                "projects": {
                    "248796": {
                        "ProjectID": "248796",
                        "ReferenceID": "Bid 26062",
                        "ProjectName": "Ada County Courthouse VRF #3 & 4 Replacement 2026",
                        "DateClose": "2026-09-04 22:00:00",
                        "DepartmentID": "4123",
                    }
                },
                "departments": [],
            },
        }
        rows = parse_ada_county_report(payload)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.source, "Ada County")
        self.assertEqual(row.solicitation_number, "Bid 26062")
        self.assertEqual(row.solicitation_type, "BID")
        self.assertEqual(row.due_date, "2026-09-04")
        self.assertEqual(row.url, "https://adacounty.bonfirehub.com/opportunities/248796")

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
