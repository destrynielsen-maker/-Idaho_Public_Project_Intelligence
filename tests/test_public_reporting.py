"""Regression coverage for reporting labels without policy/membership changes."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from idaho_public_projects.dashboard import HTML


class TestPublicReporting(unittest.TestCase):
    def test_existing_default_and_filter_logic_stays_separate_from_labels(self):
        open_function = re.search(r"function isOpen\(r\)\{[^\n]+", HTML).group()
        result_function = re.search(r"function isResult\(r\)\{[^\n]+", HTML).group()
        self.assertEqual(open_function, "function isOpen(r){return !['BID_RESULTS','AWARDED','CLOSED'].includes(String(r.stage||'').toUpperCase()) && !['RESULTS','CLOSED','AWARDED'].includes(String(r.status||'').toUpperCase())}")
        self.assertEqual(result_function, "function isResult(r){return ['BID_RESULTS','AWARDED'].includes(String(r.stage||'').toUpperCase()) || ['RESULTS','AWARDED'].includes(String(r.status||'').toUpperCase())}")
        filter_line = [line for line in HTML.splitlines() if "return data.filter" in line][0]
        self.assertIn("passesDate(r)).sort(compareRows)", filter_line)
        for evidence_label in ["dueEvidence", "seenEvidence", "stageEvidence", "amountEvidence"]:
            self.assertNotIn(evidence_label, filter_line)

    def test_reads_existing_source_health_separately_and_escapes_values(self):
        self.assertIn("fetch('data/sources.json?'+Date.now())", HTML)
        self.assertIn("different from project snapshot", HTML)
        self.assertIn("does not mean zero source activity", HTML)
        self.assertIn("esc(c.note)", HTML)
        self.assertIn("esc(c.source", HTML)
        self.assertIn("void bootSourceHealth()", HTML)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for JS renderer fixtures")
    def test_evidence_labels_execute_without_changing_frozen_data(self):
        js = HTML.split("<script>", 1)[1].split("</script>", 1)[0]
        functions = js[js.index("function mountainTimestamp"):js.index("async function bootSourceHealth")]
        check = """
const assert=require('node:assert/strict');
const at='2026-11-26T19:31:04+00:00';
assert.equal(deadlineKind({source:'Idaho Purchasing',due_date:'2026-11-01'}),'Planning target (not a bid deadline)');
assert.equal(dueEvidence({source:'Idaho DPW',stage:'BID_RESULTS',due_date:'2026-11-01'},at),'Bid date on result');
assert.match(dueEvidence({source:'City of Boise',due_date:'2026-11-01'},at),/past at snapshot/);
assert.equal(postedEvidence({source:'Idaho Purchasing',posted_date:'2026-11-01'}),'Planning record created');
assert.match(seenEvidence({last_seen:'2026-11-01T18:00:00Z'},at),/^Retained/);
assert.equal(seenEvidence({last_seen:at},at),'Seen in this snapshot');
assert.match(stageEvidence({source:'Idaho Purchasing',title:'PA Example',stage:'UPCOMING'}),/not a call for bids/);
assert.match(stageEvidence({stage:'AWARDED'}),/no awardee verified/);
assert.match(amountEvidence({source:'Idaho DPW',stage:'BID_RESULTS',estimated_value:1}),/not an award/);
assert.match(mountainTimestamp(at),/12:31 PM Mountain/);
"""
        result = subprocess.run(["node", "-e", functions + check], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is needed for JS CSV fixtures")
    def test_csv_quotes_and_shields_formulas_without_contact_fields(self):
        import csv
        import io
        js = HTML.split("<script>", 1)[1].split("</script>", 1)[0]
        evidence = js[js.index("function mountainTimestamp"):js.index("async function bootSourceHealth")]
        export = js[js.index("function csvCell"):js.index("function downloadFilteredCsv")]
        fixture = {"id":"safe-id","source":"Idaho Purchasing","title":"\u200b=FUNCTION()","location":"A, B says \"Hi\"\nnext","due_date":"2026-11-28","contact":"sensitive@example.com","owner":"Do not include me","bidders":[{"contractor":"Omit me"}]}
        invocation = "console.log(JSON.stringify(exportRowsCsv([" + json.dumps(fixture) + "],'2026-11-26T19:31:04Z')))"
        result = subprocess.run(["node", "-e", evidence + export + invocation], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = json.loads(result.stdout)
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(rows[0]["Title"], "'\u200b=FUNCTION()")
        self.assertEqual(rows[0]["Location"], fixture["location"])
        self.assertEqual(rows[0]["Recorded date type"], "Planning target (not a bid deadline)")
        self.assertEqual(rows[0]["Bidder count"], "1")
        for disallowed in ["sensitive@example.com", "Do not include me", "Omit me"]:
            self.assertNotIn(disallowed, text)
