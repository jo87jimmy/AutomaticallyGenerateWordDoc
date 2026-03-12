import json
import os
from pathlib import Path

import requests


def _cache_path(cache_dir: Path, text: str) -> Path:
    safe = str(abs(hash(text)))
    return cache_dir / f"zh_{safe}.json"


def translate_to_zh(text: str, cache_dir: Path) -> str:
    """
    Translate EN->ZH using LibreTranslate if LIBRETRANSLATE_URL is set.
    Falls back to empty string when not available.
    """
    if not text:
        return ""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(cache_dir, text)
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf8")).get("zh", "")
        except Exception:
            pass

    url = os.getenv("LIBRETRANSLATE_URL")
    if not url:
        return ""

    try:
        payload = {
            "q": text,
            "source": "en",
            "target": "zh",
            "format": "text",
        }
        r = requests.post(url.rstrip("/") + "/translate", json=payload, timeout=12)
        if r.status_code != 200:
            return ""
        data = r.json()
        zh = data.get("translatedText", "")
        cache_file.write_text(json.dumps({"zh": zh}, ensure_ascii=False), encoding="utf8")
        return zh
    except Exception:
        return ""
