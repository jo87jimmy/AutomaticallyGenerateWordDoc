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
    load_wiktionary_entry,
    fetch_frequency_from_api,
    fetch_phrases_from_api,
    get_wordnet_derivatives,
    fetch_google_dictionary_meanings,
    fetch_google_extras,
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
        start_id: int = 1,
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
        word = (
            word.lower().strip()
        )  # 確保輸入單字為小寫且無多餘空白，維持資料比對的一致性
        idx = next(self._id_counter)  # 自動取得下一個流水號

        # 1. 取得核心資料
        api_data = fetch_api(word, self.cache_api_dir)

        # 進行資料清理：移除 license/sourceUrls 並將 partOfSpeech 轉換為 pos (帶映射)
        # 確保後續解析模組處理的是經過正規化的乾淨資料
        api_data = clean_api_data(api_data)

        phonetics = parse_phonetics(api_data)
        examples = parse_examples(api_data)

        # 優先從 Google Translate 取得詞義 (因其分類與中文翻譯較符合直覺)
        # 依據使用者需求：先跑 meanings = https://translate.googleapis.com/translate_a 後才跑 meanings = parse_meanings(api_data)
        meanings = fetch_google_dictionary_meanings(word)

        # 2. 備援來源 (原 Dictionary API)
        if not meanings:
            meanings = parse_meanings(api_data)

        # 3. 備援來源 (WordNet)
        if not meanings:
            wordnet_data = get_wordnet_meanings(word)
            for m in wordnet_data:
                meanings.append(
                    {
                        "pos": m["pos"],
                        "definition": m["definition"],
                        "synonyms": m["synonyms"],
                        "examples": (
                            examples[:1] if examples else []
                        ),  # 只有在有例句時才加入，避免空值錯誤
                    }
                )

        # 3. 為例句加上中文翻譯
        for meaning in meanings:
            for ex in meaning.get("examples", []):
                if not ex.get("zh"):
                    ex["zh"] = translateText(ex.get("en", ""))
        # 3. 補充額外資訊 (Google Translate 優先提取)
        # 由於 Google 沒提供 Etymology，這部分仍需依賴 Wiktionary
        google_extras = fetch_google_extras(word)
        phrases = google_extras["phrases"]
        derivatives = google_extras["derivatives"]
        # 4. 補充額外資訊 (Wiktionary 補備援)
        wkt = load_wiktionary_entry(word, self.cache_wiktionary_dir) or {}

        # 若 Google 沒有抓到片語，則使用 Wiktionary 的
        if not phrases:
            phrases = wkt.get("phrases", [])
        # 若 Google 沒有抓到衍生詞，則使用 Wiktionary 的
        if not derivatives:
            derivatives = wkt.get("derivatives", [])

        # 辭源 (Google 無法提供，直接用 Wiktionary)
        etymology = wkt.get("etymology", [])

        # 5. 計算字頻與等級
        frequency = self.freq_map.get(word)
        if frequency is None:  # 若本地找不到字頻，嘗試從 API 抓取
            frequency = fetch_frequency_from_api(word)

        # 優先從 CEFR 對照表取得等級字串，若找不到則透過 get_level_func (即 get_level_from_rank) 依字頻計算
        level = self.cefr_map.get(word) or self.get_level_func(frequency)

        # 6. 組裝回傳條目，確保所有欄位皆有正確的數值
        return {
            "id": idx,
            "word": word,
            "phonetics": phonetics,
            "meanings": meanings,
            "phrases": phrases[:5],  # 限制最多五筆片語
            "derivatives": derivatives[:5],  # 限制最多五筆衍生詞
            "etymology": etymology[:2],  # 限制最多兩筆字源說明
            "categories": [],
            "level": level,  # CEFR 分級 (A1-C2)
            "frequency": frequency,  # 字頻名次
        }
