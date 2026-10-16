# Moag companion audio

Imported from the user-provided `/Users/mathewjacob/Downloads/malayalam.zip` on 2026-10-02. Embedded MP3 tags identify Rodney Moag and the album *Malayalam: A University Course and Reference Grammar* (1985).

Contains `lesson_01.mp3` through `lesson_25.mp3`, approximately 625 minutes (10 hours 25 minutes). Original filenames retained. macOS metadata files were excluded. ZIP entries passed CRC checking during extraction; all 25 MP3 files were readable by `ffprobe`. A full-file automatic recognition scan has now compared English section announcements and task descriptions with the current lessons; exact Malayalam text alignment remains unverified. See the [recording audit and provisional cue map](AUDIO-AUDIT.md).

`manifest.json` records track checksums, sizes, durations, codecs, and embedded metadata. Original ZIP remains in Downloads. Reuse license not verified.

## Individual vocabulary words

Lessons 1–25 now offer word clips as well as continuous vocabulary playback. The new transcription pass uses full **Whisper large-v3**, including independent English-announcement recognition, Malayalam word timestamps, and isolated rechecks. The turbo model is not used for these word transcriptions. Pause detection and acoustic comparison of repeated utterances propose the cuts; these are automatic alignments, not fluent listening verification.

[`vocabulary-transcripts.csv`](vocabulary-transcripts.csv) contains the written forms, meanings, clip paths, source times, and review status. Every printed vocabulary entry remains represented, including entries without an audio match. `matched` means an automatic spelling/phonetic match; it does not mean human verification. `review` identifies uncertain labels, and `untranscribed` explicitly identifies a word still needing transcription. `not_aligned` means a printed entry has no assigned clip; it is not proof that the word is absent from the recording. Uncertain players are marked “check match” in the lessons.

The generated [word manifest](../../../docs/assets/audio/moag/words/manifest.json), `vocabulary-recognition/`, `vocabulary-alignment/`, and `vocabulary-rechecks/` preserve the evidence. Original MP3s remain unchanged. Word clips are re-encoded to cut accurately at short utterance boundaries; the two recorded readings of an item are normally retained together. `vocabulary-ranges.json` also corrects the continuous vocabulary players, including the previously unlocated sections in Lessons 2, 21, and 25.

Word and letter controls are embedded in their tables. Only exact written forms and listed variants are attached to named rows. Uncertain recordings stay in table rows explicitly labeled “Unconfirmed” and “check match”; a missing-row dash means no confident assignment. User confirmations are recorded in `vocabulary-reviews.json` and bound to the clip's source times and displayed transcription.

The [label audit](vocabulary-label-audit.csv) checks all 1,005 published clips. It found a bug where substring matching across broad English transcript segments let neighboring words overwrite clip labels. That override was removed; English support now requires substantial temporal overlap and compares complete phrases. The audit changed 142 proposed labels. It leaves 142 recordings unconfirmed (137 provisional transcriptions and five untranscribed), including duplicate candidates, rather than attaching them to named rows as settled matches. The [structured report](vocabulary-label-audit.json) preserves before/after labels and review counts. Audio bytes were unchanged. `python3 scripts/test_audio_row_alignment.py` covers the tomorrow/examination regression, other displaced labels, and safe placement of uncertain clips; this does not substitute for fluent listening review.

To rebuild existing results, run `python3 scripts/build-vocabulary-audio.py`, then `python3 scripts/integrate-moag-audio.py`. Pass `--check` to each command to verify generated output and checksums without changing it. Fresh recognition requires an Apple Silicon MLX environment with `mlx-whisper`, `numpy`, and `scipy`, and the full `mlx-community/whisper-large-v3-mlx` checkpoint: run `scripts/locate-vocabulary-audio.py --model MODEL_DIRECTORY`, `scripts/transcribe-vocabulary-audio.py --model MODEL_DIRECTORY`, `scripts/align-vocabulary-audio.py`, then `scripts/recheck-vocabulary-audio.py --model MODEL_DIRECTORY` with that environment's Python. Recognition and rechecks resume from saved results.

## Listening review and contextual follow-up

The user completed all 142 entries in the temporary review page. Their unmodified export is preserved in [`vocabulary-review-export.json`](vocabulary-review-export.json). The preliminary `vocabulary-review-analysis.*` files counted decisions and notes only; their “ready to apply” assessment is superseded by the contextual audit.

[`vocabulary-review-context.csv`](vocabulary-review-context.csv) records the contextual review of all 142 entries, including the preceding/following clips, original lesson vocabulary/text, saved Malayalam recognition, isolated rechecks, and English recognition. [`vocabulary-context-audit.csv`](vocabulary-context-audit.csv) and its detailed JSON cover the ordered sequence screen of all 1,005 published clips. There are 68 specific findings: 32 within the exported review queue and 36 among the other automatically matched clips. Some findings support a proposed resolution; others require boundary, spelling, or listening checks. The 825 automatic assignments without a specific finding remain unverified, and the two earlier user reviews are recorded separately.

The contextual review identifies probable neighboring-label substitutions, crossed repetition boundaries, and an English “Part Two” announcement apparently mistaken for a Malayalam word. It also preserves conflicts with user confirmations and uncertainty notes. None of these findings establishes that an auditor heard the audio. Production labels and cuts have not been changed by this audit. Rebuild the evidence reports with `python3 scripts/audit-vocabulary-context.py`; the per-clip contextual judgments are retained in `vocabulary-context-findings.json`.

## Completed Koyal comparison and vocabulary targets

Koyal was run locally on all 1,005 existing word clips, with 68 longer excerpts around contextual findings. Raw output, source/model checksums and inference times are saved in `koyal-vocabulary.json` and `koyal-vocabulary-context.json`. These files preserve recognizer output; they do not update lesson labels. Re-run with:

```sh
/private/tmp/koyal-env/bin/python scripts/transcribe-koyal-vocabulary.py \
  --model /private/tmp/koyal-ml-120m-1.0/koyal-ml-120m-1.0.nemo
python3 scripts/compare-koyal-vocabulary.py
python3 scripts/audit-koyal-timestamps.py
```

The transcription command resumes matching cached clips/excerpts by content hash. `koyal-comparison.json`/`.csv` compare the user export, available Whisper evidence, Koyal and the saved 16-clip BuzzASR trial. Normalization ignores punctuation/spacing and exact whole-output repetitions, while preserving different endings and extra speech. Koyal agrees with 99 of 121 nonflagged user references; the 22 disagreements are individually interpreted in `koyal-assessment.json`. On the same small selected 16-clip sample, Koyal agrees with 13 user labels and BuzzASR with 5. These are agreement counts, not accuracy estimates; some references are themselves uncertain or contradicted by context. The 160 disagreements with other automatically assigned labels are not 160 proven errors. `koyal-followup.csv` is a diagnostic queue, not a demand that every model mismatch be manually accepted.

All 25 lessons now have original-track Koyal timestamps, totaling 2,296 recognized words. `koyal-cutoff-audit.json`/`.csv` join those approximate times to all 1,005 existing clips. The 22 crossing-boundary diagnostics often reflect merged ASR words; they are not certified bad cuts. In particular, source-time recognition can merge neighboring words or omit speech that isolated recognition recovers.

**The printed vocabulary is the target.** `koyal-cut-proposals.json` retains all 941 original vocabulary rows and meanings, allowing source-listed variants and optional full phrases. It locates candidate spans for 761 rows by exact contiguous source-word matching; the other 180 remain unresolved. No fuzzy neighbor substitution is used. Candidate padding is constrained by neighboring recognized words, but waveform/listening refinement is still required. Multiple occurrences, single readings and chunk-edge words remain flagged. Nothing in this trial changes production audio cuts, textbook wording, meanings or table assignments. Apparent textbook errors must be checked separately against the source edition and language evidence, rather than inferred solely from ASR disagreement.

## Koyal word timestamps for cutoff review

Run `scripts/timestamp-koyal.py` in a NeMo ASR Python environment with `torch`,
`numpy`, and `ffmpeg` available. For the existing local setup:

```sh
NUMBA_CACHE_DIR=/private/tmp/koyal-numba /private/tmp/koyal-env/bin/python scripts/timestamp-koyal.py \
  --model /private/tmp/koyal-ml-120m-1.0/koyal-ml-120m-1.0.nemo \
  --lessons 3
```

Omit `--lessons` to process all 25 lessons. Output defaults to
`data/audio/moag/koyal-timestamps/lesson_NN.json` and `.csv`; use `--output-dir`
to change it. Add `--captions` for optional word-level SRT/VTT files.
Existing outputs for selected lessons are overwritten.

The script reads original lesson recordings using `vocabulary-ranges.json`,
with one second of extra context on each side (`--context`). It splits into
chunks of at most 25 seconds near low-energy windows, keeping all audio.
JSON retains raw chunk text and raw word timestamps alongside a flattened
word list. `start`/`end` are seconds in the **original lesson MP3**;
`section_start`/`section_end` are relative to the extracted transcription
range, including context. Caption times also refer to the original MP3.

For another agent: preserve repetitions, inspect `near_chunk_edge` words,
and compare word times with existing clip boundaries in the word manifest.
TDT timestamps estimate speech positions; refine cuts using the waveform,
nearby silence, and padding. These are unverified ASR outputs, and English
announcements may be misrecognized. No production cuts or labels change.
Lesson 3 produced 85 timestamped words in the initial test. The completed all-lesson run is described above.

## Koyal Core ML export

The unofficial conversion is published at
<https://huggingface.co/matjacob/koyal-ml-120m-1.0-coreml>, with Adalat AI credited,
the original Koyal model linked as `base_model`, and CC-BY-4.0 retained. The
release contains the three Core ML packages, tokenizer, scripts, and validation
evidence. It is a format conversion with no additional training. No preexisting
published conversion was found before this export. Apple's supported PyTorch
conversion route avoids an ONNX intermediate:
<https://apple.github.io/coremltools/docs-guides/source/convert-pytorch-workflow.html>.

`scripts/export-koyal-coreml.py` exports the encoder, stateful prediction network,
and TDT joint network as separate `.mlpackage` files. It also exports the
SentencePiece tokenizer, vocabulary, model settings, TorchScript traces, and
PyTorch test vectors. Use the existing NeMo environment with `coremltools==9.0`:

```sh
NUMBA_CACHE_DIR=/private/tmp/koyal-numba /private/tmp/koyal-env/bin/python scripts/export-koyal-coreml.py \
  --model /private/tmp/koyal-ml-120m-1.0/koyal-ml-120m-1.0.nemo \
  --output-dir /private/tmp/koyal-coreml --frames 512
/private/tmp/koyal-env/bin/python scripts/validate-koyal-coreml.py /private/tmp/koyal-coreml
NUMBA_CACHE_DIR=/private/tmp/koyal-numba /private/tmp/koyal-env/bin/python scripts/transcribe-koyal-coreml.py \
  --models /private/tmp/koyal-coreml \
  --audio docs/assets/audio/moag/words/lesson_03_word_001.mp3 \
  --compare-nemo /private/tmp/koyal-ml-120m-1.0/koyal-ml-120m-1.0.nemo \
  --output /private/tmp/koyal-coreml/transcription-check.json
```

Validated locally: FP32 components at 512 padded mel frames, Core ML CPU_ONLY,
with maximum absolute component differences below 0.00002 on saved test
vectors. Three real clips produced identical transcripts to NeMo. See
[`koyal-coreml-trial.json`](koyal-coreml-trial.json). Model packages total about
449 MiB and currently live in `/private/tmp/koyal-coreml`; they are not in the
repository; they can also be downloaded from the Hugging Face release above.
The default deployment target is macOS 14 / iOS 17 generation.

The reference inference script uses Core ML for the neural networks and
NeMo/PyTorch for matching audio preprocessing. It emits text and subword token
positions; token durations are TDT frame skips, not verified phonetic lengths.
It accepts short clips that fit the exported frame count (512 frames is about
5.1 seconds); longer recordings need chunking or a larger fixed-frame export.
The exporter defaults to 1024 frames; only 512 has been validated here.
FP16 (`--fp16`) is now published in the release's `fp16/` directory, about
225 MiB for the model packages, with the original FP32 packages retained at
the repository root. Select it with `--models /path/to/download/fp16` in the
reference transcriber. `--compute-units cpu_and_ne` permits Neural Engine
execution with CPU fallback; `all` also permits GPU execution.

[`koyal-coreml-fp16-trial.json`](koyal-coreml-fp16-trial.json) records the broader
comparison: FP32 matched original NeMo on 15/15 clips; FP16 CPU matched FP32
on 15/15; FP16 CPU_AND_NE matched exactly on 14/15, with the remaining result
differing only in spacing (`കൈകൂപ്പി` versus `കൈ കൂപ്പി`). CPU token start
times shifted by up to 0.08 seconds. The FP16 encoder exceeds the strict
elementwise numerical tolerance (`rtol=0.005, atol=0.005`), and that failure
is preserved in its manifest and validation report. The numerical validator
saves every component's results before returning a nonzero status on failure.
This is small-sample transcript validation, not full numerical equivalence.

Actual Neural Engine operation placement, iPhone performance, and a Swift
application remain untested. A native application must implement matching mel extraction,
normalization, padding, SentencePiece decoding, and the TDT duration/blank loop.
The reference script contains that loop and preserves predictor state only
when a nonblank token is emitted. Original model attribution is Adalat AI,
under CC-BY-4.0: <https://huggingface.co/adalat-ai/koyal-ml-120m-1.0>.

## Core ML boundary experiment

`probe-koyal-boundaries.py` tests 123 crop variations around nine identified problem cases, using original printed forms as targets. The reusable `koyal_coreml.py` runtime caches the unchanged predictor result across blank emissions. Four warmed short-clip observations produced identical Core ML and NeMo transcripts; CPU Core ML took 0.056–0.059 seconds per clip versus NeMo's 0.186–0.201 seconds. Both paths include mel preprocessing, and NeMo includes its transcription loader overhead; model loading and ffmpeg decoding are excluded. This small comparison does not establish Neural Engine or iOS performance.

Six experimental cuts preserve two exact readings across multiple start/end variations and have quiet first/last 60 ms windows (RMS below -35 dB). Three cases remain unresolved: two fail the quiet-edge criterion in noisy audio, and one has recognizer disagreement with the printed form. Quiet edges and stable recognition are supporting evidence, not listening verification. The 512-frame export limits these trials to short excerpts; long phrases must not be truncated to fit it.

Raw crops, timings, printed source entries and selection evidence are saved in `koyal-coreml-boundary-trial.json`/`.csv`. Experimental MP3s are under `docs/assets/audio/moag/boundary-trial/`; the temporary comparison page is `docs/audio-boundary-review.html`. Run `python3 scripts/build-boundary-preview.py` to regenerate that page. All six encoded MP3s were independently decoded and passed through the original Core ML reference script and NeMo; both agreed with each other and the pre-encoding crop transcripts. Results are in `koyal-coreml-boundary-preview-check.json`. Browser checks verified all six players and exclusive playback. All 1,005 production clip checksums remain unchanged, and no textbook wording or production assignments were modified.

## Applied boundary and table repairs

The user approved the six experimental cuts for Lesson 21 തരുക / പറഞ്ഞുതരുക and Lesson 24 സ്നേഹം / തമ്മിൽ / ഗുണം / കുറവ്. Those exact approved MP3 bytes are now used in production. The user also confirmed that the original Lesson 4 അവന് recording sounded correct, that the old പണം clip contained both പണം and ഒന്ന് twice, and that the old ഒന്ന് clip was silence. The അവന് audio bytes are retained and its table assignment corrected; separate two-reading പണം and ഒന്ന് cuts were checked across nine crop variations each and after MP3 encoding with Core ML and NeMo. Both recognize the encoded outputs exactly twice. The two noisy cuts are computer-checked repairs requested by the user, not separately user-approved listening samples.

`vocabulary-cut-repairs.json` anchors all nine repairs to source checksums, exact ranges, original published metadata and printed entries/meanings. Immutable cut copies are in `vocabulary-repaired-clips/`; `audio_repairs.py` applies them during normal regeneration. സ്നേഹം uses its existing noun cell in the Reference List; the other repairs use their original vocabulary rows. No printed vocabulary, meanings or lesson prose changed. The old nine MP3s are preserved under `docs/assets/audio/moag/boundary-trial/before/`, and the comparison page now shows before/after audio. Earlier Koyal/Whisper audit outputs describe the pre-repair snapshot; these explicit repairs and the current word manifest supersede their old ranges and labels for these nine IDs.

## Individual letters

The [alphabet page](../../../docs/alphabet.md#letter-audio) retains the full UT Austin alphabet recitation and ten vowel/consonant row recordings, alongside 51 individual letter clips. The [letter manifest](../../../docs/assets/ut-austin/letters/manifest.json) records source files, symbols, romanization, cut times, and checksums. Run `python3 scripts/build-letter-audio.py` to rebuild, or add `--check` to validate. These excerpts use the already archived UT recordings and source charts; credits and licensing are linked beside the players.

Lessons 1–25 in `docs/` embed section clips in `docs/assets/audio/moag/sections/`. Players stop at the clip end; conversation buttons select separate slower, normal-speed, or role practice clips where cues were recovered. Boundaries were rechecked with local Whisper large-v3-turbo word timestamps, independent Whisper small comparisons, and nearby pauses; they remain machine-aligned rather than fluently reviewed. [section-boundaries.json](section-boundaries.json) records the recheck evidence. MP3 frames are copied without re-encoding. The original tracks remain here. `docs/assets/audio/moag/sections.json` records every clip range and checksum. Run `python3 scripts/integrate-moag-audio.py` to refresh generated audio blocks and clips from `audit.json` and `section-boundaries.json`, or pass `--check` to validate the integration and checksums. The script preserves all lesson content outside its labeled audio blocks.

## Latest lesson/minilesson follow-up

The current follow-up is recorded in `lesson-audit-followup.json`/`.csv`. It supersedes older pre-repair counts: 997 active vocabulary clips remain after removing six user-reported nonword clips, the confirmed “Part Two” announcement, and consolidating one split repetition. Their old artifacts and all original continuous recordings are retained. This pass changed 114 active labels, applied saved listening reviews where an original printed entry fits, and made one additional source-audio cut for അത്ര. All 941 printed vocabulary entries and meanings remain unchanged.

`vocabulary-label-repairs.json` records user reviews and context-backed corrections with exact source/crop checksums. The 49 additional or partial recorded forms have now been added with meanings to the existing lesson vocabulary tables, as requested by the user. Their provenance is `additional_vocabulary` in `vocabulary-label-repairs.json`; original printed rows remain unchanged. Placement flags are cleared. Both listening questions are resolved by the user: Lesson 5 clip 005 is പഠിക്കുന്നു, and Lesson 20 clip 041 is the English “Part Two” announcement, now excluded from vocabulary players. The resolved page with original-track context remains at `docs/audio-audit-remaining.html`. No transcription or placement questions remain from this focused review. This records table organization, not a new listening approval for automatically transcribed clips.

All seven minilesson texts and three added practice lessons were read in this follow-up. A learner note in Minilesson G qualifies the source’s opening generalizations using its own later examples; Minilesson E’s case-rule contradiction and the other source issues listed in `docs/proofreading-review.md` remain unresolved. The review does not certify every phonetic boundary or every line of the source edition.

FP16 Core ML checks used the supplied `cpu_and_ne` setting. The corpus, letter-audio, section-player, writing-symbol, navigation and eight regression checks pass with `/private/tmp/koyal-env/bin/python`. The system Python 3.15 XML extension failed to load in this environment; the supplied Python 3.10 environment passed the same writing-symbol check.
