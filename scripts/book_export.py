"""Shared content preparation for the EPUB and PDF editions."""

import html
import re
from pathlib import Path
from audio_tables import TABLE, cells
from reading_order import DOCS, reading_documents

ROOT = DOCS.parent
EDITION_CREDIT = (
    'Original textbook by Rodney F. Moag. Digital adaptation and modifications by Mathew Jacob. '
    'This independently prepared digital edition includes corrections, redrawn writing models, '
    'audio integration, and added practice material; it was not published by Rodney F. Moag.'
)
AUDIO_BASE = 'https://raw.githubusercontent.com/matjic/malayalam/main/docs/'
BOOK_FONTS = sorted((DOCS / 'assets/fonts/book').glob('*.ttf'))
assert len(BOOK_FONTS) == 8, 'Expected four Latin, two Malayalam and two Tamil book font faces'


def heading_slug(title):
    return re.sub(r'\s+', '-', re.sub(r'[^\w\s-]', '', title.lower())).strip('-')


def inline_writing_diagrams(text, chapter):
    """Inline SVGs so currentColor follows the reader's text theme."""
    counter = 0

    def diagram(match):
        nonlocal counter
        counter += 1
        source = DOCS / match[2]
        svg = source.read_text(encoding='utf-8')
        # A symbol can appear more than once; SVG IDs must be document-unique.
        prefix = f'epub-{chapter}-{counter}-'
        ids = re.findall(r'\bid="([^"]+)"', svg)
        for identifier in ids:
            svg = svg.replace(f'id="{identifier}"', f'id="{prefix}{identifier}"')
            svg = svg.replace(f'url(#{identifier})', f'url(#{prefix}{identifier})')
        svg = re.sub(r'aria-labelledby="([^"]+)"',
                     lambda m: 'aria-labelledby="' + ' '.join(prefix + i for i in m[1].split()) + '"', svg)
        # Keep geometry and widths, but inherit ink for all guides and labels.
        svg = re.sub(r' style="[^"]*"', '', svg)
        svg = svg.replace('"#557467"', '"currentColor"')
        # A white label halo stays white on dark pages; remove it in the EPUB.
        svg = re.sub(r'(<text\b[^>]*?) stroke="[^"]*"', r'\1', svg)
        svg = re.sub(r'(<text\b[^>]*?) stroke-width="[^"]*"', r'\1', svg)
        css_class = 'writing-symbol' if '/symbols/' in match[2] else 'writing-table'
        svg = svg.replace('<svg ', f'<svg class="{css_class}" ', 1)
        return '\n\n' + svg.strip() + '\n\n'

    return re.sub(r'!\[([^\]]*)\]\((assets/writing/[^)]+\.svg)\)', diagram, text)


def strip_book_audio(text):
    """Remove playback UI while preserving every written vocabulary row."""
    text = re.sub(r'<!-- letter-audio -->.*?<!-- /letter-audio -->', '', text, flags=re.S)

    def without_audio_column(match):
        lines = match[0].splitlines()
        if cells(lines[0])[-1].strip() != 'Audio':
            return match[0]
        return ''.join('|' + '|'.join(cells(line)[:-1]) + '|\n' for line in lines)

    text = TABLE.sub(without_audio_column, text)
    # Audio panels contain nested cue divs. Track nesting instead of stopping
    # at the first closing div, which leaves browser buttons in book exports.
    panels = []
    depth = 0
    start = None
    for tag in re.finditer(r'</?div\b[^>]*>', text):
        if tag[0].startswith('</'):
            if start is not None:
                depth -= 1
                if depth == 0:
                    panels.append((start, tag.end()))
                    start = None
        else:
            if start is not None:
                depth += 1
            elif re.search(r'class="lesson-audio"', tag[0]):
                start, depth = tag.start(), 1
    for start, end in reversed(panels):
        text = text[:start] + '\n\n' + text[end:]
    text = re.sub(r'<audio\b.*?</audio>', '', text, flags=re.S)
    text = re.sub(r'<button\b[^>]*data-(?:row-)?audio-src=[^>]*>.*?</button>', '', text, flags=re.S)
    # Any explicit recording links become ordinary labels, not MP3 downloads.
    text = re.sub(r'\[([^\]]+)\]\([^)]*\.(?:mp3|wav|ogg|m4a)(?:[?#][^)]*)?\)', r'\1', text, flags=re.I)
    text = re.sub(r'<a\b[^>]*href=["\'][^"\']*\.(?:mp3|wav|ogg|m4a)[^"\']*["\'][^>]*>(.*?)</a>', r'\1', text, flags=re.S | re.I)
    text = re.sub(r'^.*\[Listen to the Alphabet and Individual Letters\].*\n', '', text, flags=re.M)
    text = re.sub(r'^Use the \[individual letter players\].*\n', '', text, flags=re.M)
    return text


def compact_vocabulary(text, filename):
    """Use compact, column-friendly entries only in lesson vocabulary sections."""
    if not re.fullmatch(r'lesson\d+\.md', filename):
        return text
    heading = re.search(r'^(#{2,3}) Vocabulary\n', text, re.M)
    if not heading:
        return text
    start = heading.end()
    following = re.search(r'^#{1,' + str(len(heading[1])) + r'} ', text[start:], re.M)
    end = start + following.start() if following else len(text)

    def entries(match):
        lines = match[0].splitlines()
        header = [re.sub(r'<[^>]*>', '', c).strip() for c in cells(lines[0])]
        if len(header) != 2 or header[0] != 'Malayalam' or header[1] not in {'English', 'Meaning'}:
            return match[0]
        result = ['::: {.vocabulary-list}', '']
        for line in lines[2:]:
            word, meaning = [c.strip() for c in cells(line)]
            plain = html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<!--.*?-->', '', word)))
            row_class = 'vocabulary-entry vocabulary-entry-long' if len(plain) > 20 else 'vocabulary-entry'
            result += ['::: {.' + row_class.replace(' ', ' .') + '}', '',
                       '<span class="vocabulary-term" lang="ml">' + word + '</span> <span class="vocabulary-definition">' + meaning + '</span>',
                       '', ':::', '']
        result += [':::', '']
        return '\n'.join(result)

    return text[:start] + TABLE.sub(entries, text[start:end]) + text[end:]


def prepare(path, chapters):
    text = compact_vocabulary(strip_book_audio(path.read_text(encoding='utf-8')), path.name)
    # Website navigation and original printed pagination do not belong in the
    # exported reading sequence. Each format generates its own linked contents.
    text = re.sub(r'<!-- reading-navigation -->.*?<!-- /reading-navigation -->', '', text, flags=re.S)
    if path.name == 'front-matter.md':
        text = re.sub(r'<a id="front-matter-table-of-contents"></a>.*', '', text, flags=re.S)
    # References to the site's contents remain ordinary prose in the book;
    # navigation is provided by the generated contents and reader bookmarks.
    text = re.sub(r'\[([^\]]+)\]\(contents\.md(?:#[^)]*)?\)', r'\1', text)

    if path.name == 'contents.md':
        # Keep the chapter list; section anchors remain in the chapters themselves.
        text = re.sub(r'^## Sections\n.*', '', text, flags=re.M | re.S)
    text = re.sub(r'<!-- epub-download -->.*?<!-- /epub-download -->', '', text, flags=re.S)
    # Raw browser links can contain boolean attributes invalid in EPUB XHTML.
    # Let Pandoc serialize anchors, and keep non-book resources as online links.
    def web_link(match):
        attributes, label = match[1], match[2]
        target = re.search(r'href=["\']([^"\']+)["\']', attributes)
        if not target:
            return match[0]
        href = html.unescape(target[1])
        if not re.match(r'(?:[a-zA-Z][\w+.-]*:|#|/)', href):
            if not re.match(r'[\w-]+\.md(?:#|$)', href):
                href = 'https://ml.matj.io/' + href
        return '[' + html.unescape(re.sub(r'<[^>]+>', '', label)) + '](' + href + ')'

    text = re.sub(r'<a\b([^>]*)>(.*?)</a>', web_link, text, flags=re.S)
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
                  f'{m[0]} {{#{path.stem}-{heading_slug(m[0].split(" ", 1)[1])}}}', text, flags=re.M)
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

    text = re.sub(r'</?details[^>]*>', '', text)
    text = re.sub(r'<summary>(.*?)</summary>', r'\n\n**\1**\n\n', text)
    # Convert web cards to portable image/caption content before inlining SVGs.
    text = re.sub(
        r'<figure\b[^>]*>\s*<img src="([^"]+)" alt="([^"]+)"[^>]*>\s*<figcaption[^>]*>(.*?)</figcaption>\s*</figure>',
        lambda m: f'\n\n![{html.unescape(m[2])}]({m[1]})\n\n{m[3]}\n\n', text, flags=re.S)
    text = inline_writing_diagrams(text, path.stem)
    text = re.sub(r'</?div[^>]*>', '', text)
    text = re.sub(r'\((assets/[^)]+\.json)\)', lambda m: f'({AUDIO_BASE}{m[1]})', text)
    if path.name == 'practice-pronunciation.md':
        text = text.replace('The players below use UT Austin recordings. The complete recordings contain more examples than the selected words listed here.', 'Recordings for this listening practice are available on the website. The written examples and exercises are retained here.')
    if path.name == 'digital-edition.md':
        text = re.sub(r'Lessons 1–25 include section clips.*?complete answer key\.', 'Audio playback is available in the website edition; audio players and recording links are omitted from this book.', text)
        text = text.replace('an ebook has not been published by this change.',
                            'this EPUB retains chapter and section navigation.')
    # Provenance remains in the Markdown source; HTML comment blocks must not
    # split ordered lists or become part of exported vocabulary formatting.
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    return text


def book_paths():
    paths = [DOCS / name for name in ('README.md', 'digital-edition.md', 'practice.md')]
    paths += reading_documents() + [DOCS / 'proofreading-review.md', DOCS / 'technical-notes.md']
    return paths


def book_markdown():
    paths = book_paths()
    chapters = {path.name for path in paths}
    return '\n\n'.join(prepare(path, chapters) for path in paths)
