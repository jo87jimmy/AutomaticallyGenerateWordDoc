import csv
from pathlib import Path


def load_cefr(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    mapping = {}
    with path.open(encoding="utf8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            w = r.get("word") or r.get("Word")
            level = r.get("level") or r.get("CEFR") or r.get("cefr")
            if w and level:
                mapping[w.lower()] = level.strip().upper()
    return mapping


def get_level_from_rank(rank: int | None) -> str:
    if not rank:
        return ""
    if rank < 1000:
        return "A1"
    if rank < 3000:
        return "A2"
    if rank < 6000:
        return "B1"
    if rank < 10000:
        return "B2"
    return "C1"
