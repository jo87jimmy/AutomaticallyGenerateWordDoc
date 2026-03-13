import json  # 匯入 JSON 模組
from itertools import count  # 匯入 count 以產生自動流水號
from concurrent.futures import ProcessPoolExecutor  # 匯入多行程執行器
from pathlib import Path  # 匯入 Path 以處理路徑
# 段落分隔
from tqdm import tqdm  # 匯入 tqdm 顯示進度條
# 段落分隔
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
from builder.entry_builder import build_entry  # 匯入條目建立函式
from builder.extractor import iter_word_batches  # 匯入批次取詞函式
from builder.frequency_provider import load_frequency  # 匯入字頻載入函式
from builder.wiktionary_provider import build_wiktionary_cache, extract_phrases_from_dump  # 匯入 Wiktionary 功能
# 段落分隔
# 段落分隔
_FREQ = {}  # 子行程共享的字頻對照表
_CEFR = {}  # 子行程共享的 CEFR 對照表
# 段落分隔
# 段落分隔
def _init_worker(freq_map, cefr_map):  # 子行程初始化函式
    global _FREQ, _CEFR  # 宣告使用全域變數
    _FREQ = freq_map  # 設定字頻對照表
    _CEFR = cefr_map  # 設定 CEFR 對照表
# 段落分隔
# 段落分隔
def _build_entry_worker(args):  # 子行程實際建構條目
    idx, word = args  # 解析參數
    return build_entry(  # 呼叫條目建立函式
        idx,  # 條目 ID
        word,  # 單字
        _FREQ,  # 字頻對照表
        _CEFR,  # CEFR 對照表
        get_level_from_rank,  # 依名次推估等級
        CACHE_API_DIR,  # API 快取目錄
        CACHE_API_DIR,  # reuse api cache dir for zh translations  # 中文翻譯共用 API 快取
        CACHE_WIKTIONARY_DIR,  # Wiktionary 快取目錄
    )  # 結束呼叫
# 段落分隔
# 段落分隔
def main():  # 主流程
    freq_map = load_frequency(DATASETS_DIR / "word_frequency.csv")  # 載入字頻資料
    cefr_map = load_cefr(DATASETS_DIR / "cefr.csv")  # 載入 CEFR 資料
# 段落分隔
    dataset = []  # 建立輸出資料集
    id_gen = count(1)  # 初始化自動流水號產生器，從 1 開始
# 段落分隔
    # Precompute wiktionary cache only if dump exists.  # 只有在 dump 存在時才預先建快取
    if WIKTIONARY_DUMP_PATH.exists():  # 檢查 dump 是否存在
        # If you want wiktionary cache for all words, you must scan all batches.  # 若要完整快取需掃描所有批次
        all_words = []  # 收集所有單字
        for batch in iter_word_batches(DOC_DIR, batch_size=50000):  # 以較大批次讀取
            all_words.extend(batch)  # 合併單字
        build_wiktionary_cache(WIKTIONARY_DUMP_PATH, set(all_words), CACHE_WIKTIONARY_DIR)  # 建立快取
        if not PHRASES_PATH.exists():  # 若片語檔不存在
            extract_phrases_from_dump(WIKTIONARY_DUMP_PATH, PHRASES_PATH, limit=100000)  # 擷取片語
# 段落分隔
    with ProcessPoolExecutor(max_workers=8, initializer=_init_worker, initargs=(freq_map, cefr_map)) as exe:  # 建立多行程池
        for batch in iter_word_batches(DOC_DIR, batch_size=10000):  # 逐批處理單字
            # 使用 id_gen 自動產生日後的流水號參數
            args = [(next(id_gen), w) for w in batch]  
            for item in tqdm(exe.map(_build_entry_worker, args), total=len(args)):  # 以進度條收集結果
                dataset.append(item)  # 加入資料集
# 段落分隔
    out_path = OUTPUT_DIR / "dictionary.json"  # 設定輸出檔案路徑
    out_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf8")  # 寫出 JSON
# 段落分隔
# 段落分隔
if __name__ == "__main__":  # 模組被直接執行時
    main()  # 執行主流程
