# Malayalam

Install dependencies with `bun install`, then run `bun run dev` to preview the
site locally. The static site is served from `docs/`.

Run `bun run docs:sidebar` to regenerate navigation and
`bun run docs:check-sidebar` to verify it is current.

After changing chapter headings, run `bun run docs:navigation` to regenerate
section anchors, chapter navigation, contents, and the sidebar.
Run `bun run docs:check-navigation` and `bun run docs:check-reading` to validate
reading navigation, links, source-page coverage, and Markdown structure.

The symbols chapter uses standalone SVG writing tables, preserving the original
handwriting, stroke numbers, and arrows as vector paths. Rebuild them with
`python3 scripts/vectorize-writing-tables.py` (requires ImageMagick and Potrace).
The JPEGs remain archival inputs and are not loaded by that chapter.
`docs/assets/writing.css` controls size, ink, and background through
`--writing-max-width`, `--writing-ink`, and `--writing-background`. The Docsify
plugin inlines the SVGs to inherit theme colors; ordinary SVG images remain the
fallback. These are traced outlines, not separate animated pen strokes.
