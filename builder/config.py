from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOC_DIR = ROOT / "doc"
CACHE_DIR = ROOT / "cache"
CACHE_API_DIR = CACHE_DIR / "api"
CACHE_WIKTIONARY_DIR = CACHE_DIR / "wiktionary"

DATASETS_DIR = ROOT / "datasets"
OUTPUT_DIR = ROOT / "output"
INPUT_DIR = ROOT / "input"

FREQ_PATH = DATASETS_DIR / "word_frequency.csv"
CEFR_PATH = DATASETS_DIR / "cefr.csv"

WIKTIONARY_DUMP_PATH = DATASETS_DIR / "enwiktionary.xml.bz2"
PHRASES_PATH = DATASETS_DIR / "phrases.json"

for p in [CACHE_API_DIR, CACHE_WIKTIONARY_DIR, OUTPUT_DIR]:
    p.mkdir(parents=True, exist_ok=True)
