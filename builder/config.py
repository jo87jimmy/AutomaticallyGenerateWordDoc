from pathlib import Path  # 匯入 Path 以組合與解析路徑
ROOT = Path(__file__).resolve().parent.parent  # 取得專案根目錄
# 輸出與快取路徑
DOC_DIR = ROOT / "doc"  # 文件輸出資料夾
CACHE_DIR = ROOT / "cache"  # 快取根資料夾
CACHE_API_DIR = CACHE_DIR / "api"  # API 回應快取位置
CACHE_WIKTIONARY_DIR = CACHE_DIR / "wiktionary"  # Wiktionary 快取位置
# 資料集與產出路徑
DATASETS_DIR = ROOT / "datasets"  # 資料集資料夾
OUTPUT_DIR = ROOT / "output"  # 產出檔案資料夾
INPUT_DIR = ROOT / "input"  # 輸入檔案資料夾
# 字頻與 CEFR 資料
FREQ_PATH = DATASETS_DIR / "word_frequency.csv"  # 字頻資料路徑
CEFR_PATH = DATASETS_DIR / "cefr.csv"  # CEFR 對照表路徑
# Wiktionary 與片語資料
WIKTIONARY_DUMP_PATH = DATASETS_DIR / "enwiktionary.xml.bz2"  # Wiktionary dump 路徑
PHRASES_PATH = DATASETS_DIR / "phrases.json"  # 片語資料路徑
# 確保資料夾存在
for p in [CACHE_API_DIR, CACHE_WIKTIONARY_DIR, OUTPUT_DIR]:  # 逐一確保必要資料夾存在
    p.mkdir(parents=True, exist_ok=True)  # 建立資料夾（含父層）且忽略已存在
