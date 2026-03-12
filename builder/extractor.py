import re
from pathlib import Path

WORD_RE = re.compile(r"[a-zA-Z]+")


def iter_words_from_md_folder(doc_dir: Path):
    for path in sorted(doc_dir.glob("*.md")):
        text = path.read_text(encoding="utf8", errors="ignore")
        for w in WORD_RE.findall(text.lower()):
            yield w


def iter_word_batches(doc_dir: Path, batch_size: int = 10000):
    seen = set()
    batch = []
    for w in iter_words_from_md_folder(doc_dir):
        if w in seen:
            continue
        seen.add(w)
        batch.append(w)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
