# Anki Vocabulary Deck

<a href="assets/decks/malayalam-moag.apkg" download data-ignore>Download the Anki vocabulary deck</a> and open it in Anki.

One package creates a **Malayalam** parent deck with **25 lesson subdecks**.
It contains 1,090 vocabulary entries and 2,180 cards: Malayalam → English and English → Malayalam.
Recordings appear on the answer side where available; 179 entries are text-only.
All 997 recordings and a Malayalam font are included for offline study.
The [Vocabulary Glossary](vocabulary-glossary.md) also includes additional
reference-only postpositions. Core reference-table pronouns and selected
postpositions are included in the deck; full grammatical paradigms remain in
the lesson reference tables. The deck includes basic counting in Lesson 3,
selected numbers and fractions in Lesson 7, and all seven weekdays in Lesson 23.
Other compound numbers remain available in the glossary for reference.
Repeated meanings share one note, introduced in the earliest selected lesson and
tagged with every contributing lesson. Distinct senses keep separate cards, with
a short context cue on the Malayalam front. For example, ആറ് has separate
number and geography cards. Merged answers retain the source glosses, links,
and recordings from the contributing entries.
English prompts omit Malayalam spelling and synonym hints. Names include their
English spellings, such as “Raman (male name)”.
Spelling variants and related-form explanations appear as lesson notes after
revealing the answer in either direction.
English → Malayalam questions include sense or grammar cues where needed. The
main meaning appears prominently, with usage and grammar cues on smaller lines
below it. Some
broad meanings have several valid answers; these are listed as **Also accept**
after revealing the answer. Count a listed alternative as correct for that prompt.
The alternatives are specific to the card, not interchangeable in every sentence.
A prompt requesting the dictionary/head form does not require the past tense or
plural included as reference information on the answer.

Pronoun labels distinguish informal, neutral, and formal usage.
Familiar forms may express closeness or sound disrespectful depending on the
relationship; see [Lesson 1, §1.6](lesson1.md#section-1-6).

## Start with one lesson

Expand **Malayalam** and select **Lesson 01** to study that chapter.
All lessons are initially available. To study the parent deck cumulatively while
keeping future lessons out of your queue:

1. In desktop Anki, open **Browse** and switch to **Cards** mode.
2. Search `deck:Malayalam -tag:moag::lesson_01 is:new`.
3. Select all results and choose **Cards → Toggle Suspend**.
4. Study **Malayalam** to review the lesson you have started.
5. When ready for Lesson 2, search `tag:moag::lesson_02 is:suspended`, select all, and choose **Toggle Suspend** again. Repeat for later lessons.

Suspending cards preserves progress. Set your daily new-card limit to control the
pace; the two directions count as separate cards. You can always select a lesson
subdeck to study only that chapter.

## Updates and sources

Download the latest package and open it in Anki again to get corrections and new
cards. Reimporting preserves existing review progress and does not duplicate
notes. Leave **Import any learning progress** unchecked. Updates may overwrite
your edits to vocabulary fields; cards removed from the package are not deleted
from your collection automatically.

### Clean up duplicates from an older package

The catalog consolidation removes 58 redundant notes (116 cards) from fresh
imports. If you already imported an older deck, import the new package first,
then suspend the retired notes in your collection:

1. Download the <a href="assets/decks/merged-notes.tsv" download data-ignore>retired-note merge map</a>. It lists each old EntryID, its surviving EntryID, and an `AnkiSearch` value.
2. In Anki **Browse**, switch to **Cards** mode. Paste an `AnkiSearch` value such as `EntryID:moag-06-2179e7162c7aaff6`, followed by ` -is:suspended`.
3. Select the matching cards and choose **Cards → Toggle Suspend**. Repeat for the other retired IDs. You can combine searches as `(EntryID:old-id OR EntryID:another-old-id) -is:suspended`.

This preserves the retired notes' review history while removing duplicate review
tasks. Keep the surviving notes active. Anki does not automatically combine two
notes' review histories; reimporting alone does not remove the retired notes.

### Source maintenance

For deck maintainers: the entry IDs in `data/vocabulary/moag.json` are persistent.
The catalog builder preserves them across spelling or meaning corrections.
Merged entries retain their original identities and source rows in `occurrences`;
`data/vocabulary/duplicates.json` records the reviewed grouping decisions.
If changing both the Malayalam and English text, update the corresponding
catalog entry's text while keeping its ID before rebuilding. Keep the Anki model
ID, field order, and card template order stable across releases.
The deck is generated from the lesson vocabulary tables, including explicitly selected reference tables and the additional
recorded forms. Entries without audio remain available as text cards.
The lesson pages retain source credits and recording reuse terms.
