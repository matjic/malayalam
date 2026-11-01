"""Failure cases and published Anki identity contract (no Anki backend needed)."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from anki_export import format_card_text, audit_recall, collect_media, create_decks, create_model, load_inputs, ROOT


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
        (folder / 'study.json').write_text(json.dumps(overrides or {}))
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
        with self.assertRaisesRegex(ValueError, 'Unused study'):
            self.load({'absent': {'meaning': 'unused'}})

    def test_malayalam_and_empty_prompts(self):
        for prompt in ('വാക്ക്', '  '):
            with self.subTest(prompt=prompt), self.assertRaises(ValueError):
                self.load({'published-id': {'meaning': prompt}})

    def test_separate_prompt_and_answer_notes(self):
        data, study, chapters = self.load({'published-id': {
            'recall': 'a word (noun)', 'alternatives': ['മറ്റൊരു വാക്ക്'],
            'explanation': 'Accept either word for this broad cue.'}})
        note = create_decks(data, study, chapters)[1].notes[0]
        self.assertIn('<div class="english-meaning">' + format_card_text('word') + '</div>', note.fields[2])
        self.assertIn('<div class="english-recall">' + format_card_text('a word (noun)') + '</div>', note.fields[2])
        self.assertIn('Also accept:', note.fields[5])
        self.assertNotIn('Also accept:', note.fields[2])

    def test_invalid_study_metadata(self):
        for metadata in ({'recall': 'വാക്ക്'}, {'recall': ''},
                         {'alternatives': 'word'}, {'alternatives': ['']},
                         {'typo': 'word'}, 'word'):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.load({'published-id': metadata})

    def test_punctuation_collisions_need_reciprocal_alternatives(self):
        first = self.data['entries'][0]
        second = {**first, 'id': 'second', 'malayalam': 'മറ്റൊന്ന്', 'english': 'Word!'}
        entries = [first, second]
        with self.assertRaisesRegex(ValueError, 'Ambiguous recall'):
            audit_recall(entries, {})
        study = {'published-id': {'alternatives': ['മറ്റൊന്ന്']}}
        with self.assertRaisesRegex(ValueError, 'Ambiguous recall'):
            audit_recall(entries, study)
        study['second'] = {'alternatives': ['വാക്ക്']}
        self.assertEqual(len(audit_recall(entries, study)), 1)

    def test_incomplete_front(self):
        self.data['entries'][0]['english'] = '(n.)'
        with self.assertRaisesRegex(ValueError, 'Incomplete recall'):
            self.load()

    def test_same_spelling_different_senses_use_separate_prompts(self):
        self.data['entries'].append({**self.data['entries'][0], 'id': 'second', 'english': 'another sense'})
        data, study, chapters = self.load({'second': {'recall': 'a different sense'}})
        notes = create_decks(data, study, chapters)[1].notes
        self.assertNotIn('a different sense', notes[0].fields[2])
        self.assertIn('a different sense', notes[1].fields[2])

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


class FormattingTests(unittest.TestCase):
    def test_main_word_and_usage_have_separate_lines(self):
        rendered = format_card_text('your (plural or polite singular; possessive pronoun)')
        self.assertIn('<div class="prompt-main">your</div>', rendered)
        self.assertIn('<div class="prompt-cue">plural or polite singular</div>', rendered)
        self.assertIn('<div class="prompt-cue">possessive pronoun</div>', rendered)

    def test_sentence_parentheses_and_nested_cues(self):
        rendered = format_card_text('if (you) come (verb (not a noun); polite)')
        self.assertIn('<div class="prompt-main">if (you) come</div>', rendered)
        self.assertIn('<div class="prompt-cue">verb (not a noun)</div>', rendered)
        self.assertIn('<div class="prompt-cue">polite</div>', rendered)
        self.assertEqual(format_card_text('(I) wish to'),
                         '<div class="prompt-main">(I) wish to</div>')

    def test_multiple_cues_and_escaped_text(self):
        rendered = format_card_text('say <hello> (a & b) (formal)')
        self.assertIn('say &lt;hello&gt;', rendered)
        self.assertLess(rendered.index('a &amp; b'), rendered.index('formal'))
        self.assertIn('unclosed (cue', format_card_text('unclosed (cue'))


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
