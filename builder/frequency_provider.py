import csv  # 匯入 CSV 模組以讀取字頻資料
from pathlib import Path  # 匯入 Path 以處理檔案路徑

def load_frequency(path: Path) -> dict[str, int]:  # 讀取字頻資料並回傳字典
    if not path.exists():  # 檔案不存在就回傳空字典
        return {}  # 沒有字頻資料
    freq = {}  # 建立字頻對照表
    with path.open(encoding="utf8") as f:  # 以 UTF-8 編碼開啟檔案
        reader = csv.DictReader(f)  # 以欄位名稱讀取
        for r in reader:  # 逐列讀取
            w = r.get("word")  # 取得單字
            rank = r.get("rank")  # 取得名次
            if w and rank:  # 單字與名次都存在才處理
                try:  # 嘗試轉成整數
                    freq[w] = int(rank)  # 設定字頻名次
                except ValueError:  # 若名次不是數字
                    continue  # 忽略此列
    return freq  # 回傳字頻對照表
