# Malayalam vocabulary and Anki decks

`moag.json` is the generated vocabulary catalog shared by the glossary and Anki.
Lesson and appendix Markdown tables are the editable source. Their adjacent
`vocabulary-table` comments explicitly declare inclusion and handling; heading
names no longer decide whether a table is exported. Untagged exercise tables
are ignored.

```html
<!-- vocabulary-table: {"kind":"vocabulary","category":"personal_pronoun","origin":"reference_table","cards":true} -->
```

The marker must immediately precede its table, after a stable source anchor.
Each marker uses these rules:

| Field | Meaning |
|---|---|
| `kind: "vocabulary"` | Export named word/meaning columns into the shared catalog. |
| `cards: true` | Include entries in Anki as well as the glossary. |
| `cards: false` | Include vocabulary entries in the glossary only. |
| `cards: ["മുകളിൽ", "താഴെ"]` | Select rows containing these forms for cards; other rows remain glossary-only. Missing selected forms fail validation. |
| `word`, `meaning` | Optional column names; defaults are `Malayalam` and `English`. |
| `aliases: "br"` | Treat line-separated forms as alternatives for the row’s broad meaning. Keep the first as the head form and display the others as accepted answers. |
| `category` | Required descriptive category, such as `personal_pronoun` or `postposition`; it does not decide inclusion. |
| `origin: "reference_table"` | A reference-list addition, merged with matching published vocabulary where appropriate. Default `textbook` preserves published vocabulary/audio identities. |
| `case` | Postposition case group; supplies the English recall cue. Appendix D’s starred possessive restrictions are preserved. |
| `chapter` | Lesson placement for an appendix entry. The selected everyday Appendix D cards are grouped with Lesson 6’s introduction to postpositions. |
| `kind: "paradigm"`, `group` | Validate one complete seven-case chart, possibly split across tables; do not flatten it into isolated word cards. Set `cards: false`. |
| `kind: "reference"` | Validate a teaching table without exporting it. Set `cards: false`. |

Unknown options, malformed markers, missing columns, incomplete meanings, and
incomplete paradigms fail the build. An unresolved source row must carry an
explicit exclusion reason, for example:
`<!-- vocabulary-exclude: English meaning absent in source; requires review -->`.
The audit reports these exclusions. Appendix D’s unglossed പടി is currently
excluded rather than assigned a guessed meaning.

The catalog now includes the basic personal pronouns and adverb/question-word
trios in Lesson 2, demonstratives in Lesson 3, dative pronouns in Lesson 4,
possessives in Lesson 6, one-piece indefinite forms in Lesson 22, and Appendix D’s
postposition rows. Full case charts and two-piece relative constructions remain
validated reference tables. The glossary is deliberately more extensive than the
selected study deck; this is a course catalog, not a general Malayalam dictionary.

Identical word-and-meaning rows within a lesson are combined. When a reference
table repeats a word already taught in that lesson’s vocabulary, its source link
is attached to the published entry rather than creating another note. Distinct
new senses remain separate. Existing entry IDs and all audio associations are
preserved; newly added reference forms are text-only unless a verified recording
is explicitly associated. `source_anchor`, `references`, `variants`, `category`,
and `study` carry the source and selection information. Absent `study` means true
for backward compatibility with published vocabulary entries.

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

There are 1,085 notes and 2,170 cards: Malayalam → English and English → Malayalam.
The answer includes the recording where available, with the recorded form labeled
when it differs from the written entry. All 997 MP3 clips and a Malayalam font
are embedded for offline use. The 160 study entries without recordings are text-only.
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
to the Anki source repository are needed. Generated card visibility and layout have also been checked in a browser at desktop and phone widths; the native Anki GUI was not separately tested.

The reusable `.github/workflows/unit-tests.yml` runs table-contract, coverage,
identity, exporter, and audio alignment tests, plus catalog/glossary freshness
checks. The site workflow calls it as `unit-tests`; both site assembly and
deployment explicitly depend on its success. The separate Anki job runs official
Anki import/reimport tests and builds the deck alongside the EPUB/PDF workflow. Each run
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

Run `bun run test` in a Python environment with `requirements/anki.txt` installed
(or run the same Python commands from the package script). Coverage tests assert
that core pronouns, question words and postpositions stay available for study,
that source links resolve, and that social-ranking labels do not return in tables
or headers. The `--check` commands detect stale generated outputs.

## Site glossary

Run `python3 scripts/build-vocabulary-glossary.py` after rebuilding the catalog
to generate `docs/vocabulary-glossary.md`; add `--check` to detect stale output.
The page combines identical word-and-meaning pairs across chapters, keeps distinct
meanings separate, links every occurrence to its lesson, and reuses the site audio
player. Browser controls filter by Malayalam/English text and chapter. The original
source glossary in `docs/glossary.md` is preserved separately.
