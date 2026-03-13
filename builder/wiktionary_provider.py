import bz2  # 匯入 bz2 以讀取壓縮檔
import json  # 匯入 JSON 模組
import re  # 匯入正規表示式模組
import time  # 匯入時間模組
from pathlib import Path  # 匯入 Path 以處理路徑
from xml.etree.ElementTree import iterparse  # 匯入 XML 流式解析器

import requests  # 匯入 requests 以發送網路請求

# 優化正規表示式：支援標題空格（如 === Etymology ===）並增加對換行符的彈性
ETYM_RE = re.compile(r"==+\s*Etymology(?:\s+\d+)?\s*==+.*?\n(.*?)(?:\n\s*==+|\Z)", re.S | re.I)  # 擷取 Etymology 區段
DERIVED_RE = re.compile(r"==+\s*Derived terms\s*==+.*?\n(.*?)(?:\n\s*==+|\Z)", re.S | re.I)  # 擷取 Derived terms 區段
PHRASES_RE = re.compile(r"==+\s*Phrases\s*==+.*?\n(.*?)(?:\n\s*==+|\Z)", re.S | re.I)  # 擷取 Phrases 區段
LINK_RE = re.compile(r"\[\[(.*?)(?:\||\]\])")  # 擷取內部連結文字
# 清理 Wikitext：移除模板、連結、標籤並去除非文字符號
def _clean_wikitext(text: str) -> str:
    # 1. 移除註解
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    # 2. 移除 <ref> 標籤
    text = re.sub(r"<ref.*?>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<ref.*?>", "", text)
    # 3. 處理 [[link|text]] 或 [[text]]
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    # 4. 移除常見模板 {{...}}，但嘗試保留一些意義（如 {{m|...|word}}）
    # 簡單起見：先移除所有 {{...}} 區塊，若要更精準則需更複雜的遞迴解析
    # 這裡採用非貪婪匹配但要小心嵌套，目前採取逐層剝離或簡單移除
    while "{{" in text and "}}" in text:
        # 嘗試處理常見模板 {{inh|...|word|t=translation}}
        # 這裡簡易處理：只留下最後一段可能或是直接移除
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    
    # 5. 移除其餘標籤如 <small>, <big>
    text = re.sub(r"<[^>]+>", "", text)
    # 6. 去除多餘空白與換行
    text = re.sub(r"\s+", " ", text).strip()
    return text

# 依正規式擷取區段內的連結項目 (支援更深層的標題，如 ====)
def _extract_section(text: str, pattern: re.Pattern) -> list[str]:
    m = pattern.search(text)  # 搜尋符合的區段
    if not m:  # 若找不到區段
        return []  # 回傳空清單
    block = m.group(1)  # 取得區段內容
    items = []  # 建立項目清單
    for w in LINK_RE.findall(block):  # 逐一擷取連結文字
        if w:  # 有內容才加入
            items.append(w.strip())  # 去除空白後加入
    return items  # 回傳擷取結果
# 解析 Wiktionary 文字並回傳欄位
def extract_wiktionary_fields(text: str) -> dict:
    # 處理多個 Etymology 區段
    etymology = []
    for ety_match in ETYM_RE.finditer(text):
        block = ety_match.group(1).strip()
        # 跳過只有模板的行，找到包含文字的行
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        for line in lines:
            if not line.startswith("{{") or len(line) > 50: # 可能是帶有內容的行
                cleaned = _clean_wikitext(line)
                if len(cleaned) > 10:
                    etymology.append({"source": "Wiktionary", "description": cleaned[:400]})
                    break # 每個區段取第一條有效的描述
        if len(etymology) >= 2: # 最多取兩個區段
            break

    derived = _extract_section(text, DERIVED_RE)  # 擷取衍生字區段
    phrases = _extract_section(text, PHRASES_RE)  # 擷取片語區段

    return {  # 回傳結構化欄位
        "etymology": etymology,  # 字源資料
        "derivatives": [{"word": w} for w in derived[:50]],  # 衍生字（最多 50）
        "phrases": [{"text": w, "zh": "", "examples": []} for w in phrases[:50]],  # 片語（最多 50）
    }  # 結束回傳
# 依副檔名開啟 dump 檔
def _open_dump(path: Path):
    if path.suffix == ".bz2":  # 若是 bz2 壓縮
        return bz2.open(path, "rb")  # 以二進位開啟壓縮檔
    return path.open("rb")  # 以二進位開啟一般檔
# 建立 Wiktionary 快取
def build_wiktionary_cache(dump_path: Path, words: set[str], cache_dir: Path) -> None:
    if not dump_path.exists():  # dump 檔不存在就直接返回
        return  # 結束函式
    cache_dir.mkdir(parents=True, exist_ok=True)  # 確保快取資料夾存在
    words_lower = {w.lower() for w in words}  # 建立小寫單字集合

    with _open_dump(dump_path) as f:  # 開啟 dump 檔案
        context = iterparse(f, events=("end",))  # 以 end 事件流式解析
        for event, elem in context:  # 逐筆解析元素
            if elem.tag.endswith("page"):  # 只處理 page 節點
                title = elem.findtext("./{*}title")  # 取得標題
                if not title:  # 若無標題
                    elem.clear()  # 清除元素以釋放記憶體
                    continue  # 進入下一個元素
                word = title.strip()  # 清理標題文字
                if word.lower() in words_lower:  # 若是目標單字
                    text = elem.findtext("./{*}revision/{*}text") or ""  # 取得內文
                    fields = extract_wiktionary_fields(text)  # 擷取欄位
                    out = {  # 組合輸出資料
                        "word": word,  # 單字本體
                        **fields,  # 合併欄位
                    }  # 結束輸出資料
                    (cache_dir / f"{word.lower()}.json").write_text(  # 寫入快取檔
                        json.dumps(out, ensure_ascii=False), encoding="utf8"  # 序列化成 JSON
                    )  # 結束寫入
                elem.clear()  # 清除元素以釋放記憶體
# 從快取讀取 Wiktionary 資料，若無則嘗試從網路 API 抓取 (備援機制)
def load_wiktionary_entry(word: str, cache_dir: Path) -> dict | None:
    p = cache_dir / f"{word.lower()}.json"  # 取得快取檔案路徑
    
    # 1. 優先從本地快取讀取
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf8"))
        except Exception:
            pass

    # 2. 本地無快取，嘗試從網路 API 抓取 (更好、更靈活的方法)
    data = fetch_wiktionary_from_api(word)
    if data:
        # 寫入快取供下次使用
        cache_dir.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
        return data
        
    return None

# 透過網路 API 抓取 Wiktionary 的原始內容並解析
def fetch_wiktionary_from_api(word: str) -> dict | None:
    """
    從 Wiktionary MediaWiki API 抓取單字原始碼 (Wikitext) 並解析。
    這是當本地沒有 XML dump 時的最佳替代方案。
    """
    url = "https://en.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "format": "json",
        "titles": word,
        "redirects": 1
    }
    
    try:
        headers = {
            "User-Agent": "AntigravityDictionaryBuilder/1.0 (https://github.com/jo87jimmy/AutomaticallyGenerateWordDoc)"
        }
        print(f" [Wiktionary] Fetching '{word}' from API...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        res_data = response.json()
        pages = res_data.get("query", {}).get("pages", {})
        
        # 取得第一筆頁面內容
        for page_id, page_data in pages.items():
            if page_id == "-1": # 沒找到頁面
                return None
            
            revisions = page_data.get("revisions", [])
            if not revisions:
                return None
                
            text = revisions[0].get("*", "") # MediaWiki API 的內容欄位通常是 '*'
            fields = extract_wiktionary_fields(text)
            
            return {
                "word": word,
                **fields
            }
    except Exception as e:
        print(f"Wiktionary API error for '{word}': {e}")
        return None
    
    return None
# 從 dump 擷取片語清單
def extract_phrases_from_dump(dump_path: Path, out_path: Path, limit: int = 100000) -> None:
    if not dump_path.exists():  # dump 檔不存在就返回
        return  # 結束函式
    phrases = []  # 片語清單
    seen = set()  # 去重集合
    with _open_dump(dump_path) as f:  # 開啟 dump 檔
        context = iterparse(f, events=("end",))  # 流式解析
        for event, elem in context:  # 逐筆處理元素
            if elem.tag.endswith("page"):  # 只處理 page 節點
                title = elem.findtext("./{*}title")  # 取得標題
                if title and " " in title:  # 有空白表示可能是片語
                    t = title.strip()  # 清理標題
                    if t not in seen:  # 未出現過才加入
                        seen.add(t)  # 記錄為已見
                        phrases.append(t)  # 加入片語
                        if len(phrases) >= limit:  # 若達到上限
                            out_path.write_text(json.dumps(phrases, ensure_ascii=False), encoding="utf8")  # 寫入結果
                            return  # 結束函式
                elem.clear()  # 清除元素以釋放記憶體
    out_path.write_text(json.dumps(phrases, ensure_ascii=False), encoding="utf8")  # 寫入最終結果
