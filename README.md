# Idaho Public Project Intelligence

Public-sector construction and procurement opportunity intelligence for Idaho, with an initial focus on Boise and the Treasure Valley.

## Initial public sources

- City of Boise JAGGAER public bid site
- Idaho Division of Public Works construction advertisements and bid results
- Idaho Division of Purchasing Open & Future Solicitations
- Ada County Highway District public notices / OpenGov procurement links

## Outputs

The scheduled GitHub Action collects and normalizes opportunities every six hours, preserves project history, generates a sortable static dashboard, and publishes RSS feeds:

- `all-public-projects.xml`
- `treasure-valley.xml`
- `construction.xml`
- `building-projects.xml`
- `materials-equipment.xml`
- `design-rfq.xml`
- `closing-14-days.xml`
- `new-this-week.xml`
- `awards.xml`
- `early-opportunities.xml`

The collector tracks source, agency, project, location, stage, solicitation type/number, due date, category, score, source link, contacts when public, first seen, and last seen. DPW bid-result records also retain bidder and base-bid information.

## Local run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m idaho_public_projects.main
```

## Publishing

GitHub Pages deployment is intentionally skipped while the repository is private. Once the repository is public, the same workflow will publish the generated `public/` directory through GitHub Pages.
