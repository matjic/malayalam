"""Regression checks for browser-only links and audio controls in EPUB export."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('epub_builder', ROOT / 'scripts/build-epub.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ExportTests(unittest.TestCase):
    def prepare(self, text, name="example.md"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text('# Example\n\n' + text)
            return builder.prepare(path, {'example.md'})

    def test_browser_download_becomes_online_link(self):
        text = self.prepare('<a href="assets/decks/malayalam-moag.apkg" download data-ignore>Download Anki</a>')
        self.assertIn('[Download Anki](https://ml.matj.io/assets/decks/malayalam-moag.apkg)', text)
        self.assertNotIn('data-ignore', text)
        self.assertNotIn('<a ', text)

    def test_review_page_is_not_a_missing_epub_resource(self):
        text = self.prepare('<a href="audio-audit-remaining.html" target="_blank">Review</a>')
        self.assertIn('[Review](https://ml.matj.io/audio-audit-remaining.html)', text)

    def test_nested_audio_panels_are_removed(self):
        text = self.prepare('<div class="lesson-audio"><p><strong>Vocabulary audio</strong></p>'
            '<audio controls src="assets/audio/example.mp3" aria-label="Vocabulary"></audio>'
            '<div class="lesson-audio-cues"><button data-audio-src="assets/audio/example.mp3">Listen</button></div>'
            '<p class="lesson-audio-note">Browser note</p></div>')
        self.assertNotIn('example.mp3', text)
        self.assertNotIn('Vocabulary audio', text)
        self.assertNotIn('<button', text)
        self.assertNotIn('Browser note', text)

    def test_word_player_is_removed(self):
        text = self.prepare('<button type="button" data-row-audio-src="assets/audio/moag/words/lesson_05_word_005.mp3" data-audio-label="പഠിക്കുന്നു" aria-pressed="false">▶</button>')
        self.assertNotIn('.mp3', text)
        self.assertNotIn('<button', text)

    def test_audio_column_is_removed_without_dropping_added_vocabulary(self):
        text = self.prepare('| Malayalam | English | Audio |\n|---|---|---|\n'
            '| പഠിക്കുന്നു | is studying | <button data-row-audio-src="word.mp3">▶</button> |\n'
            '| <!-- recorded-audio-row --> ഇപ്പോൾ | now | <button data-row-audio-src="now.mp3">▶</button> |\n')
        self.assertIn('പഠിക്കുന്നു | is studying', text)
        self.assertIn('ഇപ്പോൾ | now', text)
        self.assertNotIn('Audio', text)
        self.assertNotIn('.mp3', text)

    def test_written_alphabet_remains_without_recitation_section(self):
        text = self.prepare('<!-- letter-audio -->\n### Recitations\n<audio src="alphabet.mp3"></audio>\n<!-- /letter-audio -->\n'
                            '| Letter | Sound |\n|---|---|\n| അ | a |\n')
        self.assertIn('| അ | a |', text)
        self.assertNotIn('Recitations', text)

    def test_export_omits_site_and_original_printed_contents(self):
        from book_export import book_paths, prepare
        self.assertNotIn('contents.md', [p.name for p in book_paths()])
        front = ROOT / 'docs/front-matter.md'
        text = prepare(front, {p.name for p in book_paths()})
        self.assertNotIn('## Table of Contents', text)
        self.assertNotIn('Original printed page', text)
        self.assertNotIn('reading-navigation', text)
        self.assertIn('Spring, 2002', text)

    def test_vocabulary_is_compact_without_changing_grammar_tables(self):
        table = '| Malayalam | English |\n|---|---|\n| പഠിക്കുന്നു | is studying |\n| ഇപ്പോൾ | now |\n'
        text = self.prepare('## Reference List\n\n' + table + '\n## Vocabulary\n\n' + table + '\n## Grammar\n\n' + table, 'lesson1.md')
        self.assertEqual(text.count('::: {.vocabulary-list}'), 1)
        self.assertEqual(text.count('class="vocabulary-term"'), 2)
        self.assertIn('പഠിക്കുന്നു</span> <span class="vocabulary-definition">is studying', text)
        self.assertIn('ഇപ്പോൾ</span> <span class="vocabulary-definition">now', text)
        self.assertEqual(text.count('| Malayalam | English |'), 2)

    def test_long_vocabulary_forms_get_their_own_line(self):
        text = self.prepare('## Vocabulary\n\n| Malayalam | English |\n|---|---|\n'
                            '| ആഘോഷിക്കപ്പെടുക (past: ആഘോഷിക്കപ്പെട്ടു) | to be celebrated |\n', 'lesson20.md')
        self.assertIn('vocabulary-entry-long', text)
        self.assertIn('ആഘോഷിക്കപ്പെടുക (past: ആഘോഷിക്കപ്പെട്ടു)', text)
        self.assertIn('to be celebrated', text)

    def test_source_comments_do_not_split_numbered_items(self):
        import json
        import subprocess
        source = '1. Translate these sentences.\n\n   1. First.\n   2. Second.\n\n   <!-- Source: PDF page 51; printed page 5. -->\n\n   3. Third.\n'
        prepared = self.prepare(source)
        self.assertNotIn('<!-- Source:', prepared)
        ast = json.loads(subprocess.check_output(['pandoc', '-f', 'markdown-auto_identifiers', '-t', 'json'], input=prepared.encode()))
        lists = []
        def visit(value):
            if isinstance(value, dict):
                if value.get('t') == 'OrderedList':
                    lists.append(len(value['c'][1]))
                visit(value.get('c'))
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(ast['blocks'])
        self.assertEqual(lists, [1, 3])


if __name__ == '__main__':
    unittest.main()
