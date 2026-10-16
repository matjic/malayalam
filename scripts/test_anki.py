"""Verify package media, official Anki import, card rendering and repeat import."""
import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile
from anki.collection import Collection
from anki.import_export_pb2 import ImportAnkiPackageRequest

ROOT = Path(__file__).resolve().parents[1]
package = ROOT / 'dist/anki/malayalam-moag.apkg'
data = json.loads((ROOT / 'data/vocabulary/moag.json').read_text())
with zipfile.ZipFile(package) as archive:
    media = json.loads(archive.read('media'))
    by_name = {name: archive.read(index) for index, name in media.items()}
    for e in data['entries']:
        for a in e['audio']:
            name = 'moag_'+Path(a['path']).name
            assert hashlib.sha256(by_name[name]).hexdigest() == a['sha256']
    assert len(media) == 998
with tempfile.TemporaryDirectory() as tmp:
    col = Collection(str(Path(tmp)/'collection.anki2'))
    request = ImportAnkiPackageRequest(package_path=str(package))
    col.import_anki_package(request)
    assert col.note_count() == 990
    assert col.card_count() == 1980
    names = [d.name for d in col.decks.all_names_and_ids()]
    assert 'Malayalam' in names
    assert len([n for n in names if n.startswith('Malayalam::')]) == 25
    seen = set()
    no_audio = 0
    for nid in col.find_notes(''):
        note = col.get_note(nid)
        assert note['Malayalam'] and note['English']
        sounds = re.findall(r'\[sound:([^]]+)\]', note['Audio'])
        seen.update(sounds)
        no_audio += not sounds
        for card in note.cards():
            assert '[sound:' not in card.question()  # Answer only, no giveaway.
            assert note['Malayalam'] in card.answer()
            assert note['English'] in card.answer()
    assert len(seen) == 997
    assert no_audio == 65
    # Reimport must not create duplicate notes/cards or reset a reviewed card.
    cid = col.find_cards('')[0]
    card = col.get_card(cid)
    card.type = 2
    card.queue = 2
    card.ivl = 12
    card.reps = 4
    col.update_card(card)
    col.import_anki_package(request)
    assert col.note_count() == 990 and col.card_count() == 1980
    card = col.get_card(cid)
    assert card.ivl == 12 and card.reps == 4 and card.queue == 2
    col.close()
print('Official Anki import/reimport passed: 990 notes, 1,980 cards, 25 chapter subdecks; all media intact.')
