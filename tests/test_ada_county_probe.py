import json
import requests
import unittest

URL = "https://adacounty.bonfirehub.com/PublicPortal/getOpenPublicOpportunitiesSectionData"


class AdaCountyProbe(unittest.TestCase):
    def test_public_bonfire_probe(self):
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json, text/plain, */*"}, timeout=35)
        print("ADA_COUNTY_PROBE status=", r.status_code)
        print("ADA_COUNTY_PROBE content_type=", r.headers.get("content-type", ""))
        print("ADA_COUNTY_PROBE body_head=", r.text[:3000].replace("\n", " "))
        r.raise_for_status()
        payload = r.json()
        print("ADA_COUNTY_PROBE type=", type(payload).__name__)
        if isinstance(payload, dict):
            print("ADA_COUNTY_PROBE keys=", sorted(payload.keys()))
            for k, v in payload.items():
                if isinstance(v, list):
                    print("ADA_COUNTY_PROBE list_key=", k, "count=", len(v))
                    if v:
                        print("ADA_COUNTY_PROBE first=", json.dumps(v[0], sort_keys=True)[:5000])
                    break
        self.assertIsNotNone(payload)


if __name__ == "__main__":
    unittest.main()
