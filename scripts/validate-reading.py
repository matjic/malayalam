"""Check digital textbook links, anchors, tables, and source-page coverage."""

import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

DOCS = Path(__file__).resolve().parents[1] / 'docs'


def validate_tables(text, name):
    """Check every pipe table, including indented tables and missing headers."""
    errors = []
    # Keep line numbers stable while removing source annotations and other HTML.
    clean = re.sub(r'<!--.*?-->', lambda m: '\n' * m[0].count('\n'), text, flags=re.S)
    lines = clean.splitlines()
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith('|'):
            index += 1
            continue
        start = index
        rows = []
        while index < len(lines) and lines[index].lstrip().startswith('|'):
            row = lines[index].strip()
            if not row.endswith('|'):
                errors.append(f'{name}:{index + 1}: table row needs a closing pipe')
            rows.append([cell.strip() for cell in re.split(r'(?<!\\)\|', row)[1:-1]])
            index += 1
        width = len(rows[0])
        if len(rows) < 2 or not all(re.fullmatch(r':?-{3,}:?', cell) for cell in rows[1]):
            errors.append(f'{name}:{start + 1}: table needs a header and separator row')
        for column, cell in enumerate(rows[0], 1):
            if not re.sub(r'<[^>]*>', '', cell).strip():
                errors.append(f'{name}:{start + 1}: table header {column} is empty')
        for offset, row in enumerate(rows):
            if len(row) != width:
                errors.append(f'{name}:{start + offset + 1}: table row has {len(row)} cells, expected {width}')
    return errors


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
        errors.extend(validate_tables(text, path.name))

    if sorted(pages) != list(range(1, 558)):
        missing = sorted(set(range(1, 558)) - set(pages))
        repeated = [key for key, count in Counter(pages).items() if count > 1]
        errors.append(f'Source pages must occur exactly once: missing={missing}, repeated={repeated}')
    for path, text in texts.items():
        targets = re.findall(r'\]\(([^)]+)\)', text)
        targets += re.findall(r'<(?:img|a|audio|video|source)\b[^>]*\b(?:src|href)="([^"]+)"', text)
        for target in targets:
            if re.match(r'(?:https?:|mailto:|data:|//)', target):
                continue
            links += 1
            file, _, fragment = target.partition('#')
            destination = (path.parent / unquote(file)).resolve() if file else path.resolve()
            # These books are generated into dist/site during deployment.
            if destination in {DOCS / "malayalam.epub", DOCS / "malayalam.pdf"}:
                continue
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
