import bz2  # 匯入 bz2 以讀取壓縮檔
import json  # 匯入 JSON 模組
import re  # 匯入正規表示式模組
from pathlib import Path  # 匯入 Path 以處理路徑
from xml.etree.ElementTree import iterparse  # 匯入 XML 流式解析器

ETYM_RE = re.compile(r"==+Etymology==+\n(.*?)(?:\n==|\Z)", re.S | re.I)  # 擷取 Etymology 區段
DERIVED_RE = re.compile(r"==+Derived terms==+\n(.*?)(?:\n==|\Z)", re.S | re.I)  # 擷取 Derived terms 區段
PHRASES_RE = re.compile(r"==+Phrases==+\n(.*?)(?:\n==|\Z)", re.S | re.I)  # 擷取 Phrases 區段
LINK_RE = re.compile(r"\[\[(.*?)(?:\||\]\])")  # 擷取內部連結文字
# 依正規式擷取區段內的連結項目
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
    ety = ETYM_RE.search(text)  # 搜尋字源區段
    etymology = []  # 建立字源清單
    if ety:  # 找到字源區段
        desc = ety.group(1).strip().split("\n")[0][:300]  # 取第一行並限制長度
        if desc:  # 有描述內容才加入
            etymology.append({"source": "Wiktionary", "description": desc})  # 新增字源描述

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
# 從快取讀取 Wiktionary 資料
def load_wiktionary_entry(word: str, cache_dir: Path) -> dict | None:
    p = cache_dir / f"{word.lower()}.json"  # 取得快取檔案路徑
    if not p.exists():  # 檔案不存在就回傳 None
        return None  # 表示沒有資料
    try:  # 嘗試讀取並解析 JSON
        return json.loads(p.read_text(encoding="utf8"))  # 回傳解析結果
    except Exception:  # 讀取失敗
        return None  # 回傳 None
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
