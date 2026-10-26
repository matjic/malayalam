"""Verify package media, official Anki import, card rendering and repeat import."""
import hashlib
import html
import json
from pathlib import Path
import re
import tempfile
import zipfile
from anki_export import build
from anki.collection import Collection
from anki.import_export_pb2 import ImportAnkiPackageRequest

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'data/vocabulary/moag.json').read_text())
overrides = json.loads((ROOT / 'data/vocabulary/anki-english.json').read_text())
entries = {e['id']: e for e in data['entries']}
expected_audio = {'moag_' + Path(clip['path']).name for entry in entries.values() for clip in entry['audio']}


def main():
    with tempfile.TemporaryDirectory() as output:
        build(Path(output))
        verify(Path(output) / 'malayalam-moag.apkg')


def verify(package):
    with zipfile.ZipFile(package) as archive:
        media = json.loads(archive.read('media'))
        by_name = {name: archive.read(index) for index, name in media.items()}
        for e in data['entries']:
            for a in e['audio']:
                name = 'moag_'+Path(a['path']).name
                assert hashlib.sha256(by_name[name]).hexdigest() == a['sha256']
        assert len(media) == len(expected_audio) + 1
        assert '_malayalam_noto.woff2' in by_name
    with tempfile.TemporaryDirectory() as tmp:
        col = Collection(str(Path(tmp)/'collection.anki2'))
        try:
            request = ImportAnkiPackageRequest(package_path=str(package))
            col.import_anki_package(request)
            assert col.note_count() == len(entries)
            assert col.card_count() == 2 * len(entries)
            names = [d.name for d in col.decks.all_names_and_ids()]
            assert 'Malayalam' in names
            assert len([n for n in names if n.startswith('Malayalam::')]) == len(data['chapters'])
            seen = set()
            no_audio = 0
            for nid in col.find_notes(''):
                note = col.get_note(nid)
                assert note['Malayalam'] and note['English']
                entry = entries[note['EntryID']]
                assert note['English'] == html.escape(overrides.get(entry['malayalam'], entry['english']))
                assert not re.search(r'[\u0d00-\u0d7f]', note['English']), note['English']
                assert not re.search(r'^a (?:male|female|feminine|name|Hindu female)', note['English'])
                sounds = re.findall(r'\[sound:([^]]+)\]', note['Audio'])
                seen.update(sounds)
                no_audio += not sounds
                for card in note.cards():
                    assert '[sound:' not in card.question()  # Answer only, no giveaway.
                    assert note['Malayalam'] in card.answer()
                    assert note['English'] in card.answer()
                    assert 'Lesson note:' not in card.question()
                    if re.search(r'[\u0d00-\u0d7f]', entry['english']):
                        detail = html.escape(entry['english'])
                        # Keep every original spelling/grammar explanation after the
                        # answer separator in both card directions.
                        assert detail in card.answer().split('<hr id="answer">', 1)[1]
                        assert detail not in card.question()
                    else:
                        assert 'Lesson note:' not in card.answer()
                    if card.ord == 1:
                        # Includes the full prompt, so neither the definition nor other
                        # template fields can leak Malayalam spellings before the flip.
                        assert not re.search(r'[\u0d00-\u0d7f]', card.question())
            assert seen == expected_audio
            assert no_audio == sum(not entry['audio'] for entry in entries.values())
            # Reimport must not create duplicate notes/cards or reset a reviewed card.
            changed_note = next(col.get_note(nid) for nid in col.find_notes('')
                                if col.get_note(nid)['Malayalam'] == 'രാമൻ')
            cid = changed_note.cards()[0].id
            card = col.get_card(cid)
            card.type = 2
            card.queue = 2
            card.ivl = 12
            card.reps = 4
            col.update_card(card)
            # Simulate the previous deck's field text with the same note identity.
            changed_note['English'] = 'a male (Hindu) name'
            col.update_note(changed_note)
            col.db.execute('update notes set mod = 1 where id = ?', changed_note.id)
            col.import_anki_package(request)
            assert col.note_count() == len(entries) and col.card_count() == 2 * len(entries)
            card = col.get_card(cid)
            assert card.ivl == 12 and card.reps == 4 and card.queue == 2
            assert col.get_note(changed_note.id)['English'] == 'Raman (male name)'
        finally:
            col.close()
    print(f'Official Anki import/reimport passed: {len(entries)} notes; all media intact.')


if __name__ == '__main__':
    main()
