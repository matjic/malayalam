# Moag learning support gaps and supplement backlog

The first companion work should help learners study the improved Moag course independently: smaller study units, feedback, supported script entry and usable audio. The clearest local practice addition is Lesson 14. These priorities are editorial judgments from the [coverage map](MOAG-COVERAGE.md), not results from learner testing. No supplement has been produced by this audit.

## Audio follow up

The [recording audit](../audio/moag/AUDIO-AUDIT.md) has completed file-integrity checks and a full-file ASR-assisted scan of all 25 tracks. It recovered repetition, slower/normal readings, oral practice and selected spoken responses. This partially addresses G01 and advances G02; it does not complete either. Exact wording, precise timings and per-exercise coverage remain unverified. Some tracks explicitly adapt or reorder exercises, and some require prepared or teacher-validated answers. Before creating replacement audio, map and verify the existing activity.

## What counts as a gap

| Category | Meaning in this audit |
| --- | --- |
| Missing support | A particular companion capability was not identified in the inspected local edition; existing models or teacher support may still cover part of the need |
| Local practice gap | A topic is taught, but its dedicated practice is sparse relative to the objectives |
| Presentation and scaffolding | Material exists, but learners would benefit from a smaller sequence or bridge |
| Unverified asset or access gap | A resource exists, but its relevance or usability has not been established |
| Support for transfer | Controlled practice exists; additional contextual choice or open interaction would extend it |
| Audience or topic extension | Optional material for new purposes or audiences, not a failure of the source course |
| Existing editorial dependency | A source issue already tracked by the transcription review; recheck it there rather than duplicate the repair |

“Not identified” is limited to the reviewed local edition. Practical objectives and prerequisite recommendations are interpretations. The [structured audit](moag-audit.json) preserves evidence links and source hashes.

## Priority order

| Work | Priority | Why |
| --- | --- | --- |
| [Study routes](#g04), [feedback](#g01), and [script entry](#g03) | First | They make the opening lessons more independently usable without inventing another core course |
| [Audio alignment](#g02), then [pronunciation support](#g08) | First | Reuse opportunities must be understood before recording replacement material |
| [Early meaning contrasts](#g05) and [Lesson 14 practice](#g06) | First | They address concrete decisions and a localized practice imbalance |
| [Communicative transfer](#g07), [review checks](#g09), [vocabulary](#g10), [reading bridges](#g11), and [casual listening](#g12) | Later | Build on the feedback and study-route foundation |
| [Audience routes](#g13) and [new communication contexts](#g14) | Optional after the core pilot | They should respond to learner needs rather than expand the project before the basics work |

<a id="g01"></a>
## Independent feedback on exercises

**Reference:** G01. **Category:** Missing support. **Priority:** First. **Scope:** All 25 lessons; minilessons A–F as new practice is added.

**Observed:** Exercise models, translated examples and teacher/partner checking exist. No complete answer key with explanations of acceptable alternatives was identified; the digital guide explicitly says layout adaptation does not supply an answer key.

**Why it matters:** Independent learners cannot reliably distinguish a valid alternative from a mistake, especially in open responses and translation.

**Proposed supplement:** Start with Lesson 1: original checks or companion answers with reasoning, common errors and acceptable variants. Separate fixed answers from sample open responses.

**Completion check:** Each pilot task has a verified model or answer, a short reason, and a clear note where other answers can be valid. Open tasks have a simple self-check rubric.

**Dependencies:** None within this backlog.

**Evidence:** [digital-edition](../../docs/digital-edition.md), [lesson1](../../docs/lesson1.md#lesson1-exercises), [usage](../../docs/usage.md#usage-how-to-use-the-lessons).

<a id="g02"></a>
## Match existing recordings to current lessons

**Reference:** G02. **Category:** Unverified asset and access gap. **Priority:** First. **Scope:** Lessons 1–25; coverage of script and minilessons unknown.

**Observed:** There are 25 lesson-named MP3s. Inventory metadata points to 1985; the text is the fourth edition. No section timestamp map or verified text alignment was identified. The digital edition does not claim a complete linked audio course.

**Why it matters:** A track filename does not tell a learner which current dialogue, word list or exercise it supports.

**Proposed supplement:** Audit one track at a time against the current lesson, recording timestamps, matched sections, wording differences and uncovered sections. Decide on embedding or new recordings after alignment and reuse status are established.

**Completion check:** The pilot lesson has a section-to-timestamp map; unmatched sections are explicit. Audio availability and text alignment remain separate statuses.

**Dependencies:** None within this backlog.

**Evidence:** [README](../../data/audio/moag/README.md), [manifest](../../data/audio/moag/manifest.json), [digital-edition](../../docs/digital-edition.md).

<a id="g03"></a>
## Script practice alongside the first lessons

**Reference:** G03. **Category:** Presentation and scaffolding. **Priority:** First. **Scope:** Alphabet and symbols; Lessons 1–3, then later joining patterns.

**Observed:** The alphabet, reading-pattern exercises and 93 redrawn writing models are present. The usage guide advises learning the script as needed, but no task-sized entry sequence with independent recognition and writing checks was identified.

**Why it matters:** A new learner must choose a manageable set of symbols and connect the models to actual lesson words.

**Proposed supplement:** Create a Lesson 1 script route using a limited symbol set, reading recognition, writing from a model, and reading without the model. Reuse existing diagram capabilities rather than commissioning replacement diagrams.

**Completion check:** Every practice word is glossed; required symbols are named; recognition and writing are checked separately. Learners can use paper, and digital writing is optional.

**Dependencies:** [G04](MOAG-GAPS.md#g04).

**Evidence:** [alphabet](../../docs/alphabet.md), [symbols](../../docs/symbols.md), [writing](../../docs/assets/writing.js), [README](../../README.md), [usage](../../docs/usage.md#usage-how-to-use-the-lessons).

<a id="g04"></a>
## Smaller study units and prerequisites

**Reference:** G04. **Category:** Presentation and scaffolding. **Priority:** First. **Scope:** All lessons; especially 1, 7, 8, 20, 21 and 25.

**Observed:** The book explicitly advises treating each substantial lesson as several sessions and offers both model-led and analytic study. Navigation and prerequisite notes have improved. No explicit per-session objective, practice selection and readiness check was identified.

**Why it matters:** Learners still have to decide what to study today and whether they are ready for the next step.

**Proposed supplement:** Add a small companion route for each pilot lesson: objective, prerequisites, relevant explanation/model, selected practice and a short exit check. Mark reference material separately from first-pass requirements.

**Completion check:** A route states what the learner should do and how to check it. Time estimates are provisional, and it does not require reading every grammar note before speaking.

**Dependencies:** None within this backlog.

**Evidence:** [usage](../../docs/usage.md#usage-how-to-use-the-lessons), [digital-edition](../../docs/digital-edition.md), [lesson7](../../docs/lesson7.md), [lesson21](../../docs/lesson21.md).

<a id="g05"></a>
## Choose forms by meaning and situation

**Reference:** G05. **Category:** Underdeveloped support for transfer. **Priority:** First for early contrasts then Later. **Scope:** Lessons 2–9, 11–13, 15–17, 19–24; minilessons C–F.

**Observed:** The source explains many contrasts and supplies examples and transformations. Form production is often easier to locate than independently checkable decisions about which form fits a new context.

**Why it matters:** Correctly changing an ending does not demonstrate that a learner can choose the expression needed in an interaction.

**Proposed supplement:** Write original short situations with feedback: identity/existence, want/like, intention/future, giving, permission/ability, event sequence and tense/aspect. Use simple diagrams where they clarify case roles or timelines.

**Completion check:** Each contrast is backed by current reviewed explanations and speaker-checked examples. Feedback explains the meaning or context rather than only marking an ending wrong.

**Dependencies:** [G01](MOAG-GAPS.md#g01).

**Evidence:** [lesson3 §3-3](../../docs/lesson3.md#section-3-3), [lesson4 §4-3](../../docs/lesson4.md#section-4-3), [lesson6 §6-3](../../docs/lesson6.md#section-6-3), [lesson7 §7-1](../../docs/lesson7.md#section-7-1), [lesson19 §19-7](../../docs/lesson19.md#section-19-7), [lesson24 §24-6](../../docs/lesson24.md#section-24-6).

<a id="g06"></a>
## Dedicated practice for Lesson 14 structures

**Reference:** G06. **Category:** Local practice gap. **Priority:** First. **Scope:** Lesson 14.

**Observed:** The exercise section contains a newspaper-section response frame, plurals and reading items. Conditionals, either/or and relatives with possession/existence are explained and illustrated, but have little dedicated production practice in that section.

**Why it matters:** The amount of practice does not match the range of new structures introduced.

**Proposed supplement:** Create three small original activities: conditional decisions, alternative choices, and descriptions identifying which person or object is meant. Add supported production after recognition.

**Completion check:** Each of the three objectives has recognition and production practice with feedback. The unclear all/each source prose is not used as an unqualified rule.

**Dependencies:** [G01](MOAG-GAPS.md#g01).

**Evidence:** [lesson14](../../docs/lesson14.md#lesson14-exercises), [lesson14 §14-2](../../docs/lesson14.md#section-14-2), [lesson14 §14-3](../../docs/lesson14.md#section-14-3), [lesson14 §14-4](../../docs/lesson14.md#section-14-4).

<a id="g07"></a>
## Use grammar to complete a communicative task

**Reference:** G07. **Category:** Underdeveloped support for transfer. **Priority:** Later. **Scope:** Selected lessons, especially 11–13 and 15–24; minilesson A.

**Observed:** Classmate responses, introductions, number games, age exchanges, route drawing and itinerary writing already occur. Many later exercises primarily manipulate forms or translate sentences; spontaneous interaction needs teacher adaptation.

**Why it matters:** Learners need a bridge from controlled practice to achieving a purpose with their own information.

**Proposed supplement:** Add one original task where useful: relay a message, resolve a schedule conflict, explain a route, describe an event, or compare options. Supply roles and enough language support for a partner or solo recording.

**Completion check:** The task has a practical outcome, uses supported vocabulary/forms, and includes a simple rubric for meaning and appropriateness. It extends existing interaction rather than claiming the course has none.

**Dependencies:** [G01](MOAG-GAPS.md#g01), [G04](MOAG-GAPS.md#g04).

**Evidence:** [lesson2](../../docs/lesson2.md#lesson2-exercises), [lesson13](../../docs/lesson13.md#lesson13-exercises), [lesson18](../../docs/lesson18.md#lesson18-exercises), [lesson22](../../docs/lesson22.md#lesson22-exercises), [lesson23](../../docs/lesson23.md#lesson23-exercises).

<a id="g08"></a>
## Independent pronunciation practice and feedback

**Reference:** G08. **Category:** Access and feedback gap. **Priority:** First. **Scope:** Alphabet; Lessons 1–12 and 20; minilessons B and G.

**Observed:** Explicit pronunciation work covers dental/alveolar/retroflex contrasts, aspiration, vowel and consonant length, nasals, laterals and rhotics. Several exercises require an instructor to speak or judge. The recordings have not been aligned to these activities.

**Why it matters:** A print description alone cannot establish that a learner hears or produces a contrast.

**Proposed supplement:** After checking existing audio, supply short speaker-verified listening trials and spoken models for selected contrasts. Offer record-and-compare practice and specific partner/teacher feedback prompts.

**Completion check:** Listening trials have validated recordings and answers. Production is not auto-certified without a reliable assessment method; learners receive observable cues and a feedback route.

**Dependencies:** [G02](MOAG-GAPS.md#g02), [G01](MOAG-GAPS.md#g01).

**Evidence:** [lesson1](../../docs/lesson1.md#lesson1-exercises), [lesson8](../../docs/lesson8.md#lesson8-exercises), [lesson11](../../docs/lesson11.md#lesson11-exercises), [lesson12](../../docs/lesson12.md#lesson12-exercises), [lesson20](../../docs/lesson20.md#lesson20-exercises).

<a id="g09"></a>
## Cumulative retrieval and readiness checks

**Reference:** G09. **Category:** Missing explicit learning support. **Priority:** Later. **Scope:** Checkpoints after selected lesson groups; vocabulary across lessons.

**Observed:** The author recommends revisiting reading practice, and exercises reuse earlier forms. No explicit schedule of cumulative checks or learner progress record was identified in the inspected edition.

**Why it matters:** Finishing a page does not show whether previously learned material is still usable.

**Proposed supplement:** Create original mixed review checks with feedback, delayed vocabulary retrieval and clear next-study suggestions. Keep these separate from claims of standardized proficiency levels.

**Completion check:** Checks mix recognition and production from prior lessons, revisit items after a delay, and identify what to review. Thresholds are pilot choices rather than validated proficiency cutoffs.

**Dependencies:** [G01](MOAG-GAPS.md#g01), [G04](MOAG-GAPS.md#g04).

**Evidence:** [usage](../../docs/usage.md#usage-how-to-use-the-lessons), [digital-edition](../../docs/digital-edition.md), [lesson8](../../docs/lesson8.md#lesson8-exercises).

<a id="g10"></a>
## Vocabulary support by task and direction

**Reference:** G10. **Category:** Coverage and retrieval support. **Priority:** Later. **Scope:** All lessons, reference lists and minilesson B.

**Observed:** Bilingual vocabulary and a Malayalam-to-English glossary exist. The author says extra grammar-example and reference vocabulary is not comprehensively included; current notes already gloss several confirmed early items. Search by English works, but that is not a curated reverse course vocabulary index.

**Why it matters:** Learners may find a meaning without knowing which equivalent is appropriate or where it was practiced.

**Proposed supplement:** Maintain a curated course vocabulary record linking senses, supporting examples, relevant lesson and optional audio. Add English-side task lookup and short retrieval sets. Use Olam only where a specific gap exists and retain applicable attribution/license provenance.

**Completion check:** New items have a checked sense, context and provenance; introduction status distinguishes a glossed chunk from a fully taught form. Raw glossary lesson numbers are not treated as first-use proof.

**Dependencies:** [G04](MOAG-GAPS.md#g04).

**Evidence:** [usage](../../docs/usage.md#usage-as-a-reference-grammar), [glossary](../../docs/glossary.md), [proofreading-review](../../docs/proofreading-review.md), [minilesson-b](../../docs/minilesson-b.md), [README](../../data/olam/README.md).

<a id="g11"></a>
## Supported reading between dialogues and formal prose

**Reference:** G11. **Category:** Presentation and extension. **Priority:** Later. **Scope:** Lessons 10, 16, 20 and 25; optional additions elsewhere.

**Observed:** The course already contains formal geographical, newspaper and cultural prose, advertisements and comprehension work. It does not lack reading material. A separate ladder of short original passages with bounded vocabulary and independent feedback was not identified.

**Why it matters:** Some learners would benefit from smaller passages before tackling the longer formal texts.

**Proposed supplement:** Write original short passages on familiar topics, with selective glosses, a few comprehension checks and a summary task. Link each to existing grammar and show spoken/formal alternatives when appropriate.

**Completion check:** Each passage states its prerequisite forms and glosses other language. Text and artwork are original or specifically licensed; school grade is not used as an L2 proficiency label.

**Dependencies:** [G01](MOAG-GAPS.md#g01), [G04](MOAG-GAPS.md#g04), [G10](MOAG-GAPS.md#g10).

**Evidence:** [lesson10](../../docs/lesson10.md#lesson10-text), [lesson16](../../docs/lesson16.md#lesson16-text), [lesson20](../../docs/lesson20.md#lesson20-text-part-i), [lesson24](../../docs/lesson24.md#lesson24-sample-newspaper-advertisements), [lesson25](../../docs/lesson25.md#lesson25-text).

<a id="g12"></a>
## Earlier listening bridges into casual speech

**Reference:** G12. **Category:** Sequencing and access. **Priority:** Later. **Scope:** Early dialogues, directions in Lesson 18 and minilesson G.

**Observed:** Early vocabulary and dialogues already include conversational short forms. Minilesson G explains several casual-speech changes but is placed after Lesson 24 and asks an instructor to model them.

**Why it matters:** Learners encounter natural reductions well before reaching the dedicated explanation.

**Proposed supplement:** Select a few already relevant phrases per early lesson and provide careful-versus-conversational listening with speaker, variety and register notes. Audit the existing recordings first.

**Completion check:** Every phrase is supported or glossed; recordings are checked against a transcript. Variation is labeled, and learners are not told that one reduction is universal.

**Dependencies:** [G02](MOAG-GAPS.md#g02), [G08](MOAG-GAPS.md#g08).

**Evidence:** [lesson1](../../docs/lesson1.md#lesson1-vocabulary), [lesson2](../../docs/lesson2.md#lesson2-conversation), [lesson18](../../docs/lesson18.md#lesson18-conversation), [minilesson-g](../../docs/minilesson-g.md).

<a id="g13"></a>
## Routes for different ages and existing abilities

**Reference:** G13. **Category:** Audience extension. **Priority:** Optional after the core pilot. **Scope:** Course-wide.

**Observed:** The usage guide discusses university/research learners, heritage undergraduates and self-study, and permits model-led or analytic study. It is not an age-specific family, child or teen curriculum, and no entry diagnostic was identified.

**Why it matters:** Age alone does not reveal whether someone needs speaking, listening, script or grammar support.

**Proposed supplement:** Use separate entry choices for age, Malayalam understanding/speaking, script literacy, purpose and activity preference. Develop versions of the same objective: caregiver game, teen project, independent adult task, or explicit grammar study.

**Completion check:** Routes respond to demonstrated needs and preferences, not fixed learning-style labels. Heritage learners can enter literacy work without repeating skills they already have; beginners still receive prerequisite support.

**Dependencies:** [G03](MOAG-GAPS.md#g03), [G04](MOAG-GAPS.md#g04), [G09](MOAG-GAPS.md#g09).

**Evidence:** [usage](../../docs/usage.md#usage-a-brief-overview), [usage](../../docs/usage.md#usage-how-to-use-the-lessons).

<a id="g14"></a>
## Additional contemporary communication contexts

**Reference:** G14. **Category:** Audience and topic extension. **Priority:** Optional after the core pilot. **Scope:** Selected early and intermediate lessons.

**Observed:** The source period is explicit and several historical facts are already flagged. Existing family, food, travel, office and cultural contexts cover many practical functions. Dedicated activities for current messaging, calls and other learner-selected situations were not identified in the reviewed teaching units.

**Why it matters:** Learners with different purposes may want to apply known forms to situations outside the textbook.

**Proposed supplement:** Choose contexts from learner requests, then create original scripts and tasks using known forms plus a few checked new words. A communication-repair activity can build on existing understanding questions.

**Completion check:** Each extension identifies which existing objective it serves and why its audience needs it. Contemporary factual or usage claims are checked when drafted; updating historical source passages remains separate.

**Dependencies:** [G04](MOAG-GAPS.md#g04), [G07](MOAG-GAPS.md#g07), [G10](MOAG-GAPS.md#g10).

**Evidence:** [lesson1](../../docs/lesson1.md#lesson1-classroom-expressions), [usage](../../docs/usage.md#usage-a-brief-overview), [proofreading-review](../../docs/proofreading-review.md).

## Existing transcription issues to coordinate

The table below copies the status of the current proofreading review as an audit dependency. It does not assign new repair work or establish that an issue remains after subsequent edits. Check the current passage and review file before acting. Clearly corrected early pronouns, prerequisite chunks, spelling errors, and navigation improvements are already credited in the coverage map.

| Current review location | Existing issue | Companion implication |
| --- | --- | --- |
| [Lesson 6, 6.7](../../docs/lesson6.md) | “Construction with -ാൻ” repeats the infinitive ending instead of naming its partner. A note identifies the illustrated infinitive + ഉണ്ട് construction; the source wording remains. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 7, 7.6](../../docs/lesson7.md) | The list “-ന്നു or എന്ന്” does not reliably describe which forms take the limiter. The intended replacement is uncertain. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 8, 8.5](../../docs/lesson8.md) | Missing wording in the restriction on ചോദിക്കുക. The same paragraph also glosses a future example as “I asked.” | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 10, 10.5](../../docs/lesson10.md) | Explanation discusses എന്ന് lists, while the revised reading uses എന്നിവയാണ്. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 13, 13.3](../../docs/lesson13.md) | Incomplete sentence about the relationship between clauses. The translated examples still illustrate the intended contrast. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 14, 14.1](../../docs/lesson14.md) | Garbled wording in the explanation of “each”; a note points learners to the translated pronoun and noun-phrase examples. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 17, 17.4](../../docs/lesson17.md) | Missing prose between നീ and “attention”; address-particle examples remain usable. | Recheck before using the affected passage as an assessed rule or example. |
| [Minilesson E](../../docs/minilesson-e.md) | Claimed nominative requirement conflicts with example 1’s dative എനിക്ക്. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 19, 19.3](../../docs/lesson19.md) | Promised treatment of obligation in 24.6 does not match that section’s ability/inability focus. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 21, 21.3](../../docs/lesson21.md) | “Past” dependent-clause example still uses present negative കിട്ടാത്തത്. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 22, 22.5](../../docs/lesson22.md) | Reference to 24.3 for emphasis with -ആയിട്ട് points to a section about self-benefit compounds. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 23, 23.2](../../docs/lesson23.md) | Past-counterfactual English rendering lacks a corresponding past auxiliary in the Malayalam result clause. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 24, 24.2](../../docs/lesson24.md) | Comparative explanation promises four elements but enumerates only two. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 24, 24.6](../../docs/lesson24.md) | Introductory wording for വയ്യ is missing; a note points to 6.7 and the examples. | Recheck before using the affected passage as an assessed rule or example. |
| [Lesson 25, vocabulary](../../docs/lesson25.md) | ധാന്യം glossed “richness” conflicts with ധന്യമായ/ധന്യമാണ് in the reading and exercise. | Recheck before using the affected passage as an assessed rule or example. |
| [Appendix F, three-argument expressions](../../docs/appendix-f.md) | Three entries contain English translations without Malayalam example sentences, also absent in the PDF. | Recheck before using the affected passage as an assessed rule or example. |
| [Glossary](../../docs/glossary.md) | Original editor queries remain unresolved, including the intended form and translation of പോയിരിക്കുകയായിരിന്നു. They are now labeled as queries. | Recheck before using the affected passage as an assessed rule or example. |
| [Index](../../docs/book-index.md) | Some source page references use obsolete pagination. For example, “Can” cites 399–402, while 24.6 starts on printed page 389. The digital index now supplies verified links for English meanings and selected grammar topics. The historical printed index is retained separately and has not been comprehensively remapped. | Recheck before using the affected passage as an assessed rule or example. |

## Proposed first pilot

Use Lesson 1 to develop the shared support format: a few small study objectives, a parallel script route, one independently checkable pronunciation activity, and feedback for a small practice set. Check the existing Lesson 1 audio first. Test whether an independent learner can complete a new naming or introduction exchange and explain any uncertainty.

Then use Lesson 4 to test meaning and response choices, and Lesson 14 to test adding genuinely missing practice rather than duplicating a full lesson. These are proposed pilots only. No activity, answer key, audio alignment, or learner trial has been implemented in this task.

## Design for later audience choices

Keep the learning objective shared while allowing different activities. A caregiver-led object game, a teen information exchange, an adult independent task and an explicit grammar route can all address the same skill. Keep age separate from existing language and script ability, and use preferences as choices rather than fixed learning-style labels.

Each future supplement should identify its Moag link, objective, prerequisites, intended audience, mode, answer/feedback approach, and provenance. Compose new examples and activities independently; use licensed external material only under its terms. This audit is a planning document and does not establish rights to publish recordings or borrowed textbook material.
