from builder.entry_builder import WordEntryBuilder
from builder.config import CACHE_API_DIR, CACHE_WIKTIONARY_DIR
from builder.cefr_provider import get_level_from_rank
from pathlib import Path
import json

# Setup minimal maps
freq_map = {"apple": 500}
cefr_map = {"apple": "A1"}

builder = WordEntryBuilder(
    freq_map=freq_map,
    cefr_map=cefr_map,
    get_level_func=get_level_from_rank,
    cache_api_dir=CACHE_API_DIR,
    cache_wiktionary_dir=CACHE_WIKTIONARY_DIR
)

word = "apple"
print(f"Building entry for '{word}'...")
entry = builder.build(word)
print(json.dumps(entry, indent=2, ensure_ascii=False))
