# Moag companion audio

Imported from the user-provided `/Users/mathewjacob/Downloads/malayalam.zip` on 2026-10-02. Embedded MP3 tags identify Rodney Moag and the album *Malayalam: A University Course and Reference Grammar* (1985).

Contains `lesson_01.mp3` through `lesson_25.mp3`, approximately 625 minutes (10 hours 25 minutes). Original filenames retained. macOS metadata files were excluded. ZIP entries passed CRC checking during extraction; all 25 MP3 files were readable by `ffprobe`. A full-file automatic recognition scan has now compared English section announcements and task descriptions with the current lessons; exact Malayalam text alignment remains unverified. See the [recording audit and provisional cue map](AUDIO-AUDIT.md).

`manifest.json` records track checksums, sizes, durations, codecs, and embedded metadata. Original ZIP remains in Downloads. Reuse license not verified.

## Reviewed publishing pipeline

`data/audio/build.json` is the editable cut and panel recipe for the 997 vocabulary clips, 149 section clips and 51 letter clips. `reviewed-vocabulary.json` binds source checksums, printed rows, explicit label reviews and reference-list placement. These decisions were migrated from the completed recognition/listening workflow; publishing no longer recomputes labels using recognizer heuristics.

```sh
cargo run --locked -- word-audio --check
cargo run --locked -- audio --check
cargo run --locked -- letter-audio --check
cargo run --locked -- review-audio
```

Omit `--check` to rebuild missing clips and generated players. FFmpeg handles accurate word/letter cuts and frame-preserving section cuts. Source hashes, clip hashes, repaired audio and exact row alternatives are checked. Missing recordings remain absent; unverified clips stay in explicitly unconfirmed rows. User listening decisions remain bound to the corresponding cuts and transcript.

The generated word manifest and `vocabulary-transcripts.csv` retain spelling, meaning, provenance, source times, recognition evidence and status. Original recordings remain unchanged. When intentionally changing a cut, update its recipe and approved review evidence together, rebuild, listen, then review the generated checksum change. A fresh ASR result never updates these decisions automatically.

## Optional recognition and review

Rust can create new evidence using native [whisper.cpp](https://github.com/ggml-org/whisper.cpp), with FFmpeg decoding input to 16 kHz mono PCM:

```sh
cargo run --locked -- transcribe --input data/audio/moag/lesson_01.mp3 --model /path/to/ggml-large-v3.bin --output dist/lesson-01-recognition.json
```

`--engine` selects the `whisper-cli` executable and `--language` defaults to Malayalam. Source/model SHA-256 values, raw detailed JSON and an unreviewed status accompany the result. No model is downloaded implicitly. Reviewed publishing uses the saved explicit decisions, independently of the recognition tool.

`cargo test --locked --test publishing` covers displaced neighboring labels, separate tomorrow/examination controls, unverified placement, source table contracts and stable note identity. These checks do not replace fluent listening review.

## Historical evidence retained

The repository retains the full Whisper recognition, isolated rechecks, Koyal timestamps and comparisons, boundary probes, listening exports, contextual judgments, noise exclusions and explicit cut/label repairs. The older Koyal/NeMo/Core ML conversion and trial scripts were one-time experimental tooling and have been removed. Their model-specific environments are no longer required for publishing. Native Whisper is the supported path for new recognition; existing Koyal outputs remain evidence and are not asserted to be reproducible using a different model.

The original review queue contained 142 uncertain assignments; subsequent contextual work and listening corrections resolved or explicitly placed them. Historical counts in audit JSON/CSV refer to those earlier inventories. The current generated manifests are authoritative for clip inventory, while original recordings and lesson text remain authoritative for source content. Agreement between recognizers is not an accuracy estimate.
