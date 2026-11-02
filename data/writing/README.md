# Writing models

`models.json` contains 93 hand-authored centerline models and their order in the 20 tables on Moag PDF pages 27–46. Coordinates are design units, not scan pixels or traced font outlines.

Each shape has a stable ID, symbol, source page, dimensions, caption and named strokes. A stroke contains its ink path, optional guide path, label position and optional transform/arrow size. A guide marks a numbered drawing movement, not necessarily a pen lift. Context strokes have no guide or label. Modern chillu-ll and stacked double-nna use explicitly identified editorial movements.

Run `cargo run --locked -- writing` to regenerate standalone SVGs, assembled tables, the manifest and chapter grids. `--check` verifies freshness. Rust keeps ink, guides and labels in separate layers. Source movement counts are independently protected by the published baseline in `tests/fixtures/writing-movements.json`.
