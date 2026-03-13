# builder/__init__.py
"""
Builder package for dictionary entries.
Exposes core APIs for easy access.
"""

from .dictionary_api_provider import (
    fetch_api,
    parse_examples,
    parse_meanings,
    parse_phonetics,
    translateText,
    clean_api_data,
    map_pos,
    fetch_phrases_from_api
)
from .cefr_provider import load_cefr, get_level_from_rank
from .frequency_provider import load_frequency, fetch_frequency_from_api
from .translate_provider import translate_to_zh
from .wordnet_provider import get_wordnet_meanings, get_wordnet_derivatives
from .wiktionary_provider import load_wiktionary_entry, build_wiktionary_cache, extract_phrases_from_dump
