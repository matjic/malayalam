"""Shared reading sequence for the textbook and added practice lessons."""

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / 'docs'
PRACTICE_AFTER = {
    'alphabet.md': 'practice-pronunciation.md',
    'lesson2.md': 'practice-sandhi.md',
    'lesson7.md': 'practice-dialogues.md',
}


def reading_documents():
    book = []
    for path in DOCS.glob('*.md'):
        pages = re.findall(r'Source: PDF page (\d+)', path.read_text())
        if pages:
            book.append((min(map(int, pages)), path))
    result = []
    for _, path in sorted(book):
        result.append(path)
        if path.name in PRACTICE_AFTER:
            practice = DOCS / PRACTICE_AFTER[path.name]
            if not practice.exists():
                raise ValueError(f'Missing practice lesson: {practice.name}')
            result.append(practice)
    return result
