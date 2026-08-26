# Idaho Public Project Intelligence — Outcome Audit

Audit date: 2026-08-26

This report was generated from the persisted production dataset created at `2026-08-26T19:27:13+00:00`, with a follow-on live collector run confirming current source counts. The audit branch was not merged into production.

## Core counts

- Normalized opportunities: **124**
- Active opportunities: **49**
- Bid results / awards: **74**
- Early / future feed candidates: **39**

## Source mix

- City of Boise: **5** normalized records
- Idaho DPW: **80** normalized records
- Idaho Purchasing: **39** normalized records

The live collection run saw **125 raw source records**: City of Boise 5, Idaho DPW 80, Idaho Purchasing 40, ACHD 0. One raw record is collapsed/handled during normalization, producing 124 normalized opportunities.

## Stage mix

- OPEN_BID: **13**
- BID_RESULTS: **71**
- UPCOMING: **33**
- FUTURE: **3**
- AWARDED: **3**
- CLOSED: **1**

## Category mix

- BUILDING: **66**
- OTHER: **47**
- MATERIALS_EQUIPMENT: **6**
- PROFESSIONAL_SERVICES: **4**
- CIVIL: **1**

## Due-date horizons

- Due in next 7 days: **6**
- Due in next 14 days: **10**
- Due in next 30 days: **19**
- Active records already past due: **9**
- Active records with no due date: **0**

## Idaho Purchasing

Stage mix:
- UPCOMING: **33**
- FUTURE: **3**
- AWARDED: **3**

Agency counts:
- STATEWIDE: 8
- ITD: 6
- DHW: 5
- ADM: 4
- VETS: 3
- ISHS: 2
- IPTV: 2
- ITS: 1
- IMD: 1
- ITS, STATEWIDE: 1
- IDOC: 1
- ODP: 1
- DOPL: 1
- AGING: 1
- AGRI: 1
- IDFG: 1

## DPW bid-result intelligence

- DPW bid-result projects: **71**
- DPW result projects with bidder detail: **70**
- Total bidder rows captured: **306**
- DPW result projects with a low-bid / estimated-value field: **64**

## Data-quality checks

- Duplicate stable IDs: **0**
- Duplicate title + agency groups: **0**
- Missing titles: **0**
- Missing agencies: **0**
- Missing source URLs: **0**

## Highest-scoring current opportunities

1. **83** — City of Boise — Siphon Cleaning and CCTV Project 2026 (PWE 852) — due 2026-09-09
2. **82** — City of Boise — City Hall Downtown Elevator Modernization Cars 1 & 2 (GBP 110) — due 2026-09-30
3. **82** — Idaho DPW — IAB Bldg. HVAC/Refurbish Air Handlers PH 2, Department of Labor, Boise — due 2026-09-29
4. **80** — City of Boise — Spare Inlet Pump (PRF 016) — due 2026-09-02

Several additional score-82 rows are historical DPW bid results in Boise/Kuna and therefore are useful contractor/bid intelligence rather than current bid opportunities.

## Audit conclusion

The dataset is structurally clean and the source expansion is producing meaningful volume. The main issue exposed by testing is lifecycle freshness: **9 records remain marked active even though their due dates have passed**. A future lifecycle/deduplication hardening sprint should automatically transition expired active items unless the source indicates an extension or updated due date.
