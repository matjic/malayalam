# Malayalam: A University Course

A source-traceable digital edition of Rodney F. Moag’s *Malayalam: A University
Course and Reference Grammar*. The project combines a Markdown textbook, reviewed
companion audio, editable writing diagrams, and a shared vocabulary catalog to
produce a website, an EPUB, a PDF, and Anki flashcards. The original textbook is
by Rodney F. Moag; this independent digital adaptation and its modifications are
by Mathew Jacob. This edition was not published by Moag.

[Website](https://ml.matj.io/) · [Vocabulary glossary](https://ml.matj.io/#/vocabulary-glossary) · [Anki deck](https://ml.matj.io/assets/decks/malayalam-moag.apkg) · [EPUB](https://ml.matj.io/malayalam.epub) · [PDF](https://ml.matj.io/malayalam.pdf)

## Architecture

The repository is a static publishing system. Human-readable source files and
versioned data feed small Python generators; the website uses Docsify to render
Markdown in the browser. No application server or database is required in production.

| Layer | Representation | Role |
|---|---|---|
| Textbook | Markdown in `docs/` | Editable prose, examples, exercises, and vocabulary tables |
| Source provenance | PDF-page comments, manifests, review records | Connect the edition and derived assets to their sources |
| Writing models | Named paths and guides in `scripts/writing_shapes.py` | Generate standalone SVGs and assembled writing tables |
| Audio | Original MP3s, timestamped clip manifests, explicit repairs | Preserve recordings while producing section, word, and letter playback |
| Vocabulary | Generated `data/vocabulary/moag.json` | Shared structured input for the glossary and Anki exporter |
| Website | Docsify, local JavaScript/CSS/fonts | Reading navigation, search, vocabulary filters, and audio controls |
| Exports | Pandoc EPUB, WeasyPrint PDF, and genanki packages | Reuse the content in ebook readers and spaced-repetition study |

## Content and data flow

The lesson Markdown remains the editable source for vocabulary as well as prose.
A catalog generator extracts written forms, meanings, chapter references, and audio
associations from the tables. The generated glossary combines repeated entries
across chapters; Anki preserves chapter membership through lesson subdecks.
Both outputs use the same catalog rather than maintaining separate vocabulary lists.

Writing diagrams follow a similar pattern: editable stroke geometry generates SVG
assets for the site and ebook. Navigation is derived from chapter titles, explicit
section anchors, and the book’s reading order.

The main source covers all 557 PDF pages, including 25 lessons, seven minilessons,
appendices, glossary, and index. Three supplementary practice lessons are identified
separately from the original textbook. Physical PDF page numbers are retained in
hidden comments, allowing prose and tables to flow across printed page boundaries
without losing source references.

## Audio and review

Audio processing is an offline pipeline. Original recordings are retained with
checksums; generated clips record source offsets and provenance. FFmpeg handles
cutting and encoding. Full Whisper large-v3 recognition, pause detection, repetition
comparison, and Koyal recognition supplied alignment evidence. Direct Core ML
exports of Koyal, including FP16, supported faster experiments with short-clip
boundaries.

Automated output is supplemented by contextual checks and listening corrections.
Explicit repairs bind labels and cuts to their source ranges and checksums, so a
confirmation cannot silently carry over to changed audio. The vocabulary tables,
glossary, and Anki decks reuse the resulting recordings. Missing audio stays absent.

Recognition agreement and passing structural checks do not establish that every
spoken form or translation is correct. The repository retains raw recognition,
review exports, repair records, and unresolved editorial findings so those judgments
can be inspected and revised.

## Delivery and validation

The site is served as static files through GitHub Pages. GitHub Actions builds the
EPUB with Pandoc and validates it with EPUBCheck. Separate jobs render and validate
the PDF and build and test the Anki deck in parallel. Once all three jobs pass, a
publishing job downloads their artifacts and assembles the site for deployment.
Both book formats share content preparation and reading order. The book exports retain the written content and omit audio players, recording
links, and Audio columns. Anki packages embed recordings and a Malayalam font for offline study.

Checks cover page-marker coverage, links, section anchors, numbered-list structure, table structure,
generated-file freshness, SVG models, audio checksums, and alignment regressions.
Anki exports are tested with the official Anki Python backend, including repeat
imports and preservation of review progress. These tests complement editorial and
listening review; they do not replace them.

## Working with the repository

The site preview uses Bun and Docsify:

```sh
bun install
bun run dev
```

Generators use Python; EPUB and PDF export additionally require Pandoc. The PDF
renderer uses Pango and the dependencies in `requirements/pdf.txt`. Anki dependencies
are isolated in `requirements/anki.txt`, with optional backend-test dependencies in
`requirements/anki-test.txt`. Package scripts expose the common build and check
commands.

- [Technical account](docs/technical-notes.md): transcription, tools, review history, architecture, and rebuild commands.
- [Vocabulary documentation](data/vocabulary/README.md): catalog schema conventions, Anki generation, and import tests.
- [Audio documentation](data/audio/moag/README.md): recognition, alignment, boundary experiments, and repair provenance.
- [Proofreading review](docs/proofreading-review.md): corrections, verification scope, and remaining source defects.
- [Deployment workflow](.github/workflows/epub.yml): EPUB/PDF/Anki validation and static-site publication.

## Sources and reuse

The [original textbook PDF](Moag-Malayalam-CompleteTextbook.pdf) is preserved in
this repository and included in the deployed site, alongside the digital edition.

Original textbook material, companion recordings, and supplementary practice
materials retain their respective credits and reuse terms. See [LICENSE.md](LICENSE.md),
the [practice guide](docs/practice.md), and the audio provenance records. The
repository license does not establish a separate reuse license for every imported
recording.
