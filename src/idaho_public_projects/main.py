from __future__ import annotations

import json
import os
from pathlib import Path

from .dashboard import write as write_dashboard
from .feeds import write_all
from .pipeline import run


def main():
    payload, sources = run()
    data_dir = Path("data")
    public_data = Path("public/data")
    feeds_dir = Path("public/feeds")
    data_dir.mkdir(parents=True, exist_ok=True)
    public_data.mkdir(parents=True, exist_ok=True)

    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    (data_dir / "opportunities.json").write_text(text, encoding="utf-8")
    (public_data / "opportunities.json").write_text(text, encoding="utf-8")
    (public_data / "sources.json").write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")

    repo = os.getenv("GITHUB_REPOSITORY", "destrynielsen-maker/-Idaho_Public_Project_Intelligence")
    owner, name = repo.split("/", 1)
    site_base = os.getenv("SITE_BASE_URL", f"https://{owner}.github.io/{name}/")
    write_all(payload["opportunities"], feeds_dir, site_base)
    write_dashboard(Path("public/index.html"))

    statuses = ", ".join(f"{s['source']}={s['status']}:{s['records_seen']}" for s in sources["collector_status"])
    print(f"Generated {len(payload['opportunities'])} opportunities. {statuses}")


if __name__ == "__main__":
    main()
