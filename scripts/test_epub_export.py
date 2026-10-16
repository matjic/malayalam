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
    def prepare(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'example.md'
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

    def test_word_player_becomes_recording_link(self):
        text = self.prepare('<button type="button" data-row-audio-src="assets/audio/moag/words/lesson_05_word_005.mp3" data-audio-label="പഠിക്കുന്നു" aria-pressed="false">▶</button>')
        self.assertIn('[പഠിക്കുന്നു](' + builder.AUDIO_BASE + 'assets/audio/moag/words/lesson_05_word_005.mp3)', text)
        self.assertNotIn('<button', text)


if __name__ == '__main__':
    unittest.main()
