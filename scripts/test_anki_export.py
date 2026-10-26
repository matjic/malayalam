"""Failure cases and published Anki identity contract (no Anki backend needed)."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from anki_export import collect_media, create_decks, create_model, load_inputs, ROOT


class InputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = {
            'schema_version': 1,
            # Deliberately non-contiguous and out of order.
            'chapters': [{'number': 3, 'title': 'Third'}, {'number': 1, 'title': 'First'}],
            'entries': [{'id': 'published-id', 'chapter': 3, 'malayalam': 'വാക്ക്',
                         'english': 'word', 'origin': 'textbook', 'audio': []}],
        }

    def load(self, overrides=None):
        folder = self.root / 'data/vocabulary'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'moag.json').write_text(json.dumps(self.data))
        (folder / 'anki-english.json').write_text(json.dumps(overrides or {}))
        return load_inputs(self.root)

    def test_chapters_are_matched_by_number(self):
        data, overrides, chapters = self.load()
        decks = create_decks(data, overrides, chapters)
        self.assertEqual(decks[1].notes[0].fields[4], 'Third')
        self.assertEqual(decks[0].deck_id, 1085467152)
        self.assertEqual(decks[1].deck_id, 1501099295)

    def test_duplicate_entry(self):
        self.data['entries'].append(copy.deepcopy(self.data['entries'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate entry ID'):
            self.load()

    def test_unknown_chapter(self):
        self.data['entries'][0]['chapter'] = 2
        with self.assertRaisesRegex(ValueError, 'Unknown chapter'):
            self.load()

    def test_duplicate_chapter(self):
        self.data['chapters'].append(self.data['chapters'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate chapter'):
            self.load()

    def test_unsupported_schema(self):
        self.data['schema_version'] = 2
        with self.assertRaisesRegex(ValueError, 'schema_version'):
            self.load()

    def test_unused_override(self):
        with self.assertRaisesRegex(ValueError, 'Unused Anki English'):
            self.load({'absent': 'unused'})

    def test_malayalam_and_empty_prompts(self):
        for prompt in ('വാക്ക്', '  '):
            with self.subTest(prompt=prompt), self.assertRaises(ValueError):
                self.load({'വാക്ക്': prompt})

    def test_media_checksum_and_collision(self):
        for name in ('first/clip.mp3', 'second/clip.mp3'):
            path = self.root / name
            path.parent.mkdir()
            path.write_bytes(b'audio')
        clip = {'path': 'first/clip.mp3', 'sha256': hashlib.sha256(b'audio').hexdigest()}
        entries = [{'audio': [clip, dict(clip)]}]
        self.assertEqual(len(collect_media(entries, self.root)), 1)
        entries[0]['audio'].append({**clip, 'path': 'second/clip.mp3'})
        with self.assertRaisesRegex(ValueError, 'Conflicting media'):
            collect_media(entries, self.root)
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            collect_media([{'audio': [{**clip, 'sha256': 'invalid'}]}], self.root)

    def test_path_outside_repository(self):
        with self.assertRaisesRegex(ValueError, 'escapes repository'):
            collect_media([{'audio': [{'path': '../outside.mp3', 'sha256': ''}]}], self.root)


class CompatibilityTests(unittest.TestCase):
    def test_published_model_contract(self):
        model = create_model()
        self.assertEqual(model.model_id, 1843859663)
        self.assertEqual([field['name'] for field in model.fields],
                         ['EntryID', 'Malayalam', 'English', 'Audio', 'Chapter', 'Source'])
        self.assertEqual([template['name'] for template in model.templates],
                         ['Malayalam → English', 'English → Malayalam'])

    def test_repository_catalog(self):
        data, _, chapters = load_inputs(ROOT)
        self.assertEqual(set(chapters), {entry['chapter'] for entry in data['entries']})


if __name__ == '__main__':
    unittest.main()
