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
postposition rows. It also includes the 1–10 reference list in Lesson 3,
all 114 number/fraction rows in Lesson 7, and the complete weekday list in
Appendix C, attached to Lesson 23. Full case charts and two-piece relative constructions remain
validated reference tables. The glossary is deliberately more extensive than the
selected study deck; this is a course catalog, not a general Malayalam dictionary.

### Coverage decisions from the revision audit

The November 2026 audit checked every lesson's marked tables and inventoried
unmarked lesson and appendix tables. It found that explicit inclusion alone had
missed most basic numbers and two weekdays. The deck now covers counting 1–10
in Lesson 3, followed by zero, 11–29, four fractions, tens, hundreds, thousands
2,000–9,000, and the larger units listed in Lesson 7. All seven weekdays are
available in Lesson 23. These changes add 63 notes (126 cards), while retaining
every published note ID and all 997 recordings. The new notes are text-only.

Lesson 7's other compound numbers stay in the glossary; memorizing each listed
combination is not required by this selection. Before consolidation, the catalog had
99 glossary-only source entries: 61 number rows and 38 postpositions. Seven-case charts, verb paradigms,
two-piece relative constructions, pronunciation contrasts, and exercise answers
remain reference material rather than isolated vocabulary cards.

The remaining Appendix C time expressions and Malayalam months, Appendix E
opposites, and Appendix F derivation tables have not been bulk-imported. They
mix already taught vocabulary, context-dependent forms, approximate calendar
spans, missing meanings, and unresolved source errors. This coverage decision
does not certify those lists or claim that the deck tests every grammar skill.
Review their meanings and useful recall contexts before selecting further cards.

Identical word-and-meaning rows within a lesson are combined. Cross-lesson
consolidation is controlled by `duplicates.json`: an editorial inventory of 85
repeated written/head forms, including two forms with different parenthetical
inflection notes. Each group records the source IDs, exact source glosses, and a
reason for merging or keeping senses separate. A changed source gloss, unknown
ID, repeated membership, or newly repeated unreviewed head form fails the build.
NFC normalization and stripping a trailing parenthetical annotation find candidates;
they do not authorize a merge. Different headwords that occur as accepted
alternatives are not automatically merged.

This review combines 79 redundant catalog entries into 73 shared entries. The
catalog now has **1,168 entries: 1,090 study notes and 78 glossary-only entries**
(51 number entries and 27 postpositions). All 1,247 source identities and all 997
recordings remain represented. Merged entries retain their complete original rows
in `occurrences`, including old IDs, glosses, source locations, study selection,
variants, and audio. The canonical entry reuses a published ID and aggregates its
audio and references. Its `chapter` is the earliest selected occurrence; all
contributing lessons remain tags. Newly added reference forms remain text-only
unless a verified recording is explicitly associated.

Distinct senses and selected constructions remain separate. `sense` supplies a
short context cue on the Malayalam recognition front, so a bare homograph does
not ask learners to guess which definition is wanted. For example, ആറ് retains
separate number and geography cards. Source restrictions remain visible in the
answer's linked source glosses; merging identical meanings does not establish
that their constructions are interchangeable. The contradictory case descriptions
for കൊണ്ട് are explicitly unresolved in its answer note.

`source_anchor`, `references`, `variants`, `category`, and `study` carry the source
and selection information. Absent `study` means true for backward compatibility.
Editorial combined meanings live in `duplicates.json`; exercise wording lives in
`study.json`. Edit these inputs or the lesson tables, then regenerate `moag.json`.

`study.json` contains editorial study metadata keyed by canonical catalog entry ID,
so distinct senses can have different prompts:

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

`cargo run --locked -- audit-prompts` checks every entry and reports shared
prompts whose answers are explicitly accepted. Checks ignore punctuation and case,
reject incomplete fronts such as “(n.)”, and require reciprocal alternatives when
different Malayalam entries share a prompt. They run during every deck build and
in the exporter tests. Different wording can still conceal a meaning overlap;
these checks do not replace linguistic review.

The initial recall review covered the 25-lesson catalog, exact and punctuation-only
collisions, shared short English glosses, pronoun/address distinctions, commands,
and head forms versus inflected forms. Metadata clarifies those cases rather than
claiming that all possible English-to-Malayalam translations are unique.

Pronoun descriptions use informal, neutral, and formal rather
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

There are 1,090 notes and 2,180 cards: Malayalam → English and English → Malayalam.
The answer includes the recording where available, with the recorded form labeled
when it differs from the written entry. All 997 MP3 clips and a Malayalam font
are embedded for offline use. The 179 study entries without recordings are text-only.
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

Reimporting the same package updates surviving notes without resetting their review progress.
The generator uses stable model/deck IDs and note GUIDs. The catalog builder
preserves published entry IDs across unambiguous spelling or meaning corrections.
If changing both fields, edit the catalog entry while retaining its ID before
rebuilding. Do not delete and recreate decks to update them.

### Updating an older deck after consolidation

A fresh import contains 58 fewer notes (116 fewer cards). Anki does not remove
old notes merely because an updated package omits them. Existing installations
therefore need one cleanup step after importing the new package.

The generated [merge map](merged-notes.tsv) lists all 58 retired study IDs,
their surviving IDs, original meanings, and exact `EntryID:` browser searches.
The same file accompanies the built package and is available as a
[website download](../../docs/assets/decks/merged-notes.tsv).
In Anki Browse, use the `AnkiSearch` values to find the retired notes, then use
**Cards → Toggle Suspend** on their unsuspended cards. Several searches can be
joined with ` OR ` and wrapped in parentheses, followed by ` -is:suspended`.
Suspension preserves those notes' history while removing their duplicate review
tasks. Retain the canonical notes; the package preserves their existing GUIDs.
Review histories from two old notes are not combined automatically.

## Build and validate

Use the Rust CLI:

```sh
cargo run --locked -- vocabulary
cargo run --locked -- vocabulary --check
cargo run --locked -- audit-prompts
cargo run --locked -- anki --no-site-copy
cargo run --locked -- glossary
cargo test --locked --test publishing
```

Outputs go to ignored `dist/anki/` (override with `--output`). Omit `--no-site-copy` to also update `docs/assets/decks/malayalam-moag.apkg`.

`src/vocabulary.rs` validates marked source tables, seven-case paradigms, selected study forms, and catalog identity. `src/anki.rs` validates prompts and media and packages decks using native Rust. The six published fields and their order, model ID `1843859663`, deck keys, template order, GUID algorithm, audio filenames, and embedded font name remain unchanged.

Tests compare every published note's GUID and rendered fields against the migration baseline, inspect the generated SQLite database and archive, and reject ambiguous prompts, invalid metadata, missing media, and changed checksums. The migrated Rust package was also imported and reimported using the official Anki 26.9.3 backend: legacy note IDs, card IDs, review intervals and repetition counts were retained. This one-time migration verification is not a build dependency.

Lesson tables remain the catalog source. `study.json` supplies direction-specific English prompts, accepted alternatives, and answer-only explanations without changing Anki's schema. Explicit `cards:false` entries remain glossary-only. Regenerate the glossary after vocabulary changes; CI checks that both are current.

The reusable unit-test workflow is a prerequisite of deployment. All source and exporter tests run through Cargo; browser redirect tests run through Bun.
