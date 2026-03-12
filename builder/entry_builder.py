from __future__ import annotations

from typing import Callable

from builder.dictionary_api_provider import (
    fetch_api,
    parse_examples,
    parse_meanings,
    parse_phonetics,
)
from builder.translate_provider import translate_to_zh
from builder.wordnet_provider import get_wordnet_meanings
from builder.wiktionary_provider import load_wiktionary_entry


def build_entry(
    idx: int,
    word: str,
    freq_map: dict[str, int],
    cefr_map: dict[str, str],
    get_level: Callable[[int | None], str],
    cache_api_dir,
    cache_zh_dir,
    cache_wiktionary_dir,
) -> dict:
    api_data = fetch_api(word, cache_api_dir)
    phonetics = parse_phonetics(api_data)
    examples = parse_examples(api_data)

    # auto-translate examples
    for ex in examples:
        if not ex.get("zh"):
            ex["zh"] = translate_to_zh(ex.get("en", ""), cache_zh_dir)

    meanings = parse_meanings(api_data)
    if not meanings:
        wordnet = get_wordnet_meanings(word)
        for m in wordnet:
            meanings.append({
                "pos": m["pos"],
                "definition": m["definition"],
                "synonyms": m["synonyms"],
                "examples": examples[:1],
            })

    for meaning in meanings:
        for ex in meaning.get("examples", []):
            if not ex.get("zh"):
                ex["zh"] = translate_to_zh(ex.get("en", ""), cache_zh_dir)

    wkt = load_wiktionary_entry(word, cache_wiktionary_dir) or {}
    phrases = wkt.get("phrases", [])
    derivatives = wkt.get("derivatives", [])
    etymology = wkt.get("etymology", [])

    frequency = freq_map.get(word)
    level = cefr_map.get(word) or get_level(frequency)

    return {
        "id": idx,
        "word": word,
        "phonetics": phonetics,
        "meanings": meanings,
        "phrases": phrases,
        "derivatives": derivatives,
        "etymology": etymology,
        "categories": [],
        "level": level,
        "frequency": frequency,
    }
