import json
import unittest
from unittest.mock import patch
from idaho_public_projects.collectors import achd

def fixture(rows, count=None):
    details={'count':len(rows) if count is None else count,'rows':rows}
    return '<script>window.__data={"govProjects":{"loading":false},"unrelated":function noop(){},"public":{"govProjects":'+json.dumps(details)+'}};</script>'

def row(**updates):
    result = {
        'government':{'code':'achdidaho'},'status':'open','isPrivate':False,'isPaused':False,'comingSoon':False,
        'id':320264,'title':'2027 Tree Pruning Services','financialId':'MO27-16','releaseProjectDate':'2026-11-10T07:00:00Z',
        'proposalDeadline':'2026-12-02T22:00:00Z','template':{'title':'Request For Proposal'},'summary':'<p>Public project summary</p>',
    }
    return {**result, **updates}

class TestACHDEmbed(unittest.TestCase):
    def collect(self, html):
        with patch.object(achd, 'http_get',return_value=html):
            return achd.collect()

    def test_explicit_open_and_stable_key(self):
        html=fixture([row()])
        a,=self.collect(html)
        self.assertEqual(a.id,self.collect(html)[0].id)
        self.assertEqual((a.source,a.stage,a.solicitation_number,a.posted_date,a.due_date,a.solicitation_type),('ACHD','OPEN_BID','MO27-16','2026-11-10','2026-12-02','RFP'))
        self.assertEqual(a.url,'https://procurement.opengov.com/portal/achdidaho/projects/320264')

    def test_timezone_conversion(self):
        a,=self.collect(fixture([row(proposalDeadline='2026-12-03T01:00:00Z')]))
        self.assertEqual(a.due_date,'2026-12-02')

    def test_genuine_zero_is_distinct_from_markup_gap(self):
        self.assertEqual(self.collect(fixture([])),[])
        with self.assertRaises(ValueError):
            self.collect('<html>Loading projects</html>')

    def test_fail_closed_on_wrong_schema_or_rows(self):
        for rows,count in [([row()],2),([row(),row()],2),([row(isPrivate=True)],1),([row(status='evaluation')],1),([row(government={'code':'other'})],1),([row(proposalDeadline=None)],1)]:
            with self.subTest(rows=rows,count=count), self.assertRaises(ValueError):
                self.collect(fixture(rows,count))

    def test_invalid_network_is_not_zero(self):
        with patch.object(achd, 'http_get',side_effect=RuntimeError("403")):
            with self.assertRaises(RuntimeError):
                achd.collect()

class TestACHDPagination(unittest.TestCase):
    def test_two_complete_pages_and_first_page_recheck(self):
        first = fixture([row()], 2)
        second = fixture([row(id=2, title='Another public solicitation')], 2)
        with patch.object(achd, 'http_get', side_effect=[first, second, first]) as get:
            rows = achd.collect()
        self.assertEqual(len({r.id for r in rows}), 2)
        self.assertEqual([c.args[0] for c in get.call_args_list], [achd.URL, achd.URL + '&page=2', achd.URL])

    def test_count_drift_duplicate_and_reordered_first_page_fail_closed(self):
        a = fixture([row()], 2)
        second = fixture([row(id=2, title='Another public solicitation')], 2)
        cases = [(a, fixture([row(id=2)], 3)), (a, a, a), (a, second, second), (a, fixture([], 2))]
        for pages in cases:
            with self.subTest(pages=len(pages)), patch.object(achd, 'http_get', side_effect=pages), self.assertRaises(ValueError):
                achd.collect()

    def test_caps_and_typed_public_payload(self):
        for payload in [fixture([row()],101), fixture(['not a row']), fixture([row()],True)]:
            with patch.object(achd, 'http_get', return_value=payload), self.assertRaises(ValueError):
                achd.collect()
        first = fixture([row()], 2)
        with patch.object(achd, 'MAX_OPEN_PAGES',1), patch.object(achd, 'http_get',return_value=first), self.assertRaises(ValueError):
            achd.collect()


def detail(**updates):
    project = row(**updates)
    return '<script>window.__data={"govProject":{"project":'+json.dumps(project)+'}};</script>'


class TestACHDStatus(unittest.TestCase):
    def test_explicit_lifecycle_and_no_substatus_inference(self):
        for status, sub in [('open',None),('evaluation',None),('awardPending',None),('closed','awarded')]:
            with self.subTest(status=status):
                self.assertEqual(achd.parse_status_observation(detail(status=status,closedSubstatus=sub),320264),(status,sub))

    def test_mismatch_private_shell_or_unknown_is_unverified(self):
        for html in [detail(id=7),detail(isPrivate=True),detail(government={'code':'other'}),detail(status='draft'),'<html>no data</html>']:
            self.assertEqual(achd.parse_status_observation(html,320264),('UNVERIFIED',None))

    def test_missing_observed_without_mutation_or_cross_source_lookup(self):
        target = {'id':'stable-key','source':'ACHD','stage':'OPEN_BID','status':'OPEN','first_seen':'2026-01-01',
                  'url':'https://procurement.opengov.com/portal/achdidaho/projects/320264'}
        history = [target,{**target,'source':'Other'},{**target,'url':'https://unrelated.invalid/'},{**target}]
        original = json.dumps(history)
        with patch.object(achd,'http_get',return_value=detail(status='closed',closedSubstatus='awarded')) as get:
            observations = achd.observe_missing(history, [])
        self.assertEqual(json.dumps(history),original)
        self.assertEqual(get.call_count,1)
        self.assertEqual((observations[0]['status_observed'],observations[0]['closed_substatus_observed'],observations[0]['publication_effect']),('closed','awarded','NONE'))
        with patch.object(achd,'http_get',side_effect=RuntimeError('403')):
            self.assertEqual(achd.observe_missing(history,[])[0]['status_observed'],'UNVERIFIED')
        with patch.object(achd,'http_get') as no_fetch:
            self.assertEqual(achd.observe_missing(history,achd.parse_html(fixture([row()]))),[])
            no_fetch.assert_not_called()
