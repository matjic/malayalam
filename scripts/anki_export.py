"""Anki rendering and packaging. Published identity constants are compatibility API."""
import hashlib
import html
import json
import re
from collections import defaultdict
from pathlib import Path
import shutil
import tempfile

import genanki

ROOT = Path(__file__).resolve().parents[1]
FONT_NAME = '_malayalam_noto.woff2'
PACKAGE_NAME = 'malayalam-moag.apkg'
# Field order, template order, model/deck keys and GUID inputs must remain stable.


def english_for_card(entry, overrides):
    meaning = overrides.get(entry['id'], {}).get('meaning', entry['english'])
    if any('\u0d00' <= char <= '\u0d7f' for char in meaning):
        raise ValueError(f"English flashcard text needs review: {entry['malayalam']}: {meaning}")
    return meaning


def recall_for_card(entry, overrides):
    return overrides.get(entry['id'], {}).get('recall', english_for_card(entry, overrides))


def format_card_text(text):
    """Separate trailing usage cues without breaking parentheses inside sentences."""
    main, cues = text.strip(), []
    while main.endswith(')'):
        depth, start = 0, None
        for index in range(len(main) - 1, -1, -1):
            if main[index] == ')':
                depth += 1
            elif main[index] == '(':
                depth -= 1
                if depth == 0:
                    start = index
                    break
        if start is None or not main[:start].strip():
            break
        cues.insert(0, main[start + 1:-1])
        main = main[:start].rstrip()
    # A semicolon within nested parentheses is part of that cue, not a new line.
    lines = []
    for cue in cues:
        depth, start = 0, 0
        for index, char in enumerate(cue):
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ';' and depth == 0:
                lines.append(cue[start:index].strip())
                start = index + 1
        lines.append(cue[start:].strip())
    return ('<div class="prompt-main">' + html.escape(main) + '</div>'
            + ''.join('<div class="prompt-cue">' + html.escape(line) + '</div>'
                      for line in lines if line))


def english_field_for_card(entry, overrides):
    """Two display blocks preserve the published six-field model on reimport."""
    return ('<div class="english-meaning">' + format_card_text(english_for_card(entry, overrides))
            + '</div><div class="english-recall">' + format_card_text(recall_for_card(entry, overrides)) + '</div>')


def source_for_card(entry, source_url, overrides):
    # Keep the original lesson gloss when it explains a Malayalam form. Source
    # is already answer-only in both templates; reuse it to preserve the existing
    # Anki note schema and make upgrades safe for previously imported decks.
    detail = ''
    if any('\u0d00' <= char <= '\u0d7f' for char in entry['english']):
        detail = '<div class="lesson-note">Lesson note: ' + html.escape(entry['english']) + '</div>'
    study = overrides.get(entry['id'], {})
    if study.get('alternatives'):
        detail += ('<div class="alternatives"><div>Also accept:</div><ul>'
                   + ''.join('<li lang="ml">' + html.escape(word) + '</li>'
                             for word in study['alternatives']) + '</ul></div>')
    if study.get('explanation'):
        detail += '<div class="usage-note">' + html.escape(study['explanation']) + '</div>'
    return detail + f'<a href="{html.escape(source_url, quote=True)}">Open lesson</a>'


def stable_id(text):
    return 1_000_000_000 + int(hashlib.sha256(text.encode()).hexdigest()[:8], 16) % 1_000_000_000


def load_inputs(root):
    data = json.loads((root / 'data/vocabulary/moag.json').read_text(encoding='utf-8'))
    overrides = json.loads((root / 'data/vocabulary/study.json').read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported vocabulary schema_version')
    chapters = {}
    for chapter in data['chapters']:
        number = chapter['number']
        if not isinstance(number, int) or number < 1 or number in chapters:
            raise ValueError(f'Invalid or duplicate chapter number: {number}')
        chapters[number] = chapter
    unused = set(overrides) - {entry['id'] for entry in data['entries']}
    if unused:
        raise ValueError(f'Unused study entries: {sorted(unused)}')
    ids = set()
    for entry in data['entries']:
        if not entry['id'] or entry['id'] in ids:
            raise ValueError(f"Invalid or duplicate entry ID: {entry['id']}")
        ids.add(entry['id'])
        if entry['chapter'] not in chapters:
            raise ValueError(f"Unknown chapter for {entry['id']}: {entry['chapter']}")
        study = overrides.get(entry['id'], {})
        if not isinstance(study, dict) or set(study) - {'meaning', 'recall', 'explanation', 'alternatives'}:
            raise ValueError(f"Invalid study metadata: {entry['id']}")
        for field in ('meaning', 'recall', 'explanation'):
            if field in study and (not isinstance(study[field], str) or not study[field].strip()):
                raise ValueError(f"Empty or invalid {field}: {entry['id']}")
        if not entry['malayalam'].strip() or not english_for_card(entry, overrides).strip():
            raise ValueError(f"Empty flashcard text: {entry['id']}")
        prompt = recall_for_card(entry, overrides)
        if not prompt.strip() or any('\u0d00' <= c <= '\u0d7f' for c in prompt):
            raise ValueError(f"Recall prompt needs review: {entry['id']}")
        alternatives = study.get('alternatives', [])
        if not isinstance(alternatives, list) or any(not isinstance(a, str) or not a.strip() for a in alternatives):
            raise ValueError(f"Invalid alternatives: {entry['id']}")
    audit_recall(data['entries'], overrides)
    return data, overrides, chapters


def audit_recall(entries, study):
    """Reject incomplete fronts and collisions lacking reciprocal accepted answers.

    Normalization catches punctuation-only differences. Semantic overlaps still
    require editorial review; a passing check is not a linguistic certification.
    """
    groups = defaultdict(list)
    for entry in entries:
        prompt = recall_for_card(entry, study)
        normalized = re.sub(r'[^\w]+', ' ', prompt.casefold()).strip()
        if not normalized or re.fullmatch(r'(?:n|adj|adv|v|noun|verb)', normalized):
            raise ValueError(f"Incomplete recall prompt: {entry['id']}")
        if re.search(r'\b(?:inferior|superior)s?\b', english_for_card(entry, study), re.I):
            raise ValueError(f"Social ranking label needs review: {entry['id']}")
        groups[normalized].append(entry)
    collisions = []
    for prompt, group in groups.items():
        words = {entry['malayalam'] for entry in group}
        if len(words) < 2:
            continue
        for entry in group:
            accepted = set(study.get(entry['id'], {}).get('alternatives', [])) | {entry['malayalam']}
            if not words <= accepted:
                raise ValueError(f"Ambiguous recall prompt: {prompt}: {entry['id']}")
        collisions.append(dict(prompt=prompt, entries=[e['id'] for e in group]))
    return collisions


def create_model():
    return genanki.Model(
        stable_id('moag-vocab-model-v1'),
        'Malayalam Moag Vocabulary v1',
        fields=[{'name': name} for name in ['EntryID', 'Malayalam', 'English', 'Audio', 'Chapter', 'Source']],
        templates=[
            {
                'name': 'Malayalam → English',
                'qfmt': '<div class="chapter">{{Chapter}}</div><div class="ml" lang="ml">{{Malayalam}}</div>',
                'afmt': '{{FrontSide}}<hr id="answer"><div>{{English}}</div>{{Audio}}<div class="source">{{Source}}</div>',
            },
            {
                'name': 'English → Malayalam',
                'qfmt': '<div class="chapter">{{Chapter}}</div><div class="recall-question">{{English}}</div>',
                'afmt': '{{FrontSide}}<hr id="answer"><div class="ml" lang="ml">{{Malayalam}}</div><div>{{English}}</div>{{Audio}}<div class="source">{{Source}}</div>',
            },
        ],
        css=Path(__file__).with_name('anki.css').read_text(encoding='utf-8'),
        sort_field_index=1,
    )


def collect_media(entries, root):
    """Validate checksums and prevent silent basename collisions before writing."""
    media = {}
    checked = set()
    for entry in entries:
        for clip in entry['audio']:
            path = (root / clip['path']).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError(f'Audio path escapes repository: {clip["path"]}')
            name = 'moag_' + path.name
            if name in media and media[name] != path:
                raise ValueError(f'Conflicting media filename: {name}')
            identity = (path, clip['sha256'])
            if identity not in checked:
                if hashlib.sha256(path.read_bytes()).hexdigest() != clip['sha256']:
                    raise ValueError(f'Audio checksum mismatch: {clip["path"]}')
                checked.add(identity)
            media[name] = path
    return media


def audio_for_card(entry):
    sounds = []
    for clip in entry['audio']:
        name = 'moag_' + Path(clip['path']).name
        variant = ''
        if clip['transcript'] != entry['malayalam']:
            variant = '<div class="variant" lang="ml">Recorded: ' + html.escape(clip['transcript']) + '</div>'
        sounds.append('<div class="recording">' + variant + '[sound:' + name + ']</div>')
    return ''.join(sounds)


def create_decks(data, overrides, chapters):
    model = create_model()
    parent = genanki.Deck(stable_id('moag-parent'), 'Malayalam', description='Moag chapter vocabulary with embedded recordings. See the accompanying README for gradual lesson study.')
    decks = {
        number: genanki.Deck(stable_id(f'moag-chapter-{number}'), f'Malayalam::Lesson {number:02}',
                             description=html.escape(chapter['title']))
        for number, chapter in chapters.items()
    }
    for position, entry in enumerate(data['entries'], 1):
        chapter = chapters[entry['chapter']]
        sounds = audio_for_card(entry)
        source_url = 'https://matjic.github.io/malayalam/#/lesson' + str(entry['chapter'])
        note = genanki.Note(
            model=model, guid=genanki.guid_for(entry['id']), due=position,
            fields=[entry['id'], html.escape(entry['malayalam']), english_field_for_card(entry, overrides),
                    sounds, html.escape(chapter['title']), source_for_card(entry, source_url, overrides)],
            tags=[f'moag::lesson_{entry["chapter"]:02}', 'moag::' + entry['origin'],
                  'audio::available' if sounds else 'audio::unavailable'])
        decks[entry['chapter']].add_note(note)
    return [parent, *decks.values()]


def write_package(destination, decks, media, font):
    # genanki uses basenames; stage exactly the names referenced by the cards.
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for name, source in {**media, FONT_NAME: font}.items():
            target = Path(tmp) / name
            shutil.copyfile(source, target)
            files.append(str(target))
        package = genanki.Package(decks)
        package.media_files = files
        # Finish the archive before replacing a previously built package.
        staged = Path(tmp) / PACKAGE_NAME
        package.write_to_file(str(staged))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(staged, destination)


def build(output, *, root=ROOT, site_package=None):
    """Build artifacts in output; publishing the site copy is an explicit option."""
    output, root = Path(output), Path(root)
    data, overrides, chapters = load_inputs(root)
    media = collect_media(data['entries'], root)
    fonts = sorted((root / 'docs/assets/fonts').glob('*RuDNG1bFn6E.woff2'))
    if len(fonts) != 1:
        raise ValueError(f'Expected one Malayalam deck font, found {len(fonts)}')
    decks = create_decks(data, overrides, chapters)
    destination = output / PACKAGE_NAME
    write_package(destination, decks, media, fonts[0])
    with_audio = sum(bool(entry['audio']) for entry in data['entries'])
    summary = dict(notes=len(data['entries']), cards=2 * len(data['entries']), chapters=len(chapters),
                   notes_with_audio=with_audio, audio_files=len(media),
                   notes_without_audio=len(data['entries']) - with_audio)
    shutil.copyfile(root / 'data/vocabulary/README.md', output / 'README.md')
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    if site_package is not None and destination.resolve() != Path(site_package).resolve():
        site_package = Path(site_package)
        site_package.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(destination, site_package)
    return summary
