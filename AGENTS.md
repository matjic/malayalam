# Working in this repository

This is a source-traceable digital adaptation of Rodney F. Moag’s Malayalam textbook. Read README.md for architecture and commands. The audience is university students, including learners without linguistics training and heritage learners with varied literacy backgrounds.

## Editorial work

Read [the editorial guidelines](guidelines/README.md) before changing teaching content. Consult [sources and limits](guidelines/research.md) when evaluating pedagogical claims or cross-language comparisons.

Preserve source-page comments, stable anchors, vocabulary-table markers, and audio metadata. Identify substantive editorial additions and corrections; keep source attribution clear. Verify new Malayalam examples and usage judgments against reliable Malayalam evidence or qualified review. Record uncertainty. Do not fabricate recordings, translations, citations, or speaker review.

## Implementation and validation

Edit human-readable sources in docs/ and versioned inputs in data/; avoid hand-editing generated dist/ output or generated catalogs. Follow README.md for the specific pipeline. Do not overwrite unrelated existing changes or bulk-stage assets.

For guidelines-only changes, verify links, consistency, and git diff whitespace; rebuilding textbook exports is unnecessary. For lesson edits, run the relevant reading/navigation checks from package.json and any affected vocabulary or audio checks. For publisher changes, run cargo test --locked and applicable output checks. Verify rendering when changing layout or export behavior. Report what was actually checked and any unresolved limitations.
