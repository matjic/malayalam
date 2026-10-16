"""Regressions for adjacent vocabulary clips being assigned to the same word."""

import json
from pathlib import Path
import re
import unittest
from collections import Counter

from audio_lexicon import english_score

ROOT = Path(__file__).resolve().parents[1]


class AudioRowAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "docs/assets/audio/moag/words/manifest.json").read_text()
        )
        cls.clips = {Path(c["path"]).stem: c for c in cls.manifest["clips"]}

    def test_neighboring_english_segment_cannot_label_examination_as_tomorrow(self):
        pair = dict(
            utterances=[
                dict(start=188.2036, end=189.0081),
                dict(start=189.8414, end=190.6385),
            ],
            english_segments=[dict(start=183.73, end=188.73, text="naale")],
        )
        self.assertEqual(english_score(pair, dict(text="നാളെ", meaning="tomorrow")), 0)

    def test_whole_multiword_segment_does_not_supply_each_neighbor_label(self):
        pair = dict(
            utterances=[dict(start=2, end=4)],
            english_segments=[dict(start=0, end=6, text="naale pareeksha")],
        )
        self.assertLess(english_score(pair, dict(text="നാളെ", meaning="tomorrow")), 0.8)

    def test_corrected_labels(self):
        expected = {
            "lesson_08_word_011": "നാളെ",
            "lesson_08_word_012": "പരീക്ഷ",
            "lesson_02_word_010": "ആഫീസിൽ",
            "lesson_06_word_013": "ധാരാളം",
            "lesson_12_word_006": "വയറ്",
            "lesson_14_word_025": "കല",
            "lesson_25_word_059": "സംഗീതം",
        }
        for clip, word in expected.items():
            with self.subTest(clip=clip):
                self.assertEqual(self.clips[clip]["transcript"], word)

    def test_tomorrow_and_examination_have_their_own_row_controls(self):
        text = (ROOT / "docs/lesson8.md").read_text()
        tomorrow = next(
            line for line in text.splitlines() if line.startswith("| നാളെ |")
        )
        examination = next(
            line for line in text.splitlines() if line.startswith("| പരീക്ഷ |")
        )
        self.assertEqual(
            re.findall(r'data-row-audio-src="([^"]+)"', tomorrow),
            ["assets/audio/moag/words/lesson_08_word_011.mp3"],
        )
        self.assertEqual(
            re.findall(r'data-row-audio-src="([^"]+)"', examination),
            ["assets/audio/moag/words/lesson_08_word_012.mp3"],
        )

    def test_repaired_neighbors_keep_their_own_original_table_rows(self):
        expected = {
            "lesson_04_word_027": "അവന്",
            "lesson_04_word_028": "പണം",
            "lesson_04_word_029": "ഒന്ന്",
            "lesson_21_word_015": "തരുക",
            "lesson_21_word_016": "പറഞ്ഞുതരുക",
            "lesson_24_word_027": "സ്നേഹം",
            "lesson_24_word_028": "തമ്മിൽ",
            "lesson_24_word_051": "ഗുണം",
            "lesson_24_word_052": "കുറവ്",
        }
        for clip_id, word in expected.items():
            clip = self.clips[clip_id]
            self.assertEqual(clip["transcript"], word)
            self.assertEqual(clip["status"], "matched")
            text = (ROOT / f"docs/lesson{clip['lesson']}.md").read_text()
            row = next(
                line
                for line in text.splitlines()
                if f'data-row-audio-src="{clip["path"][5:]}"' in line
            )
            self.assertNotIn("recorded-audio-row", row)
            self.assertNotIn("check match", row)
        reference = (ROOT / "docs/lesson24.md").read_text().split("## Vocabulary", 1)[0]
        self.assertIn(
            'data-row-audio-src="assets/audio/moag/words/lesson_24_word_027.mp3"',
            reference,
        )
        self.assertIn("| സ്നേഹിക്കുക | to love | സ്നേഹം | love |", reference)

    def test_context_checked_swaps_and_phrase_assignments(self):
        expected = {
            "lesson_09_word_018": "കൂട്ടുകാരി",
            "lesson_09_word_019": "കൂട്ടുകാരൻ",
            "lesson_10_word_014": "കിഴക്ക്",
            "lesson_10_word_015": "കിഴക്കേ",
            "lesson_16_word_010": "അവിടുത്തെ",
            "lesson_16_word_011": "ഇവിടുത്തെ",
            "lesson_20_word_022": "ആകാശം",
            "lesson_20_word_024": "വളരുക",
            "lesson_24_word_011": "നേരിൽ",
            "lesson_24_word_012": "നേഴ്സ്",
            "lesson_25_word_024": "മഞ്ഞൾ",
            "lesson_25_word_025": "കുരുമുളക്",
            "lesson_19_word_047": "എനിക്ക് നിങ്ങളെ സ്ഥലം മാറ്റേണ്ടതായി വരും",
        }
        for clip_id, transcript in expected.items():
            self.assertEqual(self.clips[clip_id]["transcript"], transcript)
        self.assertEqual(self.clips["lesson_05_word_005"]["status"], "matched")
        self.assertEqual(self.clips["lesson_05_word_005"]["transcript"], "പഠിക്കുന്നു")
        self.assertNotIn("lesson_20_word_041", self.clips)

    def test_silence_and_retired_repeat_do_not_reappear_as_words(self):
        removed = [
            "lesson_11_word_035",
            "lesson_15_word_020",
            "lesson_16_word_043",
            "lesson_20_word_070",
            "lesson_21_word_013",
            "lesson_22_word_059",
            "lesson_11_word_012",
            "lesson_20_word_041",
        ]
        for clip_id in removed:
            self.assertNotIn(clip_id, self.clips)
            lesson = int(clip_id.split("_")[1])
            self.assertNotIn(
                f'data-row-audio-src="assets/audio/moag/words/{clip_id}.mp3"',
                (ROOT / f"docs/lesson{lesson}.md").read_text(),
            )
        atra = self.clips["lesson_11_word_011"]
        self.assertEqual(atra["transcript"], "അത്ര")
        self.assertEqual((atra["start"], atra["end"]), (161.2, 164.7))

    def test_every_clip_is_present_once_and_uncertain_matches_are_explicit(self):
        for lesson in range(1, 26):
            text = (ROOT / f"docs/lesson{lesson}.md").read_text()
            expected = [
                clip for clip in self.manifest["clips"] if clip["lesson"] == lesson
            ]
            paths = re.findall(r'data-row-audio-src="([^"]+)"', text)
            self.assertEqual(
                Counter(paths), Counter(clip["path"][5:] for clip in expected)
            )
            for clip in expected:
                if clip["status"] != "matched":
                    row = next(
                        line
                        for line in text.splitlines()
                        if f'data-row-audio-src="{clip["path"][5:]}"' in line
                    )
                    if (
                        clip.get("label_review", {}).get("placement")
                        == "unplaced_recorded_form"
                    ):
                        self.assertIn("Recorded form:", row)
                        self.assertIn("check placement", row)
                    else:
                        self.assertIn("Unconfirmed:", row)
                        self.assertIn("check match", row)


if __name__ == "__main__":
    unittest.main()
