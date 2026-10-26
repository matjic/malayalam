#!/usr/bin/env python3
"""Validate book PDF text, navigation, font embedding, and page bounds."""
import argparse
from pathlib import Path
import re
import pymupdf
from book_export import ROOT, book_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', nargs='?', type=Path, default=ROOT / 'dist/malayalam.pdf')
    args = parser.parse_args()
    doc = pymupdf.open(args.pdf)
    assert not doc.is_encrypted
    assert len(doc) > 100, 'Expected the complete course, not a short preview'
    text = '\n'.join(page.get_text() for page in doc)
    assert len(text) > 100_000, 'Searchable book text is missing'
    assert len(re.findall(r'[\u0d00-\u0d7f]', text)) > 10_000, 'Malayalam text is missing'
    assert '\ufffd' not in text, 'Unmapped replacement characters in PDF text'
    headings = [title for _, title, *_ in doc.get_toc()]
    assert headings.count('Contents') == 1, 'Expected a single generated contents section'
    assert 'Table of Contents' not in headings, 'Original printed contents leaked into export'
    normalize = lambda s: re.sub(r'\s+', ' ', s).strip()
    for path in book_paths():
        title = re.search(r'^# (.+)$', path.read_text(), re.M)[1]
        assert normalize(title) in [normalize(h) for h in headings], f'Missing chapter bookmark: {title}'
    # WeasyPrint shares resources across pages; page.get_fonts() recursively
    # rescans all SVG resources on every page. Inspect each font object once.
    font_refs = {}
    for ref in range(1, doc.xref_length()):
        if (doc.xref_get_key(ref, 'Type') == ('name', '/Font')
                and doc.xref_get_key(ref, 'Subtype')[1] not in {'/CIDFontType0', '/CIDFontType2'}):
            font_refs[ref] = doc.xref_get_key(ref, 'BaseFont')[1]
    internal_links = external_links = 0
    overflow = []
    for page in doc:
        assert abs(page.rect.width - 595.28) < 1 and abs(page.rect.height - 841.89) < 1, 'Expected A4 pages'
        for link in page.get_links():
            if link['kind'] in {pymupdf.LINK_GOTO, pymupdf.LINK_NAMED}:
                internal_links += 1
                assert 0 <= link['page'] < len(doc), f'Broken internal link: {link}'
            elif link['kind'] == pymupdf.LINK_URI:
                external_links += 1
                assert not link['uri'].startswith('file:'), 'Local filesystem link leaked into PDF'
                assert not re.search(r'\.(mp3|wav|ogg|m4a)(?:[?#]|$)', link['uri'], re.I), 'Audio link leaked into PDF'
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    x0,y0,x1,y1 = span['bbox']
                    if x0 < -1 or y0 < -1 or x1 > page.rect.width+1 or y1 > page.rect.height+1:
                        overflow.append((page.number+1, span['text'][:60]))
    assert not overflow, f'Text outside PDF page bounds: {overflow[:12]}'
    malayalam_fonts = [ref for ref,name in font_refs.items() if 'Malayalam' in name]
    assert malayalam_fonts and all('Serif' in font_refs[ref] for ref in malayalam_fonts), 'Malayalam serif font not present'
    latin_fonts = [ref for ref,name in font_refs.items() if 'Source-Serif-4' in name]
    assert latin_fonts and all(doc.extract_font(ref)[3] for ref in latin_fonts), 'English serif font is not embedded'
    assert all(doc.extract_font(ref)[3] for ref in malayalam_fonts), 'Malayalam font is not embedded'
    assert internal_links > 100 and external_links > 10, 'Expected navigation and source links'
    print(f'Validated {len(doc)} searchable A4 pages; {len(headings)} bookmarks; embedded Malayalam fonts; {internal_links} internal and {external_links} external links.')


if __name__ == '__main__':
    main()
