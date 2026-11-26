import unittest
from idaho_public_projects.reporting_status import envelope

class TestReportingStatus(unittest.TestCase):
    def setUp(self):
        self.now = "2026-11-26T20:00:00+00:00"
        self.old = "2026-11-26T14:00:00+00:00"

    def test_verified_metadata_vs_error_dates_and_durable_ids(self):
        rows = [
            {"id":"known", "source":"ACHD", "posted_date":"2026-11-10", "due_date":"2026-12-02", "last_seen":self.now},
            {"id":"fresh", "source":"ACHD", "posted_date":"2026-11-20", "due_date":"2027-01-01", "last_seen":self.now},
            {"id":"retained", "source":"ACHD", "posted_date":"2026-11-11", "last_seen":self.old},
            {"id":"dpw-future", "source":"Idaho DPW", "stage":"OPEN_BID", "due_date":"2026-11-27", "last_seen":self.now},
            {"id":"dpw-result", "source":"Idaho DPW", "stage":"BID_RESULTS", "due_date":"2026-11-18", "last_seen":self.now},
        ]
        current={"collector_status":[{"source":"ACHD","status":"OK"},{"source":"Idaho DPW","status":"OK"},{"source":"Ada County","status":"ERROR"}]}
        previous={"generated_at":self.old,"collector_status":[{"source":"ACHD","status":"OK"},{"source":"Ada County","status":"OK"}]}
        q=envelope({"generated_at":self.now,"opportunities":rows},current,previous,{"known","retained"})
        self.assertEqual(q["schema_version"],1)
        data={x["id"]:x for x in q["sources"]}
        self.assertEqual((data["achd"]["new_since_previous_success"],data["achd"]["retained_records"],data["achd"]["observed_records"]), (1,3,2))
        self.assertEqual(data["achd"]["latest_authoritative_date"],"2026-11-20")
        self.assertIsNone(data["idaho-dpw"]["latest_authoritative_date"])
        self.assertIsNone(data["idaho-dpw"]["new_since_previous_success"])
        self.assertEqual(data["ada-county"]["last_success_at"],self.old)
        self.assertEqual(data["ada-county"]["collection_outcome"],"error")
        self.assertIsNone(data["ada-county"]["observed_records"])

    def test_verified_zero_distinct_and_prior_truth_survives(self):
        previous={"reporting_v1":{"sources":[{"id":"achd","last_success_at":self.old,"latest_authoritative_date":"2026-11-10"}]}}
        current={"collector_status":[{"source":"ACHD","status":"EMPTY"},{"source":"Ada County","status":"EMPTY"}]}
        r=envelope({"generated_at":self.now,"opportunities":[]},current,previous,set())
        data={x["id"]:x for x in r["sources"]}
        self.assertEqual((data["achd"]["collection_outcome"],data["achd"]["observed_records"],data["achd"]["latest_authoritative_date"]),("no_data",0,"2026-11-10"))
        self.assertEqual(data["ada-county"]["collection_outcome"],"unknown")
        self.assertIsNone(data["ada-county"]["observed_records"])
