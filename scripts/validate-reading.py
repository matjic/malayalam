"""Check digital textbook links, anchors, tables, and source-page coverage."""

import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

DOCS = Path(__file__).resolve().parents[1] / 'docs'


def main():
    errors, pages, links, sections = [], [], 0, 0
    texts = {path: path.read_text() for path in DOCS.glob('*.md')}
    anchors = {}
    for path, text in texts.items():
        ids = re.findall(r'<a id="([^"]+)"></a>', text)
        repeated = [key for key, count in Counter(ids).items() if count > 1]
        errors.extend(f'{path.name}: duplicate anchor {key}' for key in repeated)
        anchors[path] = set(ids)
        # Existing Docsify heading links use its punctuation-stripping slug.
        for heading in re.findall(r'^#+ (.+)$', text, re.M):
            slug = re.sub(r'[^\w\u0d00-\u0d7f\- ]', '', heading.lower()).replace(' ', '-')
            anchors[path].add(slug)
        sections += len([key for key in ids if key.startswith('section-')])
        pages.extend(map(int, re.findall(r'Source: PDF page (\d+)', text)))
        if '\ufffd' in text:
            errors.append(f'{path.name}: Unicode replacement character')
        # HTML source comments may contain punctuation or appear inside cells.
        clean = re.sub(r'<!--.*?-->', '', text, flags=re.S)
        width = None
        lines = clean.splitlines()
        for index, line in enumerate(lines):
            if not line.startswith('|'):
                width = None
                continue
            cells = re.split(r'(?<!\\)\|', line.rstrip())
            count = len(cells) - 2
            if index + 1 < len(lines) and re.fullmatch(r'\|[ :|\-]+\|', lines[index + 1]):
                width = count
            elif width is not None and count != width:
                errors.append(f'{path.name}:{index + 1}: table row has {count} cells, expected {width}')

    if sorted(pages) != list(range(1, 558)):
        missing = sorted(set(range(1, 558)) - set(pages))
        repeated = [key for key, count in Counter(pages).items() if count > 1]
        errors.append(f'Source pages must occur exactly once: missing={missing}, repeated={repeated}')
    for path, text in texts.items():
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if re.match(r'(?:https?:|mailto:|data:|//)', target):
                continue
            links += 1
            file, _, fragment = target.partition('#')
            destination = (path.parent / unquote(file)).resolve() if file else path.resolve()
            if not destination.exists():
                errors.append(f'{path.name}: missing link/image {target}')
            elif fragment and destination.suffix == '.md' and unquote(fragment) not in anchors.get(destination, set()):
                errors.append(f'{path.name}: missing fragment {target}')
    for error in errors:
        print(error)
    print(f'Checked {len(texts)} documents, {links} local links/images, {sections} numbered sections, and {len(pages)} source pages.')
    if errors:
        raise SystemExit(1)
    print('Digital reading checks passed.')


if __name__ == '__main__':
    main()
