import csv
from pathlib import Path


def load_frequency(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    freq = {}
    with path.open(encoding="utf8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            w = r.get("word")
            rank = r.get("rank")
            if w and rank:
                try:
                    freq[w] = int(rank)
                except ValueError:
                    continue
    return freq
