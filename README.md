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
