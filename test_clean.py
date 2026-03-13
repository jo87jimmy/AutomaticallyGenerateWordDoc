from builder.wiktionary_provider import _clean_wikitext

text = "{{etymon|en|id=Q89|:inh|enm:appel<id:apple>|tree=1}}\nThe noun is derived from {{inh|en|enm|appel}}."
cleaned = _clean_wikitext(text)
print(f"Original: {text}")
print(f"Cleaned: '{cleaned}'")
