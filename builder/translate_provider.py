import json  # 匯入 JSON 模組
import os  # 匯入 OS 模組以讀取環境變數
from pathlib import Path  # 匯入 Path 以處理路徑

import requests  # 匯入 requests 以發送 HTTP 請求

def _cache_path(cache_dir: Path, text: str) -> Path:  # 產生翻譯快取檔案路徑
    safe = str(abs(hash(text)))  # 使用雜湊值避免檔名問題
    return cache_dir / f"zh_{safe}.json"  # 回傳快取檔案路徑

def translate_to_zh(text: str, cache_dir: Path) -> str:  # 將英文翻譯成中文
    """  # 文件字串開始
    Translate EN->ZH using LibreTranslate if LIBRETRANSLATE_URL is set.  # 說明翻譯方式
    Falls back to empty string when not available.  # 若不可用則回傳空字串
    """  # 文件字串結束
    if not text:  # 若文字為空
        return ""  # 回傳空字串
    cache_dir.mkdir(parents=True, exist_ok=True)  # 確保快取資料夾存在
    cache_file = _cache_path(cache_dir, text)  # 計算快取檔案路徑
    if cache_file.exists():  # 若快取檔案存在
        try:  # 嘗試讀取快取
            return json.loads(cache_file.read_text(encoding="utf8")).get("zh", "")  # 取出中文
        except Exception:  # 讀取失敗就忽略
            pass  # 走 API 翻譯流程

    url = os.getenv("LIBRETRANSLATE_URL")  # 取得 LibreTranslate 服務 URL
    if not url:  # 若未設定 URL
        return ""  # 回傳空字串

    try:  # 嘗試呼叫翻譯 API
        payload = {  # 組合請求資料
            "q": text,  # 需要翻譯的文本
            "source": "en",  # 來源語言
            "target": "zh",  # 目標語言
            "format": "text",  # 文字格式
        }  # 結束 payload
        r = requests.post(url.rstrip("/") + "/translate", json=payload, timeout=12)  # 發送翻譯請求
        if r.status_code != 200:  # 回應狀態非成功
            return ""  # 回傳空字串
        data = r.json()  # 解析回應 JSON
        zh = data.get("translatedText", "")  # 取得翻譯結果
        cache_file.write_text(json.dumps({"zh": zh}, ensure_ascii=False), encoding="utf8")  # 寫入快取
        return zh  # 回傳翻譯結果
    except Exception:  # 任何錯誤都視為失敗
        return ""  # 回傳空字串
