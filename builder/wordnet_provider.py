from builder import dictionary_api_provider

try:  # 嘗試載入 NLTK WordNet
    import nltk
    # 確保 WordNet 資源已下載，避免 LookupError
    try:
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
    except Exception:
        pass
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

# WordNet 詞性標記到標準名稱的映射，原因：WordNet 使用 'n', 'v', 'a' 等縮寫
WN_POS_MAP = {
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "s": "adjective",  # 衛星形容詞
    "r": "adverb"
}

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
        
        # 轉換 WordNet POS 為標準格式後再進行縮寫映射
        wn_pos = syn.pos()
        std_pos = WN_POS_MAP.get(wn_pos, wn_pos)
        pos_abbr = dictionary_api_provider.map_pos(std_pos)

        meanings.append({  # 新增一筆詞義
            "pos": pos_abbr,  # 詞性縮寫
            "definition": syn.definition(),  # 詞義定義
            "synonyms": uniq[:max_synonyms],  # 限制同義詞數量
        })  # 結束新增
    return meanings  # 回傳詞義清單

# 利用 WordNet 找出單字的衍生詞
def get_wordnet_derivatives(word: str) -> list[dict]:
    """
    找出與給定單字有形態學關聯的字詞 (例如: act -> action, actor)。
    """
    if not wn:
        return []
        
    derivatives = set()
    for syn in wn.synsets(word):
        for lemma in syn.lemmas():
            # 取得形態學關聯的形式
            for related in lemma.derivationally_related_forms():
                deriv_word = related.name().replace("_", " ")
                if deriv_word.lower() != word.lower():
                    derivatives.add(deriv_word)
    
    # 轉換成規定的格式並限制數量
    return [{"word": w} for w in sorted(list(derivatives))[:10]]
