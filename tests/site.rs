use malayalam::{
    content::{Book, heading_slug},
    routes::{base_path, legacy_link},
    site,
};
use std::{fs, path::Path};

#[test]
fn docsify_heading_aliases_stay_compatible() {
    assert_eq!(
        heading_slug("1.1. How to Use Grammatical Explanations"),
        "_11-how-to-use-grammatical-explanations"
    );
    assert_eq!(heading_slug("  A — B: Questions?  "), "a-b-questions");
    assert_eq!(
        heading_slug("1.5. The Quotative or Citation Particle എന്ന്"),
        "_15-the-quotative-or-citation-particle-എന്ന്"
    );
}

#[test]
fn every_page_and_source_anchor_has_a_canonical_route() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let base = base_path("/malayalam").unwrap();
    let book = Book::load(root, &base).unwrap();
    assert!(book.pages.len() >= 25);
    for page in book.pages.values() {
        for anchor in &page.anchors {
            let old = format!("{}?id={anchor}", page.stem);
            let target = legacy_link(&old, &book.routes, &base).unwrap();
            assert_eq!(
                percent_encoding::percent_decode_str(&target)
                    .decode_utf8()
                    .unwrap(),
                format!("{}#{anchor}", page.route)
            );
        }
    }
}

#[test]
fn rendered_book_preserves_content_styles_media_and_all_local_links() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let output = tempfile::tempdir().unwrap();
    site::build(root, output.path(), "/").unwrap();
    let book = Book::load(root, "/").unwrap();
    assert_eq!(
        book.sidebar,
        fs::read_to_string(root.join("docs/_sidebar.md")).unwrap()
    );
    for page in book.pages.values() {
        let path = output
            .path()
            .join(page.route.trim_start_matches('/'))
            .join("index.html");
        let html = fs::read_to_string(path).unwrap();
        assert!(html.contains("class=\"ready sticky\""));
        assert!(html.contains("class=\"markdown-section\""));
        assert!(html.contains("/assets/vue.css"));
        assert!(html.contains("/assets/runtime/navigation-"));
        assert!(!html.contains("src=\"/assets/docsify@4.js\""));
        assert!(!html.contains("src=\"/assets/docsify_search.min.js\""));
        for anchor in &page.anchors {
            assert!(
                html.contains(&format!("id=\"{}\"", site::escape(anchor))),
                "{} lost {anchor}",
                page.stem
            );
        }
    }
    for stylesheet in [
        "vue",
        "navigation",
        "reading",
        "writing",
        "audio",
        "footer",
        "vocabulary-glossary",
    ] {
        assert_eq!(
            fs::read(root.join(format!("docs/assets/{stylesheet}.css"))).unwrap(),
            fs::read(output.path().join(format!("assets/{stylesheet}.css"))).unwrap()
        );
    }
    let lesson = fs::read_to_string(output.path().join("lesson1/index.html")).unwrap();
    assert!(lesson.contains("പറയൂ"));
    assert!(lesson.contains("data-row-audio-src=\"/assets/audio/"));
    assert!(lesson.contains("id=\"_11-how-to-use-grammatical-explanations\""));
    assert!(!lesson.contains("href=\"#/"));
    assert!(lesson.contains("<ul class=\"app-sub-sidebar\"><li class=\"toc-level-3\">"));
    let search: serde_json::Value =
        serde_json::from_slice(&fs::read(output.path().join("assets/search-index.json")).unwrap())
            .unwrap();
    assert!(
        search
            .as_array()
            .unwrap()
            .iter()
            .any(|entry| entry["body"].as_str().unwrap().contains("മലയാളം"))
    );
    // A completed publishing job must supply the two generated book downloads.
    for export in ["malayalam.epub", "malayalam.pdf"] {
        fs::write(output.path().join(export), b"test artifact").unwrap();
    }
    site::check(output.path(), "/", true).unwrap();
}
