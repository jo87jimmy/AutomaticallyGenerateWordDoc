import json  # 匯入 JSON 模組以序列化/反序列化資料
import os  # 匯入 OS 模組以處理作業系統相關功能
import time  # 匯入時間模組以控制請求節奏
from pathlib import Path  # 匯入 Path 以處理檔案路徑

import requests  # 匯入 requests 以發送 HTTP 請求
# Dictionary API 的基礎 URL
API = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"

def _cache_path(cache_dir: Path, word: str) -> Path:  # 組合快取檔案路徑
    return cache_dir / f"{word}.json"  # 回傳單字對應的快取檔名
# 取得 API 資料並快取
def fetch_api(word: str, cache_dir: Path, timeout: int = 12) -> dict | None:
    cache_dir.mkdir(parents=True, exist_ok=True)  # 確保快取資料夾存在
    cache_file = _cache_path(cache_dir, word)  # 計算快取檔案路徑
    if cache_file.exists():  # 若快取檔案已存在
        try:  # 嘗試讀取快取
            return json.loads(cache_file.read_text(encoding="utf8"))  # 讀取並解析快取 JSON
        except Exception:  # 讀取失敗就忽略
            pass  # 繼續走 API 請求流程
# 嘗試發送 API 請求
    try:  
        r = requests.get(API.format(word), timeout=timeout)  # 呼叫 Dictionary API
        if r.status_code != 200:  # HTTP 非成功狀態
            return None  # 回傳 None 表示失敗
        data = r.json()  # 解析回傳 JSON
        if isinstance(data, list) and data:  # API 可能回傳清單
            data = data[0]  # 取第一筆作為主要結果
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")  # 將資料寫入快取
        time.sleep(0.05)  # 稍作延遲避免過於頻繁
        return data  # 回傳取得的資料
    except Exception:  # 任何錯誤都視為失敗
        return None  # 回傳 None
# 解析音標與發音資訊
def parse_phonetics(data: dict | None) -> list[dict]:
    results = []  # 建立回傳清單
    if not data:  # 若資料為空
        return results  # 回傳空清單
    
    seen_texts = set()  # 用於紀錄已出現過的音標文字，避免重複
    
    for p in data.get("phonetics", []):  # 逐筆處理 phonetics
        text = p.get("text", "")  # 取出音標文字
        if not text:
            continue
            
        # 如果音標相同，則跳到下一筆
        if text in seen_texts:
            continue
            
        # 若已滿兩筆，且當前是不同的音標時則跳出
        # (能走到這裡代表是不同的音標文字)
        if len(results) >= 2:
            break
            
        results.append({  # 新增一筆音標資料
            "region": _detect_region(p),  # 偵測發音區域
            "text": text,  # 音標文字
            "audio": p.get("audio", ""),  # 音檔連結
        })
        seen_texts.add(text)  # 紀錄已處理過的文字
        
    return results  # 回傳音標清單
# 英文詞性對照表
_POS_MAP = {  
    "noun": "n.",  # 名詞
    "verb": "v.",  # 動詞
    "adjective": "adj.",  # 形容詞
    "adverb": "adv.",  # 副詞
    "pronoun": "pron.",  # 代名詞
    "preposition": "prep.",  # 介系詞
    "conjunction": "conj.",  # 連接詞
    "interjection": "int.",  # 感嘆詞
    "numeral": "num.",  # 數詞
    "article": "art.",  # 冠詞
    "determiner": "det.",  # 限定詞
    "auxiliary": "aux.",  # 助動詞
    "modal": "modal",  # 情態助動詞
}  # 結束詞性對照表

# 將詞性映射為縮寫
def map_pos(pos: str) -> str:
    if not pos:  # 詞性為空
        return ""  # 回傳空字串
    return _POS_MAP.get(pos.lower(), pos)  # 轉小寫後查表，找不到就原樣回傳

# 清理並正規化 API 資料
def clean_api_data(data: dict | None) -> dict | None:
    if not data:
        return data
    
    # 移除多餘欄位，節省記憶體與減少雜訊
    data.pop("sourceUrls", None)
    data.pop("license", None)
    
    # 正規化 meanings 中的欄位
    if "meanings" in data:
        for m in data["meanings"]:
            if "partOfSpeech" in m:
                # 取得原詞性，映射後存入 pos 欄位，並移除原 partOfSpeech
                m["pos"] = map_pos(m.get("partOfSpeech", ""))
                m.pop("partOfSpeech", None)
                
    return data

# 依音檔或欄位推測發音區域
def _detect_region(p: dict) -> str:
    region = p.get("region", "")  # 先取資料中的 region 欄位
    if region:  # 若已有區域資訊
        return region  # 直接回傳
    audio = (p.get("audio") or "").lower()  # 取音檔 URL 並轉小寫
    if "-us" in audio or "_us" in audio or "/us" in audio:  # 依音檔字串判斷美式
        return "us"  # 回傳 us
    if "-uk" in audio or "_uk" in audio or "/uk" in audio:  # 依音檔字串判斷英式
        return "uk"  # 回傳 uk
    return "uk"  # 其他情況回傳空字串

# 解析詞義與例句
def parse_meanings(data: dict | None) -> list[dict]:
    meanings = []  # 建立回傳清單
    if not data:  # 若資料為空
        return meanings  # 回傳空清單
    
    seen_pos = set()  # 用於紀錄已處理過的詞性，確保每個詞性只出現一次
    
    for m in data.get("meanings", []):  # 逐筆處理 meanings
        # 取得並映射詞性，優先嘗試已正規化的 pos 欄位
        p_val = m.get("pos") or m.get("partOfSpeech", "")
        pos = map_pos(p_val)
        
        # 若詞性已處理過或為空，則跳過 (同一個 pos 只取一個區塊)
        if not pos or pos in seen_pos:
            continue
            
        definitions = m.get("definitions", [])
        if not definitions:
            continue
            
        # 取該詞性的第一筆定義作為主要解釋
        first_def = definitions[0]
        
        # 收集同義詞：優先取 meaning 層級的，若無則取第一筆定義中的
        synonyms = m.get("synonyms", []) or []
        if not synonyms:
            synonyms = first_def.get("synonyms", []) or []
            
        # 尋找該詞性下的第一個可用例句
        examples = []
        for d in definitions:
            ex = d.get("example")
            if ex:
                zh = translateText(ex)  # 進行翻譯
                examples = [{"en": ex, "zh": zh}]  # 包裝成規定的物件格式
                break  # 同一個 pos 只取一個例句，找到即停止
                
        meanings.append({
            "pos": pos,  # 詞性 (如 n., v.)
            "definition": first_def.get("definition", ""),  # 英文定義
            "synonyms": synonyms,  # 同義詞清單
            "examples": examples,  # 例句清單 (最多一筆)
        })
        
        seen_pos.add(pos)  # 標記此詞性已處理
        
    return meanings  # 回傳詞義清單

# 線上翻譯文字 (使用 Google Translate 免費 API)
def translateText(text: str) -> str:
    if not text:  # 若文字為空則直接回傳
        return ""
    try:
        # 使用 Google Translate 的 gtx 客戶端 API (繁體中文)
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-TW",
            "dt": "t",
            "q": text
        }
        # 發送 GET 請求取得翻譯
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:  # 請求成功
            data = r.json()  # 解析 JSON
            if data and data[0]:  # 確保有回傳內容且有第一段資料
                # 組合翻譯結果，data[0] 是一個包含了各分句翻譯內容的清單
                return "".join(item[0] for item in data[0] if item[0])
        return ""
    except Exception as e:  # 發生網路或解析異常時
        print(f"Translation error: {e}")  # 印出錯誤日誌供後續除錯
        return ""  # 回傳空字串以防程式崩潰

# 解析所有例句 並進行翻譯 (限制解析兩個例句)
def parse_examples(data: dict | None) -> list[dict]:
    examples = []  # 建立回傳清單
    if not data:  # 若資料為空
        return examples  # 回傳空清單
    for m in data.get("meanings", []):  # 逐筆處理 meanings
        if len(examples) >= 2:  # 若外層循環已滿兩個則跳出
            break
        for d in m.get("definitions", []):  # 逐筆處理 definitions
            if len(examples) >= 2:  # 若內層循環已滿兩個則跳出
                break
            ex = d.get("example")  # 取得英文例句
            if ex:  # 若例句存在
                zh = translateText(ex)  # 呼叫翻譯函式取得繁體中文翻譯
                examples.append({"en": ex, "zh": zh})  # 加入回傳清單
    return examples  # 回傳例句清單
