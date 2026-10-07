"""Package docs as a portable EPUB 3; requires Pandoc on PATH."""

import argparse
import html
import re
import subprocess
import tempfile
from pathlib import Path

from reading_order import DOCS, reading_documents

ROOT = DOCS.parent
AUDIO_BASE = 'https://raw.githubusercontent.com/matjic/malayalam/main/docs/'
FONT = next((DOCS / 'assets/fonts').glob('*RuDNG1bFn6E.woff2'))


def heading_slug(title):
    return re.sub(r'\s+', '-', re.sub(r'[^\w\s-]', '', title.lower())).strip('-')


def prepare(path, chapters):
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'<!-- epub-download -->.*?<!-- /epub-download -->', '', text, flags=re.S)
    # Give Pandoc the existing section IDs so it can rewrite cross-chapter links.
    text = re.sub(
        r'<a id="([^"]+)"></a><!-- reading-anchor -->\n(#{1,6} [^\n]+)',
        lambda m: f'{m[2]} {{#{m[1]}}}', text)
    text = re.sub(r'<a id="([^"]+)"></a>', r'\n\n[]{#\1}\n\n', text)
    if not re.search(r'^# .*\{#', text, re.M):
        text = re.sub(r'^(# [^\n]+)', rf'\1 {{#{path.stem}}}', text, count=1, flags=re.M)

    # Pandoc's EPUB writer also assigns IDs to headings without explicit IDs.
    text = re.sub(r'^(#{1,6} [^\n]+)$',
                  lambda m: m[0] if re.search(r'\{#[^}]+\}$', m[0]) else
                  f'{m[0]} {{#{path.stem}-{heading_slug(m[0].split(' ', 1)[1])}}}', text, flags=re.M)
    # Raw HTML void tags must be well-formed XHTML in EPUB.
    text = re.sub(r'<br\s*/?>', '<br />', text)

    def link(match):
        name, fragment = match[1], match[2]
        if name not in chapters:
            return f'(https://github.com/matjic/malayalam/blob/main/docs/{name}' + (f'#{fragment}' if fragment else '') + ')'
        if fragment:
            target = (DOCS / name).read_text(encoding='utf-8')
            for heading in re.finditer(r'^(#{1,6}) (.+)$', target, re.M):
                if heading_slug(heading[2]) == fragment:
                    before = target[:heading.start()]
                    anchor = re.search(r'<a id="([^"]+)"></a><!-- reading-anchor -->\n$', before)
                    fragment = anchor[1] if anchor else f'{Path(name).stem}-{fragment}'
                    break
        return '(#' + (fragment or Path(name).stem) + ')'

    text = re.sub(r'\(([\w-]+\.md)(?:#([^\s)]+))?\)', link, text)

    def audio_links(match):
        block = match[0]
        clips = re.findall(r'<button\b[^>]*data-audio-src="([^"]+)"[^>]*>(.*?)</button>', block)
        if not clips:
            clips = [(src, label) for label, src in re.findall(
                r'<audio\b[^>]*aria-label="([^"]+)"[^>]*src="([^"]+)"', block)]
        return '\n\n' + ' · '.join(
            f'[{html.unescape(label)}]({AUDIO_BASE}{src})' for src, label in clips) + '\n\n'

    text = re.sub(r'<div class="lesson-audio">.*?</div>\s*</div>', audio_links, text, flags=re.S)
    text = re.sub(r'<audio\b.*?</audio>', audio_links, text, flags=re.S)
    text = re.sub(r'</?details[^>]*>', '', text)
    text = re.sub(r'<summary>(.*?)</summary>', r'\n\n**\1**\n\n', text)
    # Use ordinary images: ebook readers do not run the SVG-inlining plugin.
    text = re.sub(
        r'<figure\b[^>]*>\s*<img src="([^"]+)" alt="([^"]+)"[^>]*>\s*<figcaption[^>]*>(.*?)</figcaption>\s*</figure>',
        lambda m: f'\n\n![{html.unescape(m[2])}]({m[1]})\n\n{m[3]}\n\n', text, flags=re.S)
    text = re.sub(r'</?div[^>]*>', '', text)
    text = re.sub(r'\((assets/[^)]+\.json)\)', lambda m: f'({AUDIO_BASE}{m[1]})', text)
    if path.name == 'digital-edition.md':
        text = text.replace('an ebook has not been published by this change.',
                            'this EPUB retains chapter and section navigation.')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/malayalam.epub')
    args = parser.parse_args()
    paths = [DOCS / name for name in ('README.md', 'contents.md', 'digital-edition.md', 'practice.md')]
    paths += reading_documents() + [DOCS / 'proofreading-review.md']
    chapters = {path.name for path in paths}
    content = '\n\n'.join(prepare(path, chapters) for path in paths)
    content = '# About this EPUB {#epub-notes}\n\n' + (
        'This edition includes the textbook and added practice lessons. '
        'Recordings are online links and require an internet connection. '
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
            '--toc', '--toc-depth=2', '--epub-chapter-level=1',
            '--metadata=title:Malayalam: A University Course and Reference Grammar',
            '--metadata=author:Rodney F. Moag', '--metadata=lang:en',
            '--metadata=rights:Creative Commons Attribution-NonCommercial-ShareAlike 4.0; added practice material retains its credited reuse terms.',
            '--epub-cover-image=' + str(DOCS / 'assets/images/front-cover-002.jpg'),
            '--epub-embed-font=' + str(FONT),
            '--css=' + str(ROOT / 'scripts/epub.css'),
        ], check=True, cwd=DOCS)
    print(f'Built {output} ({output.stat().st_size:,} bytes; {len(paths)} documents)')


if __name__ == '__main__':
    main()
