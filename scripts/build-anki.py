#!/usr/bin/env python3
"""Build a chapter-organized Anki package from the shared vocabulary catalog."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import genanki

ROOT = Path(__file__).resolve().parents[1]
FONT = next((ROOT / 'docs/assets/fonts').glob('*RuDNG1bFn6E.woff2'))
FONT_NAME = '_malayalam_noto.woff2'


def stable_id(text):
    return 1_000_000_000 + int(hashlib.sha256(text.encode()).hexdigest()[:8], 16) % 1_000_000_000


def build(output):
    data = json.loads((ROOT / 'data/vocabulary/moag.json').read_text())
    model = genanki.Model(stable_id('moag-vocab-model-v1'), 'Malayalam Moag Vocabulary v1',
        fields=[{'name': x} for x in ['EntryID', 'Malayalam', 'English', 'Audio', 'Chapter', 'Source']],
        templates=[
            dict(name='Malayalam → English', qfmt='<div class="chapter">{{Chapter}}</div><div class="ml" lang="ml">{{Malayalam}}</div>',
                 afmt='{{FrontSide}}<hr id="answer"><div>{{English}}</div>{{Audio}}<div class="source">{{Source}}</div>'),
            dict(name='English → Malayalam', qfmt='<div class="chapter">{{Chapter}}</div><div>{{English}}</div>',
                 afmt='{{FrontSide}}<hr id="answer"><div class="ml" lang="ml">{{Malayalam}}</div>{{Audio}}<div class="source">{{Source}}</div>')],
        css='''@font-face{font-family:MalayalamDeck;src:url("_malayalam_noto.woff2")}.card{font-family:Arial,sans-serif;font-size:23px;text-align:center;line-height:1.6;padding:20px}.ml{font-family:MalayalamDeck,"Noto Sans Malayalam",sans-serif;font-size:34px;line-height:1.8}.chapter,.source,.variant{font-size:14px;opacity:.75;margin:16px 0}.recording{margin:16px 0}''', sort_field_index=1)
    parent = genanki.Deck(stable_id('moag-parent'), 'Malayalam', description='Moag chapter vocabulary with embedded recordings. See the accompanying README for gradual lesson study.')
    decks = {}
    for chapter in data['chapters']:
        n = chapter['number']
        # Fixed names keep subdeck identity stable when a chapter title is edited.
        decks[n] = genanki.Deck(stable_id(f'moag-chapter-{n}'), f'Malayalam::Lesson {n:02}', description=html.escape(chapter['title']))
    media = {}
    for position, entry in enumerate(data['entries'], 1):
        sounds = []
        for clip in entry['audio']:
            path = ROOT / clip['path']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == clip['sha256'], path
            name = 'moag_' + path.name
            media[name] = path
            variant = '' if clip['transcript'] == entry['malayalam'] else '<div class="variant" lang="ml">Recorded: '+html.escape(clip['transcript'])+'</div>'
            sounds.append('<div class="recording">'+variant+'[sound:'+name+']</div>')
        chapter = data['chapters'][entry['chapter']-1]
        source_url = 'https://matjic.github.io/malayalam/#/lesson'+str(entry['chapter'])
        note = genanki.Note(model=model, guid=genanki.guid_for(entry['id']),
            due=position, fields=[entry['id'], html.escape(entry['malayalam']), html.escape(entry['english']), ''.join(sounds),
                    html.escape(chapter['title']), f'<a href="{source_url}">Open lesson</a>'],
            tags=[f'moag::lesson_{entry["chapter"]:02}', 'moag::'+entry['origin'], 'audio::available' if sounds else 'audio::unavailable'])
        decks[entry['chapter']].add_note(note)
    output.mkdir(parents=True, exist_ok=True)
    # genanki uses basenames for media; stage the names referenced by sound fields.
    import tempfile
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for name, source in media.items():
            target = Path(tmp) / name
            shutil.copyfile(source, target)
            files.append(str(target))
        font = Path(tmp) / FONT_NAME
        shutil.copyfile(FONT, font)
        files.append(str(font))
        package = genanki.Package([parent, *decks.values()])
        package.media_files = files
        package.write_to_file(str(output / 'malayalam-moag.apkg'))
    summary = dict(notes=len(data['entries']), cards=2*len(data['entries']), chapters=25,
                   notes_with_audio=sum(bool(e['audio']) for e in data['entries']), audio_files=len(media),
                   notes_without_audio=sum(not e['audio'] for e in data['entries']))
    shutil.copyfile(ROOT / 'data/vocabulary/README.md', output / 'README.md')
    (output / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/anki')
    build(parser.parse_args().output)
