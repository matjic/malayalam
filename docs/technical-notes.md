# How This Digital Edition Was Built

This project turns Rodney F. Moag’s *Malayalam: A University Course and Reference Grammar* into a readable website, an EPUB, and audio-supported vocabulary materials. The work combines source transcription, editorial review, Python build scripts, browser checks, speech recognition, and listening corrections. Codex assisted with transcription, investigation, implementation, and review; Mathew Jacob directed the work, evaluated the results, and supplied listening corrections.

This account draws on the repository’s commit history, saved build and review records, and the available Codex session history. It describes the processes actually used, including their limitations. The [proofreading review](proofreading-review.md) lists unresolved textbook issues.

## From PDF Pages to Unicode Markdown

The main source was the 557-page fourth-edition PDF. Source pages were rendered for visual reading; extracted English text helped with navigation and comparison. Malayalam text extraction was unreliable, so the transcription depended on the page images rather than trusting extracted character sequences.

The text was organized into Markdown documents for the front matter, script and writing chapters, 25 lessons, seven minilessons, six appendices, glossary, and index. Prose, vocabulary, grammar tables, examples, and exercises became selectable text. Photographs remained images.

Hidden comments preserve source-page provenance for editorial work. Original printed page references and the duplicate printed contents and index have been removed from the visible edition; navigation uses current chapter and section links. The edition retains markers for all 557 pages, even where paragraphs and tables have been joined across a print page break.

Proofreading compared suspected errors with the PDF. Three parallel Codex reviewers covered lesson groups and minilessons, while a coordinating review checked the surrounding chapters and overall consistency. Clear transcription and source errors were corrected; substantive learner guidance and unresolved source contradictions were identified with editorial notes. Unicode repairs included malformed vowel markers and legacy doubled റ spellings that needed the conjunct റ്റ. This was not a comprehensive modernization of historical spelling.

The record of that stage is visible in the [initial transcription commit](https://github.com/matjic/malayalam/commit/3610216) and the [proofreading commit](https://github.com/matjic/malayalam/commit/5858012). A structural coverage check establishes that page markers and sections are present; it does not establish that every sentence is linguistically correct.

## A Website for Reading

The site uses **Docsify** to render ordinary Markdown in the browser, with local CSS, JavaScript, and font assets. **Bun** runs the development server and package scripts. The source remains editable without a database or content-management service.

Python scripts generate the sidebar and previous/next navigation from the textbook’s reading sequence. Descriptive lesson titles were added while retaining the original lesson numbers and numbered grammar sections. Explicit anchors support links to grammar explanations, vocabulary sections, and index targets.

The book exports contain one generated contents list instead of repeating the website and printed contents. The PDF also provides chapter and section bookmarks.

The layout was adapted for narrow screens, including horizontally scrollable tables and a responsive navigation menu. Source-page boundaries no longer interrupt prose. Browser checks exercised chapter navigation, section jumps, tables, and the menu at different viewport sizes.

The three added [practice lessons](practice.md) draw on selected UT Austin pronunciation, sandhi, and conversation materials. They sit after the alphabet, Lesson 2, and Lesson 7. They are identified as additions, with their own source credits and reuse notices.

## Redrawing the Writing Models

The writing chapter’s scanned diagrams were rebuilt as **93 editable SVG models**, also assembled into **20 writing tables**. The models are authored as named paths, guides, arrows, and movement labels in [writing_shapes.py](https://github.com/matjic/malayalam/blob/main/scripts/writing_shapes.py). A Python generator produces the standalone SVGs and chapter grids.

The drawings were compared with the printed models and refined through visual review. Separate ink, guide, and label layers allow theme and size changes without flattening the diagrams into bitmaps. Movement numbers follow the source where supplied; a numbered movement is not necessarily a separate pen lift. Standalone SVG images remain available as a fallback when the website’s inline rendering is unavailable.

## Finding and Cutting the Recordings

The Moag companion collection contains 25 original lesson tracks, about ten hours and twenty-five minutes in total. A manifest records their durations, metadata, and checksums. The original recordings were preserved; browser players use generated excerpts.

The first task was locating section announcements, conversations, exercises, and vocabulary passages. English announcement recognition, pause detection, and comparison with lesson structure helped establish a cue map. That stage included **Whisper large-v3-turbo** and independent **Whisper small** comparisons. Those section-location experiments are separate from the later vocabulary transcription pass.

Individual vocabulary work used the full **Whisper large-v3** model through **MLX**, rather than the turbo model. The pipeline combined Malayalam recognition and word timestamps with English-announcement recognition, pause boundaries, and acoustic comparison of repeated utterances. **FFmpeg** cut and encoded the clips; **ffprobe** checked recording metadata. Where a vocabulary item was spoken twice, the intention was to retain both readings in one clip.

Alignment could not safely rely on list order. The recordings sometimes include additional forms, omit printed items, or recite parts of a longer phrase separately. An early bug allowed broad neighboring English recognition to overwrite a short clip’s label—for example, confusing “tomorrow” and “examination.” The fix required temporal overlap and whole-phrase support, with regression tests to keep that mistake from returning.

A temporary browser review page presented 142 uncertain clips one at a time. Mathew listened, confirmed words, supplied corrections, and flagged silence or bad boundaries. The exported reviews were then checked against the surrounding clips, the original recording, and the printed lesson context. A saved confirmation is tied to its particular source range and clip checksum so it cannot silently approve a later recut.

## Second Opinions and Boundary Experiments

**Koyal**, run locally through **NVIDIA NeMo**, supplied an independent Malayalam recognition pass over the original set of 1,005 word clips and longer excerpts around suspected errors. Word timestamps from the original recordings helped inspect cutoffs and neighboring words. **BuzzASR** was also tried on a small reviewed sample. Its results did not support replacing the existing approach; both systems served as additional evidence.

Koyal’s encoder, predictor, and TDT joint components were exported directly from **PyTorch to Core ML** using **coremltools**, without an ONNX intermediate. FP32 conversion was followed by an FP16 version. The reference transcriber still uses NeMo-based audio preprocessing; this is not a complete independent Swift or iOS implementation.

The faster short-clip inference made it practical to try several start/end variations around troublesome words. Candidate cuts were compared across offsets, inspected for edge energy, and checked again after MP3 encoding. Quiet edges alone were insufficient in noisy recordings. Some candidate cuts received explicit listening approval; others were requested repairs checked by recognizers. The saved records distinguish those cases.

The tested short-input export uses 512 feature frames, roughly five seconds. Long phrases were not truncated merely to fit it. The `cpu_and_ne` setting permits CPU fallback and does not prove that inference ran on the Neural Engine. Recognition stability is useful evidence, not a substitute for hearing and understanding a word.

The [audio process notes](https://github.com/matjic/malayalam/blob/main/data/audio/moag/README.md) link the raw recognizer output, timestamp reports, review exports, cut experiments, and final repair records. Some reports describe earlier snapshots; their old counts and cut ranges should not be mistaken for the current manifest.

## One Vocabulary Catalog, Several Outputs

The lesson tables remain the editable vocabulary source. The [catalog generator](https://github.com/matjic/malayalam/blob/main/scripts/build-vocabulary-catalog.py) exports them to [moag.json](https://github.com/matjic/malayalam/blob/main/data/vocabulary/moag.json), including Malayalam forms, English meanings, lesson references, origins, and audio paths, transcripts, and checksums. The catalog also includes the recorded derived noun from a lesson Reference List.

Additional recorded forms were added to the existing vocabulary tables with meanings, preserving the original printed entries. Missing recordings are left absent rather than filled with a neighboring word. The current catalog has **990 lesson vocabulary entries**, with **997 recordings** attached to **925 entries**; **65 entries are text-only**. Different chapters retain their own occurrences.

The [Vocabulary Glossary](vocabulary-glossary.md) is generated from that catalog. It combines identical word-and-meaning pairs across chapters into **984 entries**, keeps different meanings separate, links to the lessons, and reuses the site’s audio player. Browser controls filter by Malayalam or English text and by lesson. The [original textbook glossary](glossary.md) remains a separate source document.

The [Anki exporter](https://github.com/matjic/malayalam/blob/main/scripts/build-anki.py) uses **genanki** to create one package with a Malayalam parent deck and 25 lesson subdecks. Each entry produces Malayalam → English and English → Malayalam cards, for **1,980 cards**. The recordings and Malayalam font are embedded; entries without audio have no audio control. Stable deck/model identifiers and note GUIDs support repeat imports. A note’s initial identity includes its chapter, written form, and meaning; changing those fields can create a new note.

The local **Anki source repository** was consulted for package-format behavior. Tests with Anki’s official Python backend imported the package into a disposable collection, checked card rendering and embedded media, and verified that reimporting did not duplicate notes or reset a reviewed card’s progress. This backend test is separate from testing every desktop or mobile interface. See the [Anki guide](anki.md) for gradual lesson study.

## EPUB, PDF, and Publication

The [EPUB builder](https://github.com/matjic/malayalam/blob/main/scripts/build-epub.py) prepares temporary copies of the Markdown and uses **Pandoc** to produce EPUB 3. The website’s source files are not rewritten for export. Reading order, linked sections, source credits, photographs, and writing diagrams are retained; expandable practice answers become visible text.

Audio players, recording links, and Audio columns are omitted from the EPUB and PDF; written vocabulary entries are retained. Audio playback remains available on the website and in Anki. Serif typefaces are embedded, but font support and wide-table behavior depend on the reader. **EPUBCheck** validates the generated book in the GitHub Actions workflow. On the main branch, that workflow assembles the static site and EPUB and deploys them to **GitHub Pages** at the project’s custom domain.

The PDF shares the EPUB’s prepared Markdown and reading order. Pandoc generates
HTML, and [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/), using Pango for text shaping, renders A4 pages with
embedded Source Serif 4 and Noto Serif Malayalam type, repeated table headers, page numbers, linked contents,
and PDF bookmarks. The PDF is searchable text rather than a set of page images;
its pagination differs from the source scan. Audio controls and recording links are omitted.
The workflow generates and validates the PDF alongside the EPUB and publishes
both downloads. PDF checks cover text and chapter coverage, embedded Malayalam
fonts, bookmarks, page bounds, and internal link destinations.

## Checks, Rebuilds, and Remaining Limits

The repository includes checks for source-page coverage, numbered sections, relative links, table structure, navigation, SVG geometry and metadata, audio manifests and checksums, generated vocabulary/glossary freshness, and Anki import behavior. These checks catch different classes of mistakes. Passing them does not certify every translation, spoken form, diagram, or phonetic boundary.

The absence of an active audio review flag means the current review queue has been resolved or the form has been placed in its table. It does not mean every automatically transcribed recording received a fresh human listening review. Source contradictions, incomplete grammar explanations, and other unresolved language issues remain documented in the [proofreading review](proofreading-review.md).

For maintainers, the main reproducible steps are:

| Task | Command |
|---|---|
| Preview the site | `bun install`, then `bun run dev` |
| Regenerate chapter navigation | `bun run docs:navigation` |
| Check links, tables, and page markers | `bun run docs:check-reading` |
| Check vocabulary clips and alignment regressions | `bun run docs:check-word-audio` |
| Check individual letter recordings | `bun run docs:check-letter-audio` |
| Rebuild the shared vocabulary catalog | `bun run docs:vocabulary` |
| Rebuild the generated glossary | `bun run docs:glossary` |
| Build Anki packages | `bun run docs:anki` |
| Test Anki import and reimport | `bun run docs:check-anki` |
| Build the EPUB | `bun run docs:epub` |
| Build and validate the PDF | `bun run docs:pdf`, then `bun run docs:check-pdf` |

PDF generation requires Pango and the packages in [requirements/pdf.txt](https://github.com/matjic/malayalam/blob/main/requirements/pdf.txt); its validation also uses PyMuPDF from `requirements/pdf-test.txt`. Use a virtual environment for these tools. On macOS, install Pango with Homebrew; the workflow installs its Linux libraries.

Python commands need a working Python environment. Anki export and its optional backend tests have separate pinned requirements in [requirements/](https://github.com/matjic/malayalam/tree/main/requirements); EPUB generation also needs Pandoc. Fresh speech recognition requires the model-specific environments described in the audio notes, not just the site’s JavaScript dependencies.

The [commit history](https://github.com/matjic/malayalam/commits/main/) records the implementation stages. Useful milestones include the [writing-model redraw](https://github.com/matjic/malayalam/commit/2f15c1e), [reviewed audio integration](https://github.com/matjic/malayalam/commit/61f4e23), [shared vocabulary and exports](https://github.com/matjic/malayalam/commit/0742931), and [site download links](https://github.com/matjic/malayalam/commit/459a887). Private Codex conversations helped reconstruct this account; they are not required to build the project and are not published here.
