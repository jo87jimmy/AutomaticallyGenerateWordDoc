import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from builder.wiktionary_provider import fetch_wiktionary_from_api
import json

word = "apple"
print(f"Fetching Wiktionary for '{word}'...")
data = fetch_wiktionary_from_api(word)
print(json.dumps(data, indent=2, ensure_ascii=False))
