import json
import unittest
from collections import Counter
from datetime import date, datetime
from pathlib import Path


DATA_PATH = Path('public/data/opportunities.json')


def iso_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except ValueError:
        return None


class OutcomeAudit(unittest.TestCase):
    def test_current_dataset_outcomes(self):
        payload = json.loads(DATA_PATH.read_text(encoding='utf-8'))
        rows = payload.get('opportunities', [])
        today = date.today()

        ids = [r.get('id') for r in rows if r.get('id')]
        duplicate_ids = [k for k, v in Counter(ids).items() if v > 1]
        missing_title = sum(1 for r in rows if not r.get('title'))
        missing_agency = sum(1 for r in rows if not r.get('agency'))
        missing_url = sum(1 for r in rows if not r.get('url'))

        by_source = Counter(r.get('source') or 'UNKNOWN' for r in rows)
        by_stage = Counter(r.get('stage') or 'UNKNOWN' for r in rows)
        by_category = Counter(r.get('category') or 'UNKNOWN' for r in rows)
        by_agency = Counter(r.get('agency') or 'UNKNOWN' for r in rows)

        active = [r for r in rows if r.get('stage') not in {'CLOSED', 'BID_RESULTS', 'AWARDED'} and r.get('status') not in {'CLOSED', 'RESULTS', 'COMPLETED'}]
        results = [r for r in rows if r.get('stage') in {'BID_RESULTS', 'AWARDED'}]
        early = [r for r in rows if r.get('source') == 'Idaho Purchasing' or r.get('stage') in {'FUTURE', 'UPCOMING'}]

        due_7 = due_14 = due_30 = overdue_active = 0
        no_due_active = 0
        for r in active:
            due = iso_date(r.get('due_date'))
            if due is None:
                no_due_active += 1
                continue
            days = (due - today).days
            if days < 0:
                overdue_active += 1
            if 0 <= days <= 7:
                due_7 += 1
            if 0 <= days <= 14:
                due_14 += 1
            if 0 <= days <= 30:
                due_30 += 1

        purchasing = [r for r in rows if r.get('source') == 'Idaho Purchasing']
        purchasing_stage = Counter(r.get('stage') or 'UNKNOWN' for r in purchasing)
        purchasing_agency = Counter(r.get('agency') or 'UNKNOWN' for r in purchasing)

        dpw_results = [r for r in rows if r.get('source') == 'Idaho DPW' and r.get('stage') == 'BID_RESULTS']
        dpw_with_bidders = sum(1 for r in dpw_results if r.get('bidders'))
        bidder_rows = sum(len(r.get('bidders') or []) for r in dpw_results)
        dpw_with_value = sum(1 for r in dpw_results if r.get('estimated_value') is not None)

        title_agency = Counter((r.get('title','').strip().lower(), r.get('agency','').strip().lower()) for r in rows)
        duplicate_title_agency = sum(1 for k, v in title_agency.items() if k[0] and v > 1)

        top = sorted(rows, key=lambda r: (r.get('score', 0), r.get('due_date','')), reverse=True)[:15]

        print('\n=== IDAHO PUBLIC PROJECT INTELLIGENCE OUTCOME AUDIT ===')
        print('Generated:', payload.get('generated_at', ''))
        print('Normalized opportunities:', len(rows))
        print('Active opportunities:', len(active))
        print('Bid results / awards:', len(results))
        print('Early / future feed candidates:', len(early))
        print('Source mix:', dict(by_source))
        print('Stage mix:', dict(by_stage))
        print('Category mix:', dict(by_category))
        print('Due next 7 days:', due_7)
        print('Due next 14 days:', due_14)
        print('Due next 30 days:', due_30)
        print('Active records already past due:', overdue_active)
        print('Active records with no due date:', no_due_active)
        print('Idaho Purchasing stage mix:', dict(purchasing_stage))
        print('Idaho Purchasing agencies:', dict(purchasing_agency.most_common()))
        print('DPW bid-result projects:', len(dpw_results))
        print('DPW result projects with bidders:', dpw_with_bidders)
        print('DPW bidder rows:', bidder_rows)
        print('DPW result projects with low-bid/value:', dpw_with_value)
        print('Duplicate IDs:', len(duplicate_ids))
        print('Duplicate title+agency groups:', duplicate_title_agency)
        print('Missing title / agency / URL:', missing_title, missing_agency, missing_url)
        print('Top agencies:', dict(by_agency.most_common(15)))
        print('TOP 15 BY SCORE:')
        for r in top:
            print(f"  {r.get('score',0):>3} | {r.get('due_date') or 'TBD':10} | {r.get('source','')} | {r.get('stage','')} | {r.get('title','')[:110]}")
        print('=== END OUTCOME AUDIT ===\n')

        self.assertGreater(len(rows), 0)
        self.assertEqual(duplicate_ids, [], f'Duplicate stable IDs found: {duplicate_ids[:10]}')
        self.assertEqual(missing_title, 0)
        self.assertEqual(missing_agency, 0)
        self.assertEqual(missing_url, 0)


if __name__ == '__main__':
    unittest.main()
