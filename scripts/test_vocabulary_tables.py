"""Source contracts and essential coverage regressions, independent of Anki."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from audio_tables import TABLE
from vocabulary_tables import CASES, clean, read_tables, word_rows

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalog_builder', Path(__file__).with_name('build-vocabulary-catalog.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def marked(rows='| വാക്ക് | word |', **options):
    config = dict(kind='vocabulary', category='example', cards=True)
    config.update(options)
    return ('<a id="test-words"></a>\n### A renamed heading\n'
            '<!-- vocabulary-table: ' + json.dumps(config) + ' -->\n'
            '| Malayalam | English |\n|---|---|\n' + rows + '\n')


class TableContractTests(unittest.TestCase):
    def test_labels_not_heading_names_control_inclusion(self):
        self.assertEqual(read_tables('| Malayalam | English |\n|---|---|\n| വാക്ക് | word |\n', 'test'), [])
        table = read_tables(marked(), 'test')[0]
        self.assertEqual(list(word_rows(table, 'test'))[0]['malayalam'], 'വാക്ക്')
        self.assertEqual(table.anchor, 'test-words')

    def test_named_columns_and_aliases(self):
        text = marked(aliases='br', word='Form').replace('| Malayalam | English |', '| English | Form |')
        text = text.replace('| വാക്ക് | word |', '| our | നമ്മുടെ<br>നമ്മളുടെ |')
        row = list(word_rows(read_tables(text, 'test')[0], 'test'))[0]
        self.assertEqual(row['english'], 'our')
        self.assertEqual(row['malayalam'], 'നമ്മുടെ')
        self.assertEqual(row['variants'], ['നമ്മളുടെ'])

    def test_malformed_contracts_cannot_silently_drop_words(self):
        examples = [marked().replace('"cards": true', '"cards": "yes"'),
                    marked().replace('"category": "example"', '"catgory": "example"'),
                    marked().replace(' -->', ' broken -->'),
                    marked().replace('| Malayalam |', 'unrelated prose\n| Malayalam |'),
                    marked().replace('<a id="test-words"></a>', ''),
                    marked().replace('| word |', '| word | extra |')]
        for text in examples:
            with self.subTest(text=text), self.assertRaises(ValueError):
                read_tables(text, 'test')

    def test_missing_meaning_requires_an_explicit_exclusion_reason(self):
        for meaning in ('', '(n.)'):
            with self.subTest(meaning=meaning), self.assertRaisesRegex(ValueError, 'incomplete'):
                read_tables(marked(f'| പടി | {meaning} |'), 'test')
        text = marked('| പടി <!-- vocabulary-exclude: source meaning missing; needs review --> | |')
        self.assertEqual(list(word_rows(read_tables(text, 'test')[0], 'test')), [])
        with self.assertRaisesRegex(ValueError, 'reason'):
            read_tables(text.replace('source meaning missing; needs review', ''), 'test')

    def test_selected_practice_form_cannot_disappear(self):
        with self.assertRaisesRegex(ValueError, 'disappeared'):
            read_tables(marked(cards=['നീ']), 'test')

    def test_paradigm_must_have_every_case_once_across_split_tables(self):
        options = dict(kind='paradigm', category='pronoun', cards=False, group='singular')
        rows = ['| ' + case + ' | ഞാൻ |' for case in sorted(CASES)]
        text = ('<a id="pronouns"></a>\n<!-- vocabulary-table: ' + json.dumps(options)
                + ' -->\n| Case | First person |\n|---|---|\n' + '\n'.join(rows) + '\n')
        read_tables(text, 'test')
        for broken in (text.replace(rows[0] + '\n', ''), text + text):
            with self.assertRaisesRegex(ValueError, 'seven cases'):
                read_tables(broken, 'test')


class CourseCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = builder.catalog()
        cls.entries = cls.catalog['entries']
        cls.practice = [e for e in cls.entries if e.get('study', True)]
        cls.forms = {form for e in cls.practice for form in [e['malayalam'], *e.get('variants', [])]}

    def test_essential_pronouns_and_cases_are_study_entries(self):
        required = {
            'ഞാൻ', 'നീ', 'നിങ്ങൾ', 'നമ്മൾ', 'ഞങ്ങൾ', 'അവൻ', 'ഇവൻ', 'അവൾ', 'ഇവൾ',
            'അയാൾ', 'ഇയാൾ', 'അദ്ദേഹം', 'ഇദ്ദേഹം', 'അവർ', 'ഇവർ',
            'എന്റെ', 'നിന്റെ', 'നിങ്ങളുടെ', 'നമ്മുടെ', 'നമ്മളുടെ', 'ഞങ്ങളുടെ',
            'അവന്റെ', 'അവളുടെ', 'അവരുടെ', 'എനിക്ക്', 'നിനക്ക്', 'നിങ്ങൾക്ക്',
            'നമുക്ക്', 'നമ്മൾക്ക്', 'ഞങ്ങൾക്ക്',
        }
        self.assertFalse(required - self.forms, f'Missing core forms: {required - self.forms}')

    def test_question_words_and_core_postpositions_are_study_entries(self):
        required = {'ആര്', 'എന്ത്', 'ഏത്', 'എവിടെ', 'എപ്പോൾ', 'എങ്ങനെ', 'എത്ര',
                    'മുകളിൽ', 'താഴെ', 'ഇടയിൽ', 'കുറിച്ച്', 'ശേഷം', 'പകരം', 'നിന്ന്', 'വരെ', 'കൂടെ'}
        self.assertFalse(required - self.forms, f'Missing function words: {required - self.forms}')

    def test_both_senses_of_plural_and_honorific_pronouns_are_kept(self):
        meanings = [e['english'] for e in self.practice if e['malayalam'] == 'അവർ']
        self.assertTrue(any(m.startswith('she') for m in meanings))
        self.assertTrue(any(m.startswith('they') for m in meanings))
        meanings = [e['english'] for e in self.practice if e['malayalam'] == 'നിങ്ങൾ']
        self.assertTrue(any('singular' in m for m in meanings))
        self.assertTrue(any('plural' in m for m in meanings))

    def test_reference_only_is_an_explicit_distinction(self):
        self.assertTrue(any(e.get('study') is False for e in self.entries))
        self.assertTrue(all(e['category'] == 'postposition' for e in self.entries if e.get('study') is False))
        tables = read_tables((ROOT / 'docs/lesson8.md').read_text(), 'lesson8')
        self.assertEqual({t.options['group'] for t in tables if t.options['kind'] == 'paradigm'},
                         {'singular', 'plural', 'marked'})

    def test_starred_possessive_postpositions_keep_their_case_restriction(self):
        meanings = [e['english'] for e in self.entries if e['malayalam'] == 'ചുറ്റും']
        possessive = next(m for m in meanings if 'possessive' in m)
        self.assertNotIn('also dative', possessive)
        nearby = next(e for e in self.entries if e['origin'] == 'reference_table'
                      and e['malayalam'] == 'അടുത്ത്')
        self.assertIn('also dative', nearby['english'])

    def test_source_links_resolve_to_actual_table_anchors(self):
        for entry in self.entries:
            if entry.get('source_anchor'):
                text = (ROOT / entry['source']).read_text()
                self.assertIn(f'<a id="{entry["source_anchor"]}"></a>', text)

    def test_reference_aliases_survive_merging_into_published_vocabulary(self):
        entry = next(e for e in self.entries if e['chapter'] == 22 and e['malayalam'] == 'ആർക്കെങ്കിലും')
        self.assertEqual(entry['origin'], 'textbook')
        self.assertIn('ആർക്കായാലും', entry['variants'])

    def test_every_existing_vocabulary_table_is_explicitly_labeled(self):
        for n in range(1, 26):
            text = (ROOT / f'docs/lesson{n}.md').read_text()
            heading = re.search(r'^(#{2,3}) Vocabulary\n', text, re.M)
            body = text[heading.end():]
            end = re.search(r'^#{1,' + str(len(heading[1])) + r'} ', body, re.M)
            body = body[:end.start()] if end else body
            self.assertGreater(len(TABLE.findall(body)), 0)
            self.assertEqual(body.count('vocabulary-table:'), len(TABLE.findall(body)), f'Lesson {n}')

    def test_cards_false_also_applies_to_original_vocabulary_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs/assets/audio/moag/words').mkdir(parents=True)
            for path in (ROOT / 'docs').glob('lesson*.md'):
                shutil.copyfile(path, root / 'docs' / path.name)
            manifest = 'docs/assets/audio/moag/words/manifest.json'
            shutil.copyfile(ROOT / manifest, root / manifest)
            path = root / 'docs/lesson1.md'
            path.write_text(path.read_text().replace('"cards":true', '"cards":false', 1)
                            .replace('"category":"vocabulary"', '"category":"custom_category"', 1))
            entries = builder.catalog(root)['entries']
            name = next(e for e in entries if e['chapter'] == 1 and e['malayalam'] == 'പേര്')
            self.assertIs(name['study'], False)
            self.assertEqual(name['category'], 'custom_category')

    def test_social_ranking_labels_cannot_return_in_tables_or_headers(self):
        for path in (ROOT / 'docs').glob('*.md'):
            for table in TABLE.finditer(path.read_text()):
                self.assertIsNone(re.search(r'\b(?:inferior|superior)s?\b|equal to (?:the )?speaker',
                                            clean(table[0]), re.I), path.name)


if __name__ == '__main__':
    unittest.main()
