# Published compatibility baselines

`published-notes.json` records each published study note's EntryID, Anki GUID and SHA-256 of its six rendered fields joined by U+001F, captured before replacing the exporter. It covers all 1,085 notes, including reference-table additions and answer-only explanations. Tests also inspect the native SQLite package and embedded media.

`writing-movements.json` preserves the published 93-symbol coverage and movement counts, independently of editable geometry and the Rust renderer.

Intentional editorial changes may update field hashes after review. Preserve EntryIDs and GUIDs when correcting an existing note. Changes to writing coverage or source/editorial movement counts require comparison with the cited textbook pages.
