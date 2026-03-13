import re  # 匯入正規表示式模組
from pathlib import Path  # 匯入 Path 以處理檔案路徑
WORD_RE = re.compile(r"[a-zA-Z]+")  # 編譯只匹配英文字母的正規表示式

def iter_words_from_md_folder(doc_dir: Path):  # 逐一從 markdown 檔案產生單字
    for path in sorted(doc_dir.glob("*.md")):  # 依檔名排序走訪所有 .md 檔
        text = path.read_text(encoding="utf8", errors="ignore")  # 讀取檔案內容（忽略編碼錯誤）
        for w in WORD_RE.findall(text.lower()):  # 以小寫擷取所有單字
            yield w  # 逐一輸出單字

def iter_word_batches(doc_dir: Path, batch_size: int = 10000):  # 以批次方式輸出不重複單字
    seen = set()  # 已見過單字集合
    batch = []  # 目前批次容器
    for w in iter_words_from_md_folder(doc_dir):  # 逐字取出
        if w in seen:  # 已出現過就跳過
            continue  # 直接進入下一個單字
        seen.add(w)  # 記錄為已見
        batch.append(w)  # 加入當前批次
        if len(batch) >= batch_size:  # 若達到批次大小
            yield batch  # 輸出批次
            batch = []  # 重新建立新批次
    if batch:  # 還有未輸出的批次
        yield batch  # 輸出最後一批
