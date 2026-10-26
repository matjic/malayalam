# Anki Vocabulary Deck

<a href="assets/decks/malayalam-moag.apkg" download data-ignore>Download the Anki vocabulary deck</a> and open it in Anki.

One package creates a **Malayalam** parent deck with **25 lesson subdecks**.
It contains 990 vocabulary entries and 1,980 cards: Malayalam → English and English → Malayalam.
Recordings appear on the answer side where available; 65 entries are text-only.
All 997 recordings and a Malayalam font are included for offline study.
The same vocabulary is available in the [Vocabulary Glossary](vocabulary-glossary.md).
English prompts omit Malayalam spelling and synonym hints. Names include their
English spellings, such as “Raman (male name)”.
Spelling variants and related-form explanations appear as lesson notes after
revealing the answer in either direction.

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

For deck maintainers: the entry IDs in `data/vocabulary/moag.json` are persistent.
The catalog builder preserves them across spelling or meaning corrections.
If changing both the Malayalam and English text, update the corresponding
catalog entry's text while keeping its ID before rebuilding. Keep the Anki model
ID, field order, and card template order stable across releases.
The deck is generated from the lesson vocabulary tables, including the additional
recorded forms. Entries without audio remain available as text cards.
The lesson pages retain source credits and recording reuse terms.
