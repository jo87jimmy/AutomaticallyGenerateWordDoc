import csv  # 匯入 CSV 模組以讀取字頻資料
from pathlib import Path  # 匯入 Path 以處理檔案路徑
import requests  # 匯入 requests 以取得網路字頻

def load_frequency(path: Path) -> dict[str, int]:  # 讀取本地字頻資料並回傳字典
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
                    freq[w.lower().strip()] = int(rank)  # 設定字頻名次（鍵值小寫化並去空白）
                except ValueError:  # 若名次不是數字
                    continue  # 忽略此列
    return freq  # 回傳字頻對照表

def fetch_frequency_from_api(word: str) -> int | None:
    """
    透過 Datamuse API 取得單字的頻率資訊。
    回傳值為估計的名次 (rank)，名次越小代表越常見。
    """
    url = "https://api.datamuse.com/words"
    params = {"sp": word, "md": "f", "max": 1}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and "tags" in data[0]:
                for tag in data[0]["tags"]:
                    if tag.startswith("f:"):
                        # f: 表示每百萬字的出現頻率
                        # Datamuse 的 f 分數通常在 0.01 到 100 之間
                        # 我們將其轉換為一個概略的名次 (這裡只是一個基於經驗的簡易映射)
                        f_score = float(tag[2:])
                        if f_score > 50: return 500   # A1
                        if f_score > 10: return 2000  # A2
                        if f_score > 1:  return 5000  # B1
                        if f_score > 0.1: return 9000 # B2
                        return 15000 # C1
        return None
    except Exception:
        return None
