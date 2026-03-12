try:
    from nltk.corpus import wordnet as wn
except Exception:  # nltk not installed
    wn = None

POS_MAP = {
    "n": "n.",
    "v": "v.",
    "a": "adj.",
    "s": "adj.",
    "r": "adv.",
}


def get_wordnet_meanings(word: str, max_synsets: int = 2, max_synonyms: int = 3) -> list[dict]:
    if not wn:
        return []
    meanings = []
    synsets = wn.synsets(word)
    for syn in synsets[:max_synsets]:
        synonyms = []
        for l in syn.lemmas():
            name = l.name().replace("_", " ")
            if name != word:
                synonyms.append(name)
        # de-dupe and cap
        uniq = []
        for s in synonyms:
            if s not in uniq:
                uniq.append(s)
        meanings.append({
            "pos": POS_MAP.get(syn.pos(), ""),
            "definition": syn.definition(),
            "synonyms": uniq[:max_synonyms],
        })
    return meanings
