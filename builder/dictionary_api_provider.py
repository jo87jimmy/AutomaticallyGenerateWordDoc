import json
import os
import time
from pathlib import Path

import requests

API = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"


def _cache_path(cache_dir: Path, word: str) -> Path:
    return cache_dir / f"{word}.json"


def fetch_api(word: str, cache_dir: Path, timeout: int = 12) -> dict | None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(cache_dir, word)
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf8"))
        except Exception:
            pass

    try:
        r = requests.get(API.format(word), timeout=timeout)
        if r.status_code != 200:
            return None
        data = r.json()
        if isinstance(data, list) and data:
            data = data[0]
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
        time.sleep(0.05)
        return data
    except Exception:
        return None


def parse_phonetics(data: dict | None) -> list[dict]:
    results = []
    if not data:
        return results
    for p in data.get("phonetics", []):
        text = p.get("text", "")
        if text:
            results.append({
                "region": _detect_region(p),
                "text": text,
                "audio": p.get("audio", ""),
            })
    return results


_POS_MAP = {
    "noun": "n.",
    "verb": "v.",
    "adjective": "adj.",
    "adverb": "adv.",
    "pronoun": "pron.",
    "preposition": "prep.",
    "conjunction": "conj.",
    "interjection": "int.",
    "numeral": "num.",
    "article": "art.",
    "determiner": "det.",
    "auxiliary": "aux.",
    "modal": "modal",
}


def _map_pos(pos: str) -> str:
    if not pos:
        return ""
    return _POS_MAP.get(pos.lower(), pos)


def _detect_region(p: dict) -> str:
    region = p.get("region", "")
    if region:
        return region
    audio = (p.get("audio") or "").lower()
    if "-us" in audio or "_us" in audio or "/us" in audio:
        return "us"
    if "-uk" in audio or "_uk" in audio or "/uk" in audio:
        return "uk"
    return ""


def parse_meanings(data: dict | None) -> list[dict]:
    meanings = []
    if not data:
        return meanings
    for m in data.get("meanings", []):
        pos = _map_pos(m.get("partOfSpeech", ""))
        for d in m.get("definitions", []):
            ex = d.get("example")
            meanings.append({
                "pos": pos,
                "definition": d.get("definition", ""),
                "synonyms": d.get("synonyms", []) or [],
                "examples": [{"en": ex, "zh": ""}] if ex else [],
            })
    return meanings


def parse_examples(data: dict | None) -> list[dict]:
    examples = []
    if not data:
        return examples
    for m in data.get("meanings", []):
        for d in m.get("definitions", []):
            ex = d.get("example")
            if ex:
                examples.append({"en": ex, "zh": ""})
    return examples
