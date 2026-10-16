# Malayalam vocabulary and Anki decks

`moag.json` is a reusable, chapter-organized export of the vocabulary tables in
`docs/lesson1.md` through `docs/lesson25.md`, plus the recorded derived noun in
the Reference List. It includes the additional recorded forms added to those
tables, English meanings, origin, source chapter, and audio paths/transcripts/
checksums. Identical word-and-meaning rows within a chapter are combined, keeping
all their recordings. Words repeated in different chapters remain separate notes.

The Markdown remains the editable source. Rebuild this catalog after changing
the tables; the website needs no runtime JSON fetching or new Markdown syntax.
The Anki exporter consumes the catalog rather than parsing the tables again.
This is a course vocabulary catalog, not a general Malayalam dictionary.

## Import and study

Open `dist/anki/malayalam-moag.apkg` in Anki. One package creates **Malayalam**
with 25 nested decks named **Lesson 01** through **Lesson 25**. Expand the parent
to see the lessons; each subdeck's description contains the chapter title.

There are 990 notes and 1,980 cards: Malayalam → English and English → Malayalam.
The answer includes the recording where available, with the recorded form labeled
when it differs from the written entry. All 997 MP3 clips and a Malayalam font
are embedded for offline use. The 65 entries without recordings are text-only.
The “Open lesson” link requires internet. Original audio credits and reuse terms
remain in the lesson pages and `data/audio/moag/README.md`; this export does not
change those terms. Repository license: CC-BY-NC-SA-4.0.

All lessons are initially available. To begin, select **Lesson 01** and study that
subdeck. To use the parent deck for cumulative study without introducing later
chapters, first suspend their new cards:

1. In desktop Anki, open **Browse** and switch to **Cards** mode.
2. Search `deck:Malayalam -tag:moag::lesson_01 is:new`.
3. Select all results and use **Cards → Toggle Suspend**. They become suspended.
4. Study **Malayalam** to review Lesson 1.
5. When ready for Lesson 2, search `tag:moag::lesson_02 is:suspended`, select all,
   and use **Toggle Suspend** again. Repeat for each later lesson.

Suspension preserves progress and due reviews. New-card limits control the daily
pace; both directions count as cards. Sibling cards may be buried until a later
day according to your Anki settings. You can also study a single chapter by
selecting its subdeck. Tags include `moag::lesson_01`, `moag::textbook`,
`moag::recorded_addition`, and `audio::available`/`audio::unavailable`.

Reimporting the same package does not duplicate notes or reset review progress.
The generator uses stable model/deck IDs and note GUIDs. A note's initial identity
includes chapter, written form, and meaning; changing those identity fields creates
a new note. Do not delete and recreate decks to update them.

## Build and validate

Use Python 3.10 or newer with a working standard library:

```sh
python3 -m venv /private/tmp/malayalam-anki-env
/private/tmp/malayalam-anki-env/bin/python -m pip install -r requirements/anki.txt
/private/tmp/malayalam-anki-env/bin/python scripts/build-vocabulary-catalog.py
/private/tmp/malayalam-anki-env/bin/python scripts/build-anki.py
/private/tmp/malayalam-anki-env/bin/python scripts/build-vocabulary-catalog.py --check
```

Outputs go to ignored `dist/anki/` (override with `--output`). For import tests,
install `requirements/anki-test.txt` in the same environment and run
`scripts/test_anki.py`. The test imports into a disposable collection, checks card
rendering, chapter organization, embedded media and blank audio fields, then
reimports to check deduplication and preservation of review progress.

Validated using genanki 0.13.1 and the official Anki 26.9.3 Python backend.
The local Anki source's package metadata implementation confirms support for the
legacy `collection.anki2`/media-map package format used by genanki. No modifications
to the Anki source repository are needed. GUI/mobile appearance was not separately
tested.

## Site glossary

Run `python3 scripts/build-vocabulary-glossary.py` after rebuilding the catalog
to generate `docs/vocabulary-glossary.md`; add `--check` to detect stale output.
The page combines identical word-and-meaning pairs across chapters, keeps distinct
meanings separate, links every occurrence to its lesson, and reuses the site audio
player. Browser controls filter by Malayalam/English text and chapter. The original
source glossary in `docs/glossary.md` is preserved separately.
