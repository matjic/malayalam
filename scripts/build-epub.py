"""Package docs as a portable EPUB 3; requires Pandoc on PATH."""

import argparse
import subprocess
import tempfile
from pathlib import Path

from book_export import ROOT, DOCS, BOOK_FONTS, AUDIO_BASE, prepare, book_paths, book_markdown

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/malayalam.epub')
    args = parser.parse_args()
    paths = book_paths()
    content = book_markdown()
    content = '# About this EPUB {#epub-notes}\n\n' + (
        'This edition includes the textbook and added practice lessons. '
        'Audio playback is available separately on the website and in the Anki decks. '
        'Reading answers are always visible. Use the reader’s contents and search controls. '
        'Wide tables may need a smaller font or landscape orientation.\n\n') + content
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='malayalam-epub-') as directory:
        source = Path(directory) / 'book.md'
        source.write_text(content, encoding='utf-8')
        subprocess.run([
            'pandoc', str(source), '--from=markdown-auto_identifiers', '--to=epub3',
            '--output=' + str(output), '--resource-path=' + str(DOCS),
            '--toc', '--toc-depth=1', '--epub-chapter-level=1',
            '--metadata=title:Malayalam: A University Course and Reference Grammar',
            '--metadata=author:Rodney F. Moag', '--metadata=lang:en',
            '--metadata=rights:Creative Commons Attribution-NonCommercial-ShareAlike 4.0; added practice material retains its credited reuse terms.',
            '--epub-cover-image=' + str(DOCS / 'assets/images/front-cover-002.jpg'),
            *['--epub-embed-font=' + str(font) for font in BOOK_FONTS],
            '--css=' + str(ROOT / 'scripts/epub.css'),
        ], check=True, cwd=DOCS)
    print(f'Built {output} ({output.stat().st_size:,} bytes; {len(paths)} documents)')


if __name__ == '__main__':
    main()
