# Moag recording audit and provisional cue map

The cue table below records the initial scan. Playback now uses a subsequent [announcement and pause recheck](section-boundaries.json) with Whisper large-v3-turbo and independent Whisper small comparisons. The [clip manifest](../../../docs/assets/audio/moag/sections.json) contains the current cut ranges; use those ranges instead of this first-pass table for playback.

The 25 recordings are usable course companions: all decode successfully and match their import checksums. An automatic recognition scan of every full track found lesson-related English announcements, repeated vocabulary, readings or dialogues, and oral practice. They should be linked by topic rather than assumed to match the current printed exercise numbers. This is an ASR-assisted structural audit, not a human listening or pronunciation assessment.

## Checks and limits

- All 25 MP3s decoded completely with FFmpeg without reported errors. All SHA-256 checksums match the import manifest.
- Total duration is 625 minutes, about 10 hours 25 minutes. All tracks are mono, 22,050 Hz. Technical decoding does not establish clear speech or absence of audible defects.
- Local Whisper small scanned the full recordings for English section announcements. Selected instruction clips were recognized independently. The Malayalam renderings and invented translations were discarded as teaching evidence.
- The scan supports lesson association and reveals slower/normal readings, pause-and-respond drills, role practice and selected spoken feedback. It does not establish that every sentence or exercise matches the fourth edition.
- ASR timestamps are candidates. For tracks 10–25 they identify 30-second windows; earlier timestamps are also estimates. Do not automatically synchronize text to these locations.
- The import metadata identifies 1985; this is metadata, not an independently verified recording date or edition. Audio reuse permission remains unverified in the inventory.

The [structured audit](audit.json) preserves integrity checks, recognition cues, confidence information, short recheck transcripts and textbook references. The original recordings and import manifest were not changed.

## What this changes for supplement planning

There is already recorded teaching support to organize. Prioritize finding the correct section and supplying clear learner instructions before recording replacement vocabulary or dialogue audio. Slower and normal versions and selected recorded responses can support independent study, but they do not constitute a complete answer key.

Some tasks still depend on teacher-checked preparation. For example, Lesson 5 asks learners to use answers prepared at home and validated in class; Lesson 25 asks them to prepare comprehension responses. The next alignment pass should say which activities give a spoken answer, which only model a response, and which require outside feedback.

The Lesson 14 recording includes plural practice with spoken comparison and readings. That reduces the feedback gap for its plural task; it does not establish dedicated production practice for every conditional or relative-clause objective. The planned Lesson 14 supplement should remain targeted.

Dedicated pronunciation-discrimination work and minilesson coverage remain unmapped. Failure to recover a title in English recognition is not proof that the activity is absent.

## Track cue map

Locations below are provisional entry points for checking, not validated chapter boundaries. “Not located” means the recognition scan did not reliably recover an announcement. A reading or dialogue can still be present without a recovered title. All times are minutes and seconds.

| Track | Duration | Vocabulary cue | Reading practice cue | Conversation or text cue | Exercise cue |
| --- | --- | --- | --- | --- | --- |
| [Lesson 1](lesson_01.mp3) | 14:16 | ≈00:35 | Not located | ≈08:49 | ≈05:05 |
| [Lesson 2](lesson_02.mp3) | 27:39 | Not located | ≈04:04 | ≈17:30 | ≈07:23 |
| [Lesson 3](lesson_03.mp3) | 28:59 | ≈00:30 | ≈07:29 | ≈24:57 | ≈02:44 |
| [Lesson 4](lesson_04.mp3) | 25:56 | ≈00:51 | Not located | ≈14:06 | ≈04:59 |
| [Lesson 5](lesson_05.mp3) | 23:34 | ≈00:06 | ≈01:57 | ≈14:22 | ≈03:56 |
| [Lesson 6](lesson_06.mp3) | 29:59 | ≈02:21 | Not located | ≈21:21 | ≈05:36 |
| [Lesson 7](lesson_07.mp3) | 28:11 | ≈05:22 | ≈07:03 | ≈21:31 | ≈09:10 |
| [Lesson 8](lesson_08.mp3) | 28:15 | ≈02:18 | Not located | ≈23:24 | ≈04:12 |
| [Lesson 9](lesson_09.mp3) | 32:51 | ≈01:52 | ≈03:49 | ≈24:17 | ≈07:55 |
| [Lesson 10](lesson_10.mp3) | 29:10 | 00:00–00:30 | 02:00–02:30 | 05:30–06:00 | 11:30–12:00 |
| [Lesson 11](lesson_11.mp3) | 17:19 | 01:30–02:00 | 04:30–05:00 | 06:30–07:00 | 11:00–11:30 |
| [Lesson 12](lesson_12.mp3) | 21:02 | 03:30–04:00 | Not located | Not located | 14:00–14:30 |
| [Lesson 13](lesson_13.mp3) | 17:25 | 00:00–00:30 | 04:00–04:30 | 06:30–07:00 | Not located |
| [Lesson 14](lesson_14.mp3) | 15:08 | 02:30–03:00 | Not located | 07:00–07:30 | 09:00–09:30 |
| [Lesson 15](lesson_15.mp3) | 21:31 | 00:30–01:00 | 04:30–05:00 | 06:30–07:00 | 11:30–12:00 |
| [Lesson 16](lesson_16.mp3) | 19:31 | 00:00–00:30 | 03:30–04:00 | 05:30–06:00 | 11:00–11:30 |
| [Lesson 17](lesson_17.mp3) | 24:02 | 00:00–00:30 | 03:30–04:00 | 05:00–05:30 | Not located |
| [Lesson 18](lesson_18.mp3) | 16:06 | 00:00–00:30 | 02:30–03:00 | 04:00–04:30 | 07:30–08:00 |
| [Lesson 19](lesson_19.mp3) | 29:52 | 00:00–00:30 | 04:00–04:30 | 06:00–06:30 | Not located |
| [Lesson 20](lesson_20.mp3) | 19:25 | 01:30–02:00 | 07:00–07:30 | 09:00–09:30 | 12:00–12:30 |
| [Lesson 21](lesson_21.mp3) | 22:18 | Not located | Not located | 07:30–08:00 | 19:00–19:30 |
| [Lesson 22](lesson_22.mp3) | 23:51 | 00:00–00:30 | 07:00–07:30 | 08:30–09:00 | 12:00–12:30 |
| [Lesson 23](lesson_23.mp3) | 34:37 | 03:00–03:30 | 08:30–09:00 | Not located | 25:00–25:30 |
| [Lesson 24](lesson_24.mp3) | 39:31 | 03:30–04:00 | 12:00–12:30 | 15:30–16:00 | 21:00–21:30 |
| [Lesson 25](lesson_25.mp3) | 34:20 | Not located | 10:30–11:00 | 12:00–12:30 | 14:30–15:00 |

## Specific differences and dependencies

These findings compare recognized English instructions with the current lesson tasks. They are stronger evidence for task ordering than the unreliable Malayalam recognition. The Lesson 1 ending is explicitly a candidate requiring fluent review. Clip start times are nearby checking points, not exact word onsets.

| Track and nearby time | Observation | Current text |
| --- | --- | --- |
| Lesson 1 ≈06:40 | The audio labels a joining drill Exercise 6 and its instructions/models indicate affirmative copula joining. Current Exercise 6 asks for joining the question form; affirmative joining appears in the reading practice. Recognition of Malayalam endings remains uncertain. | [lesson1](../../../docs/lesson1.md#lesson1-reading-practice), [lesson1](../../../docs/lesson1.md#lesson1-exercises) |
| Lesson 2 ≈03:55 | The recording explicitly describes this as similar to Reading Practice A but not directly parallel. | [lesson2](../../../docs/lesson2.md#lesson2-reading-practice) |
| Lesson 2 ≈15:10 | The recording calls the additive-ending exercise Exercise 6; current text places that activity in Exercise 7A. | [lesson2](../../../docs/lesson2.md#lesson2-exercises) |
| Lesson 5 ≈11:45 | The recording asks for answers prepared at home and validated in class before using its questions. This section is not a standalone spoken answer key. | [lesson5](../../../docs/lesson5.md#lesson5-exercises) |
| Lesson 6 ≈04:10 | The recording says the order differs from the printed text. | [lesson6](../../../docs/lesson6.md#lesson6-exercises) |
| Lesson 6 ≈05:35 | The recording says the exercise has been altered for oral work. | [lesson6](../../../docs/lesson6.md#lesson6-exercises) |
| Lesson 7 ≈09:05 | Audio Exercise 1 asks learners to change verbs to let us forms. The current text places that transformation in Exercise 9; its Exercise 1 is number practice. | [lesson7](../../../docs/lesson7.md#lesson7-exercises) |
| Lesson 9 ≈09:40 | The recording says Exercise 1B was moved to the Lesson 7 tape, and that its Exercise 2 diverges from the printed form. | [lesson9](../../../docs/lesson9.md#lesson9-exercises), [lesson7](../../../docs/lesson7.md#lesson7-exercises) |
| Lesson 11 ≈16:40 | The closing announcement gives models for Exercise 4 and says time does not permit inclusion of the exercises on the tape. | [lesson11](../../../docs/lesson11.md#lesson11-exercises) |
| Lesson 22 ≈17:20 | The recording explicitly says Exercise 3 is modified from the book for oral practice. | [lesson22](../../../docs/lesson22.md#lesson22-exercises) |
| Lesson 25 ≈14:30 | The recording asks learners to prepare answers before responding orally to questions about the text. | [lesson25](../../../docs/lesson25.md#lesson25-exercises) |

## Lesson 1 as a first alignment candidate

Lesson 1 has a particularly useful structure for the first self-study pilot. The following locations came from recognition, so check a few seconds around each point before creating clips.

| Approximate point | Candidate activity |
| --- | --- |
| 00:08 | Classroom expressions |
| 00:35 | Vocabulary repetition |
| 06:46 | Copula-joining drill labeled Exercise 6; check the form mismatch before linking it |
| 08:49 | Conversation repetition instructions |
| 11:47 | Slower conversation |
| 12:14 | Normal-speed conversation |
| 12:41 | Conversational role practice |
| 13:21 | Switching the learner role |

The current [Lesson 1 conversation](../../../docs/lesson1.md#lesson1-conversation) provides the corresponding situation and characters. Sentence-level equality has not been established. The sound-discrimination task in the current Exercise 7 is not mapped by this audit.

## Remaining alignment work

For each activity that will be assigned, verify the Malayalam speech against the current text with a fluent reviewer, mark precise start and end times, identify omissions or alternate wording, and distinguish spoken answer feedback from teacher-dependent work. Keep the original recording unchanged and attach an alignment record to the selected activity. Only then use the record for automatic text highlighting or precise exercise playback.

See the updated [coverage map](../../../data/curriculum/MOAG-COVERAGE.md) and [supplement backlog](../../../data/curriculum/MOAG-GAPS.md) for how this existing audio support changes the next work.
