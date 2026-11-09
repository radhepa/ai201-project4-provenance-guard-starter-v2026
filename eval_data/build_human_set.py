#!/usr/bin/env python3
"""
Build the known-human evaluation set from Project Gutenberg.

    python eval_data/build_human_set.py

Every passage comes from a book published before 1930, so no language model
could have written it. The selection is mechanical, fixed before any scoring:
from each book's body text, consecutive paragraphs are joined into chunks of
60-200 words, and the chunk nearest each fixed position (a fraction of the way
through the book) is taken. Nothing is hand-picked after seeing a score.

A second, disjoint calibration split takes the chunks at 20% and 80% through
every book. Only the calibration split is used to set the style-signal
constants in config.py; the evaluation split is never used for tuning.

Downloads go to .cache/gutenberg/ (gitignored); the outputs are
eval_data/human_samples.json (evaluation) and
eval_data/calibration_human.json (calibration), both committed.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "gutenberg"
OUT = Path(__file__).resolve().parent / "human_samples.json"
CALIBRATION_OUT = Path(__file__).resolve().parent / "calibration_human.json"
CALIBRATION_POSITIONS = [0.2, 0.8]

# (gutenberg id, first published, plain?, positions through the book)
# "plain" marks writing in short sentences with common words: the case the
# model signal is most likely to accuse.
BOOKS = [
    (2397, 1903, False, [0.35, 0.65]),   # Helen Keller, The Story of My Life
    (2376, 1901, True, [0.35, 0.65]),    # Booker T. Washington, Up from Slavery
    (14668, 1879, True, [0.35, 0.65]),   # McGuffey's Second Eclectic Reader
    (55, 1900, True, [0.35, 0.65]),      # L. Frank Baum, The Wonderful Wizard of Oz
    (20203, 1791, False, [0.35, 0.65]),  # Autobiography of Benjamin Franklin
    (242, 1918, False, [0.35, 0.65]),    # Willa Cather, My Antonia
    (2591, 1812, True, [0.35, 0.65]),    # Grimms' Fairy Tales (19th-c. translation)
    (45, 1908, False, [0.5]),            # L. M. Montgomery, Anne of Green Gables
    (14640, 1879, True, [0.5]),          # McGuffey's First Eclectic Reader
    (113, 1911, False, [0.5]),           # Frances Hodgson Burnett, The Secret Garden
    (1342, 1813, False, [0.5]),          # Jane Austen, Pride and Prejudice
    (12, 1871, False, [0.5]),            # Lewis Carroll, Through the Looking-Glass
    (1260, 1847, False, [0.5]),          # Charlotte Bronte, Jane Eyre
]

MIN_WORDS, MAX_WORDS = 60, 200


def fetch(book_id: int) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"pg{book_id}.txt"
    if not path.exists():
        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        with urllib.request.urlopen(url, timeout=60) as resp:
            path.write_bytes(resp.read())
    return path.read_text(encoding="utf-8-sig", errors="replace")


def header(text: str, field: str) -> str:
    match = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def body(text: str) -> str:
    start = re.search(r"\*\*\* ?START OF.*?\*\*\*", text)
    end = re.search(r"\*\*\* ?END OF.*?\*\*\*", text)
    return text[start.end() if start else 0:end.start() if end else len(text)]


def is_prose(paragraph: str) -> bool:
    """Drop headings, illustrations, tables of contents and verse-like lines."""
    if paragraph.startswith("[") or not re.search(r"[a-z]", paragraph):
        return False
    lines = paragraph.splitlines()
    if len(lines) > 2 and sum(len(l) < 40 for l in lines) > len(lines) / 2:
        return False  # mostly short lines: verse, lists, contents
    return paragraph.rstrip()[-1:] in '.!?"”\''


def chunks(text: str) -> list[str]:
    paragraphs = [re.sub(r"\s+", " ", p).strip()
                  for p in re.split(r"\n\s*\n", body(text))]
    out, current = [], []
    for p in paragraphs:
        if not p or not is_prose(p) or len(p.split()) > MAX_WORDS:
            current = []  # a non-prose break ends the chunk
            continue
        current.append(p)
        words = sum(len(c.split()) for c in current)
        if words >= MIN_WORDS:
            if words <= MAX_WORDS:
                out.append(" ".join(current))
            current = []
    return out


def sample(book_id, year, plain, text, found, pos, kind):
    return {
        "id": f"{kind}_{book_id}_{int(pos * 100)}",
        "source": f"Project Gutenberg #{book_id}",
        "title": header(text, "Title"),
        "author": header(text, "Author"),
        "first_published": year,
        "plain": plain,
        "provenance": "human (published before 1930)",
        "text": found[min(int(pos * len(found)), len(found) - 1)],
    }


def main() -> int:
    samples, calibration = [], []
    for book_id, year, plain, positions in BOOKS:
        text = fetch(book_id)
        found = chunks(text)
        if not found:
            print(f"no usable chunk in {book_id}", file=sys.stderr)
            return 1
        samples += [sample(book_id, year, plain, text, found, p, "human")
                    for p in positions]
        calibration += [sample(book_id, year, plain, text, found, p, "calib")
                        for p in CALIBRATION_POSITIONS]
    eval_texts = {s["text"] for s in samples}
    calibration = [c for c in calibration if c["text"] not in eval_texts]
    for path, rows in ((OUT, samples), (CALIBRATION_OUT, calibration)):
        path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(f"wrote {len(rows)} passages to {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
