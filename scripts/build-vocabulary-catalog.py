#!/usr/bin/env python3
"""Export chapter vocabulary from the Markdown tables and verified audio manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from audio_tables import EXTRA
from vocabulary_tables import clean, read_tables, word_rows

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
    for fields in [('malayalam', 'english'), ('malayalam', 'source_anchor'), ('malayalam',), ('english',)]:
        for entry in pending[:]:
            if not all(field in entry for field in fields):
                continue
            candidates = [old for old in identities
                          if old['id'] not in used and old['chapter'] == entry['chapter']
                          and all(old.get(f) == entry[f] for f in fields)]
            competing = [other for other in pending
                         if other['chapter'] == entry['chapter']
                         and all(other.get(f) == entry[f] for f in fields)]
            if len(candidates) == len(competing) == 1:
                entry['id'] = candidates[0]['id']
                used.add(entry['id'])
                pending.remove(entry)
    known = {old['id'] for old in identities}
    for entry in pending:
        if entry['id'] in known:
            raise ValueError(f"Ambiguous vocabulary identity: {entry['id']}")
    assert len({e['id'] for e in entries}) == len(entries)


def catalog(root=ROOT):
    manifest = json.loads((root / 'docs/assets/audio/moag/words/manifest.json').read_text())
    audio = {c['path'][5:]: c for c in manifest['clips']}
    chapters, entries, seen_audio, references = [], [], set(), []
    for n in range(1, 26):
        source = f'docs/lesson{n}.md'
        text = (root / source).read_text()
        title = re.search(r'^# (.+)$', text, re.M)[1]
        chapters.append(dict(number=n, title=title, source=source))
        chapter_entries = {}
        for table in read_tables(text, source):
            if table.options['kind'] != 'vocabulary':
                continue
            if table.options.get('origin', 'textbook') == 'reference_table':
                references.append((n, source, table))
                continue
            for row in word_rows(table, source):
                word, meaning = row['malayalam'], row['english']
                identity = (word, meaning)
                if identity not in chapter_entries:
                    stable = hashlib.sha256(f'{n}\0{word}\0{meaning}'.encode()).hexdigest()[:16]
                    entry = dict(id=f'moag-{n:02}-{stable}', chapter=n, malayalam=word,
                                 english=meaning, origin='recorded_addition' if EXTRA in row['row'] else 'textbook',
                                 source=source, audio=[])
                    if not row['study']:
                        entry['study'] = False
                    if table.options['category'] != 'vocabulary':
                        entry['category'] = table.options['category']
                    if row['variants']:
                        entry['variants'] = row['variants']
                    if row['notes']:
                        entry['notes'] = row['notes']
                    chapter_entries[identity] = entry
                    entries.append(entry)
                entry = chapter_entries[identity]
                for path in re.findall(r'data-row-audio-src="([^"]+)"', row['row']):
                    clip = audio[path]
                    if clip['status'] != 'matched':
                        raise ValueError(f'Unverified recording: {path}')
                    if path not in seen_audio:
                        entry['audio'].append(dict(path='docs/'+path, transcript=clip['transcript'], sha256=clip['sha256']))
                        seen_audio.add(path)
        # Keep the one published derived noun recording outside the vocabulary table.
        for path, clip in audio.items():
            if clip['lesson'] != n or path in seen_audio:
                continue
            if n != 24 or clip['transcript'] != 'സ്നേഹം':
                raise ValueError(f'Vocabulary recording lost its tagged table: {path}')
            if f'data-row-audio-src="{path}"' not in text:
                raise ValueError(f'Missing audio source placement: {path}')
            word, meaning = clip['transcript'], clip['meaning']
            stable = hashlib.sha256(f'{n}\0reference\0{word}\0{meaning}'.encode()).hexdigest()[:16]
            entries.append(dict(id=f'moag-{n:02}-{stable}', chapter=n, malayalam=word, english=meaning,
                                origin='reference_list', source=source,
                                audio=[dict(path='docs/'+path, transcript=word, sha256=clip['sha256'])]))
            seen_audio.add(path)
    for path in sorted((root / 'docs').glob('appendix-*.md')):
        source = str(path.relative_to(root))
        for table in read_tables(path.read_text(), source):
            if table.options['kind'] == 'vocabulary':
                n = table.options.get('chapter')
                if not isinstance(n, int) or not 1 <= n <= 25:
                    raise ValueError(f'{source}: exported appendix table needs a lesson chapter')
                references.append((n, source, table))
    # Preserve existing textbook notes; attach references rather than duplicate a
    # same-lesson word whose meaning was already supplied in its vocabulary table.
    published = list(entries)
    for n, source, table in references:
        options = table.options
        for row in word_rows(table, source):
            word, meaning = row['malayalam'], row['english']
            if 'Type' in table.headers:
                raw = row['row'].split('|')
                kind = clean(raw[table.headers.index('Type')])
                meaning += ' (' + ('adjective' if kind == 'Adjectives' else 'pronoun') + ')'
            if 'case' in options:
                case = options['case']
                usage = 'after a ' + case + ' noun'
                if case == 'possessive' and '\\*' not in row['row']:
                    usage += '; also dative in colloquial speech'
                meaning += ' (postposition; ' + usage + ')'
            matches = [e for e in entries if e['chapter'] == n
                       and e['malayalam'] == word and e['english'] == meaning]
            if not matches and options['category'] not in {'postposition', 'demonstrative'}:
                matches = [e for e in published if e['chapter'] == n and e['malayalam'] == word]
            if len(matches) == 1:
                entry = matches[0]
                if entry.get('study') is False and row['study']:
                    entry['study'] = True
                for field in ('variants', 'notes'):
                    if row[field]:
                        entry[field] = list(dict.fromkeys(entry.get(field, []) + row[field]))
            else:
                stable = hashlib.sha256(f'{n}\0reference-table\0{word}\0{meaning}'.encode()).hexdigest()[:16]
                entry = dict(id=f'moag-{n:02}-{stable}', chapter=n, malayalam=word,
                             english=meaning, origin='reference_table', source=source,
                             source_anchor=table.anchor, category=options['category'],
                             study=row['study'], audio=[])
                if row['variants']:
                    entry['variants'] = row['variants']
                if row['notes']:
                    entry['notes'] = row['notes']
                entries.append(entry)
            reference = dict(source=source, anchor=table.anchor, category=options['category'])
            if reference not in entry.setdefault('references', []):
                entry['references'].append(reference)
    if len(seen_audio) != len(audio) or len({e['id'] for e in entries}) != len(entries):
        raise ValueError('Duplicate identities or missing audio in catalog')
    return dict(schema_version=1, title='Malayalam — Moag', license='CC-BY-NC-SA-4.0',
                source_of_truth='Explicit vocabulary-table comments in lesson and appendix Markdown; audio paths and checksums from the word manifest.',
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
