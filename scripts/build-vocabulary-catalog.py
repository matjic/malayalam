#!/usr/bin/env python3
"""Export chapter vocabulary from the Markdown tables and verified audio manifest."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
from audio_tables import TABLE, cells, EXTRA

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/vocabulary/moag.json'


def preserve_ids(entries, identities):
    """Keep published IDs when a spelling or gloss is corrected.

    Match exact rows first, then unambiguous single-field corrections. The
    checked-in catalog supplies the published identities.
    For edits to both fields, edit the catalog text while retaining its ID.
    """
    used = set()
    pending = list(entries)
    for fields in [('malayalam', 'english'), ('malayalam',), ('english',)]:
        for entry in pending[:]:
            candidates = [old for old in identities
                          if old['id'] not in used and old['chapter'] == entry['chapter']
                          and all(old[f] == entry[f] for f in fields)]
            competing = [other for other in pending
                         if other['chapter'] == entry['chapter']
                         and all(other[f] == entry[f] for f in fields)]
            if len(candidates) == len(competing) == 1:
                entry['id'] = candidates[0]['id']
                used.add(entry['id'])
                pending.remove(entry)
    known = {old['id'] for old in identities}
    for entry in pending:
        if entry['id'] in known:
            raise ValueError(f"Ambiguous vocabulary identity: {entry['id']}")
    assert len({e['id'] for e in entries}) == len(entries)


def clean(value):
    value = re.sub(r'<!--.*?-->', '', value)
    value = re.sub(r'<br\s*/?>', '; ', value)
    value = re.sub(r'<[^>]*>', '', value)
    return html.unescape(value).replace('\\*', '*').replace('\\|', '|').strip()


def catalog():
    manifest = json.loads((ROOT / 'docs/assets/audio/moag/words/manifest.json').read_text())
    audio = {c['path'][5:]: c for c in manifest['clips']}
    chapters, entries, seen_audio = [], [], set()
    for n in range(1, 26):
        source = f'docs/lesson{n}.md'
        text = (ROOT / source).read_text()
        title = re.search(r'^# (.+)$', text, re.M)[1]
        chapters.append(dict(number=n, title=title, source=source))
        heading = re.search(r'^(#{2,3}) Vocabulary\n', text, re.M)
        rest = text[heading.end():]
        end = re.search(r'^#{1,' + str(len(heading[1])) + r'} ', rest, re.M)
        body = rest[:end.start()] if end else rest
        chapter_entries = {}
        for table in TABLE.finditer(body):
            for line in table[0].splitlines()[2:]:
                row = cells(line)
                word, meaning = clean(row[0]), clean(row[1])
                assert word and meaning, (n, line)
                identity = (word, meaning)
                if identity not in chapter_entries:
                    stable = hashlib.sha256(f'{n}\0{word}\0{meaning}'.encode()).hexdigest()[:16]
                    entry = dict(id=f'moag-{n:02}-{stable}', chapter=n, malayalam=word,
                                 english=meaning, origin='recorded_addition' if EXTRA in line else 'textbook',
                                 source=source, audio=[])
                    chapter_entries[identity] = entry
                    entries.append(entry)
                entry = chapter_entries[identity]
                for path in re.findall(r'data-row-audio-src="([^"]+)"', line):
                    c = audio[path]
                    assert c['status'] == 'matched', path
                    if path not in seen_audio:
                        entry['audio'].append(dict(path='docs/'+path, transcript=c['transcript'], sha256=c['sha256']))
                        seen_audio.add(path)
        # A derived noun recording is placed in the lesson's Reference List.
        for path, c in audio.items():
            if c['lesson'] != n or path in seen_audio:
                continue
            assert f'data-row-audio-src="{path}"' in text
            word, meaning = c['transcript'], c['meaning']
            stable = hashlib.sha256(f'{n}\0reference\0{word}\0{meaning}'.encode()).hexdigest()[:16]
            entries.append(dict(id=f'moag-{n:02}-{stable}', chapter=n, malayalam=word, english=meaning,
                                origin='reference_list', source=source,
                                audio=[dict(path='docs/'+path, transcript=word, sha256=c['sha256'])]))
            seen_audio.add(path)
    assert len(seen_audio) == len(audio)
    assert len({e['id'] for e in entries}) == len(entries)
    return dict(schema_version=1, title='Malayalam — Moag', license='CC-BY-NC-SA-4.0',
                source_of_truth='Lesson Markdown tables; audio paths and checksums from the word manifest.',
                chapters=chapters, entries=entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = catalog()
    identities = json.loads(OUT.read_text())['entries'] if OUT.exists() else []
    preserve_ids(data['entries'], identities)
    rendered = json.dumps(data, ensure_ascii=False, indent=2)+'\n'
    if args.check:
        assert OUT.read_text() == rendered, 'Vocabulary catalog needs rebuilding'
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(rendered)
    print(f"{'Checked' if args.check else 'Built'} {len(data['entries'])} entries across 25 chapters; {sum(len(e['audio']) for e in data['entries'])} audio clips.")


if __name__ == '__main__':
    main()
