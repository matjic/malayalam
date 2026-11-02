# Published compatibility baselines

`published-notes.json` records each published study note's EntryID, Anki GUID and SHA-256 of its six rendered fields joined by U+001F, captured before replacing the exporter. It covers all 1,085 notes, including reference-table additions and answer-only explanations. Tests also inspect the native SQLite package and embedded media.

`writing-movements.json` preserves the published 93-symbol coverage and movement counts, independently of editable geometry and the Rust renderer.

Intentional editorial changes may update field hashes after review. Preserve EntryIDs and GUIDs when correcting an existing note. Changes to writing coverage or source/editorial movement counts require comparison with the cited textbook pages.

The November 2026 revision audit retained this 1,085-note baseline while adding
63 source-backed study notes. The compatibility test requires every baseline
note to remain present. Only the field hash for `moag-06-a13116e0692e63f0` was
updated: its recall cue now specifies the back/outer-surface sense of പുറത്ത്,
with an answer note connecting Appendix D to Lesson 9's existing elephant-back
caption and distinguishing Appendix E's “outside” sense. Its GUID is unchanged.

The subsequent catalog consolidation retains all 1,085 baseline IDs, either as
surviving notes or as original source occurrences. Retired baseline records have
an explicit `merged_into` successor and retain their historical field hash and
GUID. Surviving notes have reviewed updated field hashes for merged recordings,
source links, combined meanings, earlier lesson placement, and sense cues. The
test checks every retired record's membership in its successor and the GUID of
every surviving record; package checks verify the new note count and all media.
