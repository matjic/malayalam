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
