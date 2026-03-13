import csv  # 匯入 CSV 解析模組，用來讀取 CEFR 資料
from pathlib import Path  # 匯入 Path 以處理檔案路徑

# 讀取 CEFR 對照表並回傳字典
def load_cefr(path: Path) -> dict[str, str]:
    if not path.exists():  # 檔案不存在就直接回傳空對照
        return {}  # 回傳空字典表示沒有 CEFR 資料
    mapping = {}  # 建立空字典以累積 word -> level
    with path.open(encoding="utf8") as f:  # 以 UTF-8 編碼開啟檔案
        reader = csv.DictReader(f)  # 使用欄位名稱讀取每列
        for r in reader:  # 逐列處理 CSV 記錄
            w = r.get("word") or r.get("Word")  # 讀取單字欄位（支援大小寫）
            level = r.get("level") or r.get("CEFR") or r.get("cefr")  # 讀取 CEFR 等級欄位
            if w and level:  # 只有當單字與等級都存在時才納入
                mapping[w.lower()] = level.strip().upper()  # 將單字小寫化，等級去空白並大寫
    return mapping  # 回傳完成的 CEFR 對照字典

# 依頻率名次推估 CEFR 等級
def get_level_from_rank(rank: int | None) -> str:  
    if not rank:  # 名次為 None 或 0 時，視為未知
        return ""  # 回傳空字串表示沒有等級
    if rank < 1000:  # 前 1000 名屬於最基礎
        return "A1"  # 回傳 A1
    if rank < 3000:  # 1000~2999 名屬於入門
        return "A2"  # 回傳 A2
    if rank < 6000:  # 3000~5999 名屬於中級
        return "B1"  # 回傳 B1
    if rank < 10000:  # 6000~9999 名屬於中高級
        return "B2"  # 回傳 B2
    return "C1"  # 其他較低頻詞彙視為 C1
