# Malayalam: A University Course

Install dependencies with `bun install`, then run `bun run dev` to preview the
site locally. The static site is served from `docs/`.

Run `bun run docs:sidebar` to regenerate navigation and
`bun run docs:check-sidebar` to verify it is current.

After changing chapter headings, run `bun run docs:navigation` to regenerate
section anchors, chapter navigation, contents, and the sidebar.
Run `bun run docs:check-navigation` and `bun run docs:check-reading` to validate
reading navigation, links, source-page coverage, and Markdown structure.

The symbols chapter uses 93 individually redrawn SVG models in responsive cards.
Edit centerlines, guide curves, and number positions in `scripts/writing_shapes.py`;
run `python3 scripts/build-writing-symbols.py` to regenerate SVGs and chapter grids,
or add `--check` to verify generated files. This build only needs Python's standard
library. The JPEG scans are archival references and are not loaded by the chapter.

Each SVG separates `.writing-ink`, `.writing-guides`, and `.writing-labels`.
Ink paths have named `data-part` attributes and numbered `data-movement`
attributes where the source supplies writing directions. These numbered movements
can be parts of a continuous stroke; they do not imply separate pen lifts.
Diagrams show numbers and arrows with a thin line weight and responsive card sizing.
`docs/assets/writing.css` also exposes `--writing-ink`, `--writing-guide-ink`,
`--writing-background`, `--writing-stroke-width`, and `--writing-card-size`.
The Docsify plugin inlines the SVGs to inherit styling; standalone images remain
the fallback. The original table URLs now assemble the same redrawn models.

Build an EPUB from `docs/` with `bun run docs:epub` (requires Python 3 and
Pandoc 3). The result is `dist/malayalam.epub`; pass `--output PATH` directly to
`python3 scripts/build-epub.py` to choose another destination.
The **Build EPUB and deploy site** GitHub Action runs on docs/exporter changes
and can also be started manually. It validates the book with EPUBCheck and uploads
the `malayalam-epub` artifact. On `main`, it also deploys `docs/` and the generated
book together to GitHub Pages, making the EPUB available at
`https://ml.matj.io/malayalam.epub` through the homepage and footer download links.
Pull requests build and validate without deploying.

For the initial switch from branch publishing, set **Settings → Pages → Build and
deployment → Source** to **GitHub Actions** after merging this workflow. Keep the
existing custom domain `ml.matj.io`. The EPUB is generated during deployment and
does not need to be committed. It becomes available after the first successful
deployment. Local `bun run dev` previews do not include the generated download;
to serve it locally, build the EPUB, assemble `dist/site` as the workflow does,
and run `python3 -m http.server --directory dist/site`.

EPUB adaptations happen in a temporary copy; the website's Markdown is unchanged.
The export includes the textbook in reading order, Practice Lessons A–C, the
edition/practice guides, contents, and proofreading review. Chapter and section
links, photographs, SVG writing diagrams, source credits, and reuse terms are
retained. Audio players and all clip-selection buttons become online recording
links (internet required); expandable answers become always-visible text.
Docsify search, navigation controls, and JavaScript are replaced by the reader's
own controls. A Malayalam font is embedded, but font support and wide-table
layout vary between readers. No companion audio files are bundled.
