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

`study.json` contains editorial study metadata keyed by stable catalog entry ID,
so a spelling used in different lessons or senses can have different prompts:

- `meaning`: optional English answer wording, including English spellings for names.
- `recall`: optional English → Malayalam question; defaults to the meaning.
- `alternatives`: other Malayalam answers accepted for this specific prompt.
- `explanation`: usage or grammar guidance shown after revealing the answer.

Correct incomplete or inaccurate meanings in the lesson table first, then rebuild
the catalog and glossary. Put exercise-specific instructions in `study.json`.
Do not invent a register distinction just to make synonyms unique: use a natural
context or accept alternatives for a broad prompt. Grammar constructions and
inflected forms need explicit cues about the requested form. Parenthesized past
tenses and plurals on the Malayalam answer remain reference information unless
explicitly requested. Anki uses self-grading; alternatives are displayed guidance,
not an automatic answer matcher.

This replaces the former spelling-keyed `anki-english.json`. The English Anki
field stores separate `english-meaning` and `english-recall` display blocks; the
card template and CSS select the appropriate block. This preserves the published
six-field model, template order, GUIDs, and review history. It also keeps detailed
recall instructions off the visible Malayalam → English answer. Edit metadata
and rebuild rather than editing these generated HTML blocks manually.
Trailing parenthetical usage cues render below the main meaning in smaller type.
Semicolons inside a cue separate lines; nested parentheses and parentheses inside
sentences are preserved. This formatting applies to both English prompts and
English answers. Accepted alternatives render as separate list items.

The exporter rejects Malayalam script in English meanings and recall prompts.
Original glosses containing Malayalam forms, accepted alternatives, and usage
notes appear only after revealing the answer. Original glosses and editorial
notes share the existing `Source` field with the lesson link.

`python scripts/audit-vocabulary-prompts.py` checks every entry and reports shared
prompts whose answers are explicitly accepted. Checks ignore punctuation and case,
reject incomplete fronts such as “(n.)”, and require reciprocal alternatives when
different Malayalam entries share a prompt. They run during every deck build and
in the exporter tests. Different wording can still conceal a meaning overlap;
these checks do not replace linguistic review.

The initial recall review covered the 25-lesson catalog, exact and punctuation-only
collisions, shared short English glosses, pronoun/address distinctions, commands,
and head forms versus inflected forms. Metadata clarifies those cases rather than
claiming that all possible English-to-Malayalam translations are unique.

Pronoun descriptions use familiar/non-honorific, neutral, and honorific rather
than labeling people “inferior” or “superior.” Lesson 1 explains that familiarity,
age, social distance, and deference interact, and that familiar forms can be
inappropriate where a polite form is expected. These are descriptions of usage,
not personal worth. The original course's explanations are retained in the source
PDF; revised teaching descriptions are identified editorially in the lessons.
The [WALS Malayalam politeness notes](https://wals.info/valuesets/45A-mym), citing
Asher and Kumari (1997), corroborate the importance of both familiarity and regional
variation; they do not support treating every familiar form as universally rude.

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
The generator uses stable model/deck IDs and note GUIDs. The catalog builder
preserves published entry IDs across unambiguous spelling or meaning corrections.
If changing both fields, edit the catalog entry while retaining its ID before
rebuilding. Do not delete and recreate decks to update them.

## Build and validate

Use Python 3.10 or newer with a working standard library:

```sh
python3 -m venv /private/tmp/malayalam-anki-env
/private/tmp/malayalam-anki-env/bin/python -m pip install -r requirements/anki.txt
/private/tmp/malayalam-anki-env/bin/python scripts/build-vocabulary-catalog.py
/private/tmp/malayalam-anki-env/bin/python scripts/build-anki.py
/private/tmp/malayalam-anki-env/bin/python scripts/build-vocabulary-catalog.py --check
```

Outputs go to ignored `dist/anki/` (override with `--output`). The CLI also updates
`docs/assets/decks/malayalam-moag.apkg`; use `--no-site-copy` for an isolated build.
For import tests,
install `requirements/anki-test.txt` in the same environment and run
`scripts/test_anki_export.py` and `scripts/test_anki.py`. The first checks input
validation and compatibility contracts. The second builds a fresh package in a
temporary directory, imports into a disposable collection, and checks card
rendering, chapter organization, embedded media and blank audio fields, then
reimports to check deduplication and preservation of review progress.

Validated using genanki 0.13.1 and the official Anki 26.9.3 Python backend.
The local Anki source's package metadata implementation confirms support for the
legacy `collection.anki2`/media-map package format used by genanki. No modifications
to the Anki source repository are needed. GUI/mobile appearance was not separately
tested.

GitHub Actions runs the catalog and identity checks, exporter tests, official Anki
import/reimport tests, and deck build alongside the EPUB/PDF workflow. Each run
uploads `dist/anki/` as the `malayalam-anki` artifact. Successful runs on `main`
include the freshly built package in the deployed site's deck download; CI does
not commit generated packages back to the repository.

## Exporter maintenance

`scripts/build-anki.py` is the CLI. `scripts/anki_export.py` separates catalog
validation, card rendering, media verification, deck creation, and packaging;
`scripts/anki.css` controls card appearance. Importing the module does no file IO.
The `build(output)` API returns the summary and writes only to that output folder
unless a `site_package` path is explicitly supplied. Tests never replace the site
download or rely on an older package in `dist/`.

Keep the model identity, field order, template order, deck identity keys, and entry
GUID inputs stable so reimports update existing notes. Chapter lookups use their
numbers rather than JSON array positions. Counts are derived from the catalog;
audio checksums, duplicate IDs, media name collisions, and unused English overrides
fail before package generation. Study metadata changes do not require an Anki schema migration.

## Site glossary

Run `python3 scripts/build-vocabulary-glossary.py` after rebuilding the catalog
to generate `docs/vocabulary-glossary.md`; add `--check` to detect stale output.
The page combines identical word-and-meaning pairs across chapters, keeps distinct
meanings separate, links every occurrence to its lesson, and reuses the site audio
player. Browser controls filter by Malayalam/English text and chapter. The original
source glossary in `docs/glossary.md` is preserved separately.
