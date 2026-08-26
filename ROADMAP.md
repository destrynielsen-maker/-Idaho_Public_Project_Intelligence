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

## Current checkpoint

### Checkpoint 3 — Idaho Purchasing / future solicitations
Goal: add State of Idaho procurement opportunities before formal construction bidding where possible.

Planned work:
- identify the public data source behind the dynamic Open & Future Solicitations page
- collect project name, agency, status, created/start/due/updated dates and description
- classify early-stage opportunities separately from active bids
- populate the Early Opportunities RSS feed with real records

Exit criteria:
- live State Purchasing records appear in GitHub Actions without degrading Boise/DPW collection; otherwise document the external constraint and leave production stable

## Future checkpoints

### Checkpoint 4 — Treasure Valley agency expansion
Add one source per sub-sprint, in this order unless source quality changes:
1. Ada County procurement
2. ITD construction / contracting opportunities relevant to Idaho and Treasure Valley
3. Boise State / state campus projects not already fully represented through DPW
4. Boise School District and other major Treasure Valley school/public facility sources
5. Meridian, Nampa, Caldwell and other municipal procurement sources where they add material coverage beyond existing state/county feeds

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
