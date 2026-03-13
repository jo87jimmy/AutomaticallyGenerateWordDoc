import json  # 匯入 JSON 模組
from pathlib import Path  # 匯入 Path 以處理路徑
from tqdm import tqdm  # 匯入 tqdm 顯示進度條
from builder.cefr_provider import get_level_from_rank, load_cefr  # 匯入 CEFR 相關函式
from builder.config import (  # 匯入專案設定路徑
    CACHE_API_DIR,  # API 快取目錄
    CACHE_WIKTIONARY_DIR,  # Wiktionary 快取目錄
    DATASETS_DIR,  # 資料集目錄
    DOC_DIR,  # 文件目錄
    OUTPUT_DIR,  # 輸出目錄
    PHRASES_PATH,  # 片語輸出路徑
    WIKTIONARY_DUMP_PATH,  # Wiktionary dump 路徑
)  # 結束匯入
from builder.entry_builder import WordEntryBuilder  # 匯入單字建構器類別
from builder.extractor import iter_word_batches  # 匯入批次取詞函式
from builder.frequency_provider import load_frequency  # 匯入字頻載入函式
from builder.wiktionary_provider import build_wiktionary_cache, extract_phrases_from_dump  # 匯入 Wiktionary 功能
from builder.wordnet_provider import get_wordnet_meanings  # 確保 WordNet 資源已載入


def main():  # 主流程
    freq_map = load_frequency(DATASETS_DIR / "word_frequency.csv")  # 載入字頻資料
    cefr_map = load_cefr(DATASETS_DIR / "cefr.csv")  # 載入 CEFR 資料

    if not freq_map or not cefr_map:
        print("提示：本地 datasets 資料夾（word_frequency.csv, cefr.csv）缺失或讀取失敗。")
        print("系統將自動切換至網路 API 備援模式（查詢速度會較慢）。")

    dataset = []  # 建立輸出資料集

    # Precompute wiktionary cache only if dump exists.  # 只有在 dump 存在時才預先建快取
    if WIKTIONARY_DUMP_PATH.exists():  # 檢查 dump 是否存在
        # If you want wiktionary cache for all words, you must scan all batches.  # 若要完整快取需掃描所有批次
        all_words = []  # 收集所有單字
        for batch in iter_word_batches(DOC_DIR, batch_size=50000):  # 以較大批次讀取
            all_words.extend(batch)  # 合併單字
        build_wiktionary_cache(WIKTIONARY_DUMP_PATH, set(all_words), CACHE_WIKTIONARY_DIR)  # 建立快取
        if not PHRASES_PATH.exists():  # 若片語檔不存在
            extract_phrases_from_dump(WIKTIONARY_DUMP_PATH, PHRASES_PATH, limit=100000)  # 擷取片語

    # 初始化單字建構器，封裝所有共用資源與自動索引邏輯
    builder = WordEntryBuilder(
        freq_map=freq_map,
        cefr_map=cefr_map,
        get_level_func=get_level_from_rank,
        cache_api_dir=CACHE_API_DIR,
        cache_wiktionary_dir=CACHE_WIKTIONARY_DIR
    )

    for batch in iter_word_batches(DOC_DIR, batch_size=10000):  # 逐批處理單字
        # 直接在主行程中循序處理，方便除錯與追蹤
        for word in tqdm(batch, desc="Building entries"):
            item = builder.build(word)  # 呼叫建構器自動建立條目（ID 會自動增加）
            dataset.append(item)  # 加入資料集

    out_path = OUTPUT_DIR / "dictionary.json"  # 設定輸出檔案路徑
    out_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf8")  # 寫出 JSON

if __name__ == "__main__":  # 模組被直接執行時
    main()  # 執行主流程
