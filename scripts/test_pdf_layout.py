"""Guard against Pandoc browser padding and shrink-wrapped print tables."""
from pathlib import Path
import subprocess
import pymupdf
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from book_export import ROOT, DOCS, compact_vocabulary

source = '''# Layout sample

LAYOUT ORIGIN

| Malayalam | English |
|---|---|
| നമസ്കാരം | Hello |
| പഠിക്കുന്നു | Is studying |
'''
source += '\n## Vocabulary\n\n| Malayalam | English |\n|---|---|\n| അവൻ | Normal meaning |\n| ആഘോഷിക്കപ്പെടുക (past: ആഘോഷിക്കപ്പെട്ടു) | Long meaning |\n'
source = compact_vocabulary(source, 'lesson20.md')
page_html = subprocess.check_output([
    'pandoc', '--from=markdown-auto_identifiers', '--to=html5', '--standalone',
    '--metadata=title:Layout sample', '--template=' + str(ROOT / 'scripts/pdf.html'),
], input=source.encode()).decode()
assert '<style>' not in page_html, 'Pandoc browser styles leaked into print output'
fonts = FontConfiguration()
pdf = HTML(string=page_html, base_url=str(DOCS)).write_pdf(
    stylesheets=[CSS(filename=str(ROOT / 'scripts/pdf.css'), font_config=fonts),
                 CSS(string='.vocabulary-list { column-count: 1; width: 81.5mm; } table tbody td:last-child { text-align: right; }')], font_config=fonts)
doc = pymupdf.open(stream=pdf, filetype='pdf')
page = doc[0]
left, right = 20 * 72 / 25.4, page.rect.width - 20 * 72 / 25.4
origin = next(span for block in page.get_text('dict')['blocks']
              for line in block.get('lines', []) for span in line['spans']
              if 'LAYOUT ORIGIN' in span['text'])
assert abs(origin['bbox'][0] - left) < 1, 'Unexpected body padding or centering'
assert not page.get_drawings(), 'Table or vocabulary rules leaked into the PDF'
hello = next(span for block in page.get_text('dict')['blocks']
             for line in block.get('lines', []) for span in line['spans'] if span['text']=='Hello')
assert abs(hello['bbox'][2] - (right - 1.5 * 72 / 25.4)) < 1, 'Table does not fill the text area'
print('PDF layout passed: body starts at 20 mm, tables fill the 170 mm text area.')

spans = [span for block in page.get_text('dict')['blocks']
         for line in block.get('lines', []) for span in line['spans']]
normal = next(s for s in spans if s['text'] == 'Normal meaning')
long = next(s for s in spans if s['text'] == 'Long meaning')
assert abs(normal['bbox'][0]-long['bbox'][0]) < 1, 'Vocabulary meanings are not aligned'
print('Compact vocabulary passed: short and long forms share the same meaning column.')
