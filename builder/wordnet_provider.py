from builder import dictionary_api_provider

try:  # 嘗試載入 NLTK WordNet
    from nltk.corpus import wordnet as wn  # 匯入 WordNet 資料庫
except Exception:  # nltk not installed  # NLTK 未安裝時
    wn = None  # 設定為 None 代表不可用

# POS_MAP = {  # WordNet 詞性縮寫對照
#     "n": "n.",  # 名詞
#     "v": "v.",  # 動詞
#     "a": "adj.",  # 形容詞
#     "s": "adj.",  # 形容詞（衛星形容詞）
#     "r": "adv.",  # 副詞
# }  # 結束對照表

# 取得 WordNet 詞義
def get_wordnet_meanings(word: str, max_synsets: int = 2, max_synonyms: int = 3) -> list[dict]:
    if not wn:  # WordNet 不可用
        return []  # 回傳空清單
    meanings = []  # 建立詞義清單
    synsets = wn.synsets(word)  # 取得同義詞集合
    for syn in synsets[:max_synsets]:  # 限制處理前幾個 synset
        synonyms = []  # 建立同義詞清單
        for l in syn.lemmas():  # 逐一處理 lemma
            name = l.name().replace("_", " ")  # 轉換底線為空白
            if name != word:  # 排除與原字相同的詞
                synonyms.append(name)  # 加入同義詞
        # de-dupe and cap  # 去重與限制數量
        uniq = []  # 建立去重清單
        for s in synonyms:  # 逐一處理同義詞
            if s not in uniq:  # 若尚未加入
                uniq.append(s)  # 加入清單
        meanings.append({  # 新增一筆詞義
            "pos": dictionary_api_provider._POS_MAP.get(syn.pos(), ""),  # 詞性縮寫
            "definition": syn.definition(),  # 詞義定義
            "synonyms": uniq[:max_synonyms],  # 限制同義詞數量
        })  # 結束新增
    return meanings  # 回傳詞義清單
