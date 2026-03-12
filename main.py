import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tqdm import tqdm

from builder.cefr_provider import get_level_from_rank, load_cefr
from builder.config import (
    CACHE_API_DIR,
    CACHE_WIKTIONARY_DIR,
    DATASETS_DIR,
    DOC_DIR,
    OUTPUT_DIR,
    PHRASES_PATH,
    WIKTIONARY_DUMP_PATH,
)
from builder.entry_builder import build_entry
from builder.extractor import iter_word_batches
from builder.frequency_provider import load_frequency
from builder.wiktionary_provider import build_wiktionary_cache, extract_phrases_from_dump


_FREQ = {}
_CEFR = {}


def _init_worker(freq_map, cefr_map):
    global _FREQ, _CEFR
    _FREQ = freq_map
    _CEFR = cefr_map


def _build_entry_worker(args):
    idx, word = args
    return build_entry(
        idx,
        word,
        _FREQ,
        _CEFR,
        get_level_from_rank,
        CACHE_API_DIR,
        CACHE_API_DIR,  # reuse api cache dir for zh translations
        CACHE_WIKTIONARY_DIR,
    )


def main():
    freq_map = load_frequency(DATASETS_DIR / "word_frequency.csv")
    cefr_map = load_cefr(DATASETS_DIR / "cefr.csv")

    dataset = []
    idx = 1

    # Precompute wiktionary cache only if dump exists.
    if WIKTIONARY_DUMP_PATH.exists():
        # If you want wiktionary cache for all words, you must scan all batches.
        all_words = []
        for batch in iter_word_batches(DOC_DIR, batch_size=50000):
            all_words.extend(batch)
        build_wiktionary_cache(WIKTIONARY_DUMP_PATH, set(all_words), CACHE_WIKTIONARY_DIR)
        if not PHRASES_PATH.exists():
            extract_phrases_from_dump(WIKTIONARY_DUMP_PATH, PHRASES_PATH, limit=100000)

    with ProcessPoolExecutor(max_workers=8, initializer=_init_worker, initargs=(freq_map, cefr_map)) as exe:
        for batch in iter_word_batches(DOC_DIR, batch_size=10000):
            args = [(idx + i, w) for i, w in enumerate(batch)]
            for item in tqdm(exe.map(_build_entry_worker, args), total=len(args)):
                dataset.append(item)
            idx += len(batch)

    out_path = OUTPUT_DIR / "dictionary.json"
    out_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
