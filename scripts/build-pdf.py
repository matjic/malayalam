#!/usr/bin/env python3
"""Build a searchable, linked PDF using the same prepared content as the EPUB."""
import argparse
import logging
from pathlib import Path
import subprocess
import tempfile
from book_export import ROOT, DOCS, book_markdown, book_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/malayalam.pdf')
    args = parser.parse_args()
    # Import only for PDF builds; EPUB/site tooling does not require WeasyPrint.
    from weasyprint import CSS, HTML
    from weasyprint.text.fonts import FontConfiguration

    print('Preparing shared book content…', flush=True)
    content = '# About this PDF {#pdf-notes}\n\n' + (
        'This digital edition includes the textbook and added practice lessons. '
        'Use the linked contents and PDF bookmarks to navigate. '
        'Audio playback is available separately on the website and in the Anki decks.\n\n') + book_markdown()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='malayalam-pdf-') as tmp:
        source = Path(tmp) / 'book.md'
        source.write_text(content)
        html_path = Path(tmp) / 'book.html'
        subprocess.run(['pandoc', str(source), '--from=markdown-auto_identifiers', '--to=html5', '--standalone',
                        '--template=' + str(ROOT / 'scripts/pdf.html'),
                        '--toc', '--toc-depth=1', '--metadata=title:Malayalam: A University Course and Reference Grammar',
                        '--metadata=author:Rodney F. Moag', '--metadata=lang:en', '-o', str(html_path)], check=True)
        document = html_path.read_text()
        document = document.replace('<body>', '<body><div class="titlepage"><p class="kicker">A UNIVERSITY COURSE</p><h1>Malayalam</h1><p class="subtitle">A University Course and Reference Grammar</p><p class="author">Rodney F. Moag</p><p class="edition">Fourth edition · Digital edition<br>Text, examples, and writing models</p></div>', 1)
        errors = []
        class RenderErrors(logging.Handler):
            def emit(self, record):
                if record.levelno >= logging.ERROR:
                    errors.append(record.getMessage())
        handler = RenderErrors()
        logger = logging.getLogger('weasyprint')
        logger.addHandler(handler)
        try:
            fonts = FontConfiguration()
            print('Laying out PDF pages…', flush=True)
            rendered = HTML(string=document, base_url=str(DOCS)).render(
                stylesheets=[CSS(filename=str(ROOT / 'scripts/pdf.css'), font_config=fonts)], font_config=fonts)
            if errors:
                raise RuntimeError('PDF rendering failed: ' + '\n'.join(errors))
            rendered.write_pdf(str(output))
        finally:
            logger.removeHandler(handler)
    print(f'Built {output} ({output.stat().st_size:,} bytes; {len(rendered.pages)} pages; {len(book_paths())} documents)')


if __name__ == '__main__':
    main()
