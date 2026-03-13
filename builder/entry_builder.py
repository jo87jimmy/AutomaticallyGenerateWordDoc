import itertools
from typing import Callable, Optional, Dict, List, Any
from pathlib import Path

from . import (  # 透過相對匯入取得套件內部的核心功能，增強模組的可移植性
    fetch_api,
    parse_examples,
    parse_meanings,
    parse_phonetics,
    translateText,
    clean_api_data,
    get_wordnet_meanings,
    load_wiktionary_entry
)

class WordEntryBuilder:
    """
    單字條目建構器 (WordEntryBuilder)
    負責協調多個資料來源，封裝單字的完整資訊並管理自動流水號。
    符合資深架構師對「職責切分」與「封裝實作細節」的設計原則。
    """
    
    def __init__(
        self,
        freq_map: Dict[str, int],
        cefr_map: Dict[str, str],
        get_level_func: Callable[[Optional[int]], str],
        cache_api_dir: Path,
        cache_wiktionary_dir: Path,
        start_id: int = 1
    ):
        """
        初始化建構器。
        """
        self.freq_map = freq_map
        self.cefr_map = cefr_map
        self.get_level_func = get_level_func
        self.cache_api_dir = cache_api_dir
        self.cache_wiktionary_dir = cache_wiktionary_dir
        
        # 使用 count 產生器實現自動遞增的單字索引
        self._id_counter = itertools.count(start_id)

    def build(self, word: str) -> Dict[str, Any]:
        """
        根據給定的單字，建立完整的條目字典。
        每次呼叫時，內部的 ID 計數器會自動遞增。
        """
        idx = next(self._id_counter)  # 自動取得下一個流水號
        
        # 1. 取得核心資料
        api_data = fetch_api(word, self.cache_api_dir)
        
        # 進行資料清理：移除 license/sourceUrls 並將 partOfSpeech 轉換為 pos (帶映射)
        # 確保後續解析模組處理的是經過正規化的乾淨資料
        api_data = clean_api_data(api_data)

        phonetics = parse_phonetics(api_data)
        examples = parse_examples(api_data)
        meanings = parse_meanings(api_data)

        # 2. 備援來源 (WordNet)
        if not meanings:
            wordnet_data = get_wordnet_meanings(word)
            for m in wordnet_data:
                meanings.append({
                    "pos": m["pos"],
                    "definition": m["definition"],
                    "synonyms": m["synonyms"],
                    "examples": examples[:1],
                })

        # 3. 為例句加上中文翻譯
        for meaning in meanings:
            for ex in meaning.get("examples", []):
                if not ex.get("zh"):
                    ex["zh"] = translateText(ex.get("en", ""))

        # 4. 補充額外資訊
        wkt = load_wiktionary_entry(word, self.cache_wiktionary_dir) or {}
        phrases = wkt.get("phrases", [])
        derivatives = wkt.get("derivatives", [])
        etymology = wkt.get("etymology", [])

        # 5. 計算字頻與等級
        frequency = self.freq_map.get(word)
        level = self.cefr_map.get(word) or self.get_level_func(frequency)

        # 6. 組裝回傳條目
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
