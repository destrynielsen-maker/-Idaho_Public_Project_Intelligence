# Idaho Public Project Intelligence Roadmap

This roadmap keeps work in bounded checkpoints so each sprint can be tested, merged, and left in a clean state before the next source or feature is added.

## Completed foundation

### Checkpoint 0 — MVP pipeline
- City of Boise live collector
- Idaho Division of Public Works live collector
- project normalization, scoring, lifecycle/history fields
- RSS generation
- scheduled GitHub Actions collection
- bid-result / bidder intelligence from DPW

### Checkpoint 1 — Dashboard usability
- permit-dashboard-style light UI
- full-text project search
- source, stage, category, type, score and active/result filters
- due / posted / first-seen date filtering
- preset and custom date ranges
- sortable project columns
- result counts and reset controls

### Checkpoint 2 — ACHD live collection investigation
Outcome: externally blocked from the GitHub Actions runtime; production left unchanged.

What was verified:
- ACHD's public-notice page contains useful live procurement intelligence, including bid windows, solicitation types, contract/project numbers, locations, project scopes, bid-security language and bonding requirements.
- the existing parser handles saved ACHD notice fixtures correctly.
- a browser-style request from GitHub Actions still produced zero live ACHD records.
- the OpenGov public project-list fallback also remained client-rendered / empty to the collector.
- Boise and Idaho DPW continued to collect normally throughout the test.

Decision:
- do not merge an ineffective fetch workaround.
- keep the current fail-soft ACHD collector in place.
- revisit ACHD only when a stable official machine-readable endpoint, feed, export or other durable access path is identified.

### Checkpoint 3 — Idaho Purchasing / future solicitations
Completed successfully.

What was added:
- official State of Idaho machine-readable source: `/wp-json/wm4/v1/procurement-report`
- live collection of 40 Division of Purchasing records in GitHub Actions
- project name, agency, description, status, created/start/due/updated/completed dates
- RFP/RFQ/RFI/ITB number extraction from project names where available
- FUTURE / UPCOMING / AWARDED stage mapping
- JSON-schema fixture coverage in the test suite
- Idaho Purchasing records automatically flow into the existing Early Opportunities RSS feed

Validation result at completion:
- City of Boise: 5 records
- Idaho DPW: 80 records
- Idaho Purchasing: 40 records
- ACHD: 0 records / fail-soft
- 125 raw source records and 124 normalized opportunities

### Checkpoint 4A — Ada County procurement
Completed successfully.

What was added:
- authoritative Ada County Bonfire/Euna public procurement source
- public endpoint: `/PublicPortal/getOpenPublicOpportunitiesSectionData`
- stable project IDs, solicitation numbers, project titles and close dates
- direct links to individual Bonfire opportunity pages
- deterministic fixture coverage
- live pipeline wiring with fail-soft source isolation

Validation result at completion:
- Ada County: 3 open projects
- City of Boise: 5 records
- Idaho DPW: 80 records
- Idaho Purchasing: 40 records
- ACHD: 0 records / fail-soft
- 128 raw source records and 127 normalized opportunities

## Current checkpoint

### Checkpoint 4B — ITD construction / contracting opportunities
Goal: add Idaho Transportation Department opportunities that materially expand coverage beyond the DPW and Idaho Purchasing records already present.

Planned work:
- identify ITD's authoritative public construction / contracting sources
- separate genuinely new ITD opportunities from records already represented through DPW or Idaho Purchasing
- collect solicitation/project number, title, dates, location, stage and source links
- add fixture tests
- require successful live GitHub Actions collection before merge

Exit criteria:
- ITD contributes unique, useful records without creating duplicate project noise or degrading existing collectors; otherwise document the overlap/constraint and leave production stable

## Future checkpoints

### Checkpoint 4 — Treasure Valley agency expansion
Continue one source per sub-sprint after ITD:
1. Boise State / state campus projects not already fully represented through DPW
2. Boise School District and other major Treasure Valley school/public facility sources
3. Meridian, Nampa, Caldwell and other municipal procurement sources where they add material coverage beyond existing state/county feeds

Each source must pass fixture tests and a live GitHub Actions collection before merge.

### Checkpoint 5 — Project lifecycle and deduplication hardening
Goal: follow one project from early notice through bid and award instead of treating every source event as unrelated.

Planned work:
- cross-source project matching
- stronger stable IDs
- addendum/change detection
- stage transitions: FUTURE → DESIGN/RFQ → OPEN_BID → CLOSED → BID_RESULTS → AWARDED
- preserve first seen / last seen / last changed timestamps
- avoid duplicate records when the same project appears in multiple systems

### Checkpoint 6 — Award, bidder and contractor intelligence
Goal: make the system useful for sales targeting, not just bid discovery.

Planned work:
- normalize bidder / contractor names
- identify apparent low bidder and awardee
- contractor bid-frequency history
- project-value and bid-spread analysis
- searchable GC / contractor history
- contractor-focused RSS or dashboard filters

### Checkpoint 7 — Dashboard productivity features
Only after data coverage is solid:
- saved filter presets in the browser
- selectable visible columns
- CSV export of current filtered results
- quick views for Building / Facilities, Treasure Valley, Closing Soon, Early Opportunities and Awards
- stronger project-detail presentation without turning the dashboard into a heavy web application

### Checkpoint 8 — Publishing and repository cleanup
When repository settings are ready:
- rename repository to `Idaho_Public_Project_Intelligence` if needed
- make repository public if GitHub Pages is intended to be public
- enable/verify Pages deployment
- verify dashboard and RSS public URLs
- run final production smoke test

## Operating rule

Do not combine unrelated checkpoints. A normal sprint should change one source or one user-facing capability, run tests and live collection, merge only when clean, then stop at a stable checkpoint.
