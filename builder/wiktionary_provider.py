import bz2
import json
import re
from pathlib import Path
from xml.etree.ElementTree import iterparse

ETYM_RE = re.compile(r"==+Etymology==+\n(.*?)(?:\n==|\Z)", re.S | re.I)
DERIVED_RE = re.compile(r"==+Derived terms==+\n(.*?)(?:\n==|\Z)", re.S | re.I)
PHRASES_RE = re.compile(r"==+Phrases==+\n(.*?)(?:\n==|\Z)", re.S | re.I)
LINK_RE = re.compile(r"\[\[(.*?)(?:\||\]\])")


def _extract_section(text: str, pattern: re.Pattern) -> list[str]:
    m = pattern.search(text)
    if not m:
        return []
    block = m.group(1)
    items = []
    for w in LINK_RE.findall(block):
        if w:
            items.append(w.strip())
    return items


def extract_wiktionary_fields(text: str) -> dict:
    ety = ETYM_RE.search(text)
    etymology = []
    if ety:
        desc = ety.group(1).strip().split("\n")[0][:300]
        if desc:
            etymology.append({"source": "Wiktionary", "description": desc})

    derived = _extract_section(text, DERIVED_RE)
    phrases = _extract_section(text, PHRASES_RE)

    return {
        "etymology": etymology,
        "derivatives": [{"word": w} for w in derived[:50]],
        "phrases": [{"text": w, "zh": "", "examples": []} for w in phrases[:50]],
    }


def _open_dump(path: Path):
    if path.suffix == ".bz2":
        return bz2.open(path, "rb")
    return path.open("rb")


def build_wiktionary_cache(dump_path: Path, words: set[str], cache_dir: Path) -> None:
    if not dump_path.exists():
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    words_lower = {w.lower() for w in words}

    with _open_dump(dump_path) as f:
        context = iterparse(f, events=("end",))
        for event, elem in context:
            if elem.tag.endswith("page"):
                title = elem.findtext("./{*}title")
                if not title:
                    elem.clear()
                    continue
                word = title.strip()
                if word.lower() in words_lower:
                    text = elem.findtext("./{*}revision/{*}text") or ""
                    fields = extract_wiktionary_fields(text)
                    out = {
                        "word": word,
                        **fields,
                    }
                    (cache_dir / f"{word.lower()}.json").write_text(
                        json.dumps(out, ensure_ascii=False), encoding="utf8"
                    )
                elem.clear()


def load_wiktionary_entry(word: str, cache_dir: Path) -> dict | None:
    p = cache_dir / f"{word.lower()}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf8"))
    except Exception:
        return None


def extract_phrases_from_dump(dump_path: Path, out_path: Path, limit: int = 100000) -> None:
    if not dump_path.exists():
        return
    phrases = []
    seen = set()
    with _open_dump(dump_path) as f:
        context = iterparse(f, events=("end",))
        for event, elem in context:
            if elem.tag.endswith("page"):
                title = elem.findtext("./{*}title")
                if title and " " in title:
                    t = title.strip()
                    if t not in seen:
                        seen.add(t)
                        phrases.append(t)
                        if len(phrases) >= limit:
                            out_path.write_text(json.dumps(phrases, ensure_ascii=False), encoding="utf8")
                            return
                elem.clear()
    out_path.write_text(json.dumps(phrases, ensure_ascii=False), encoding="utf8")
