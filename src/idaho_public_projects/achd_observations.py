"""Read-only ACHD reconciliation preview. Writes only JSON to stdout."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .collectors.achd import collect, observe_missing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("history", type=Path, help="Read-only snapshot of previously recorded opportunities")
    args = parser.parse_args()
    snapshot = json.loads(args.history.read_text())
    observations = observe_missing(snapshot["opportunities"], collect())
    print(json.dumps(observations, indent=2))


if __name__ == "__main__":
    main()
