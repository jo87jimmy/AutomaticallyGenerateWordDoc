from __future__ import annotations  # 啟用前向型別註解
from typing import Callable  # 匯入 Callable 以標註可呼叫型別
from builder.dictionary_api_provider import (  # 匯入 Dictionary API 相關函式
    fetch_api,  # 取得 API 資料
    parse_examples,  # 解析例句
    parse_meanings,  # 解析詞義
    parse_phonetics,  # 解析音標
)  # 結束匯入清單
from builder.translate_provider import translate_to_zh  # 匯入英文翻譯成中文的函式
from builder.wordnet_provider import get_wordnet_meanings  # 匯入 WordNet 詞義擷取函式
from builder.wiktionary_provider import load_wiktionary_entry  # 匯入 Wiktionary 資料讀取函式
from builder.translate_provider import translateText  # 匯入英文翻譯成中文的函式

def build_entry(  # 建立單字完整條目
    idx: int,  # 單字索引
    word: str,  # 單字本體
    freq_map: dict[str, int],  # 字頻對照表
    cefr_map: dict[str, str],  # CEFR 對照表
    get_level: Callable[[int | None], str],  # 依字頻取得 CEFR 等級的方法
    cache_api_dir,  # API 快取資料夾
    cache_zh_dir,  # 中文翻譯快取資料夾
    cache_wiktionary_dir,  # Wiktionary 快取資料夾
) -> dict:  # 回傳條目字典
    api_data = fetch_api(word, cache_api_dir)  # 取得 Dictionary API 資料
    phonetics = parse_phonetics(api_data)  # 解析音標與發音資訊
    examples = parse_examples(api_data)  # 解析例句
    # auto-translate examples  # 自動翻譯例句
    # for ex in examples:  # 逐筆例句處理
    #     if not ex.get("zh"):  # 若尚未有中文
    #         ex["zh"] = translate_to_zh(ex.get("en", ""), cache_zh_dir)  # 翻譯並填入中文
    
    meanings = parse_meanings(api_data)  # 解析詞義
    if not meanings:  # 若 API 沒有詞義
        # 改用 WordNet 擷取
        wordnet = get_wordnet_meanings(word)
        for m in wordnet:  # 逐筆 WordNet 詞義
            meanings.append({  # 加入到詞義清單
                "pos": m["pos"],  # 詞性
                "definition": m["definition"],  # 英文定義
                "synonyms": m["synonyms"],  # 同義詞
                "examples": examples[:1],  # 取一筆例句
            })  # 結束新增

    # 為每個詞義與例句自動編列流水號，以利後端或前端展示時能有明確的索引
    for m_idx, meaning in enumerate(meanings, 1):  # 逐一處理詞義並取得索引
        meaning["id"] = m_idx  # 設定詞義的流水號
        for e_idx, ex in enumerate(meaning.get("examples", []), 1):  # 逐一處理該詞義下的例句
            ex["id"] = e_idx  # 設定例句的流水號
            if not ex.get("zh"):  # 若該例句尚未翻譯
                ex["zh"] = translateText(ex.get("en", ""))  # 執行自動翻譯
                # ex["zh"] = translate_to_zh(ex.get("en", ""), cache_zh_dir)  # 備用的翻譯方式

    wkt = load_wiktionary_entry(word, cache_wiktionary_dir) or {}  # 讀取 Wiktionary 資料
    phrases = wkt.get("phrases", [])  # 取得片語
    derivatives = wkt.get("derivatives", [])  # 取得衍生字
    etymology = wkt.get("etymology", [])  # 取得字源

    frequency = freq_map.get(word)  # 取得字頻
    level = cefr_map.get(word) or get_level(frequency)  # 取得 CEFR 等級（優先對照表）

    return {  # 回傳完整條目
        "id": idx,  # 條目 ID
        "word": word,  # 單字
        "phonetics": phonetics,  # 音標清單
        "meanings": meanings,  # 詞義清單
        "phrases": phrases,  # 片語清單
        "derivatives": derivatives,  # 衍生字清單
        "etymology": etymology,  # 字源資訊
        "categories": [],  # 類別（目前空白）
        "level": level,  # CEFR 等級
        "frequency": frequency,  # 字頻
    }  # 結束回傳
