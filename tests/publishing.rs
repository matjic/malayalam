use malayalam::{anki, audio, book, reading, util::*, vocabulary};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path};
fn root() -> &'static Path {
    Path::new(env!("CARGO_MANIFEST_DIR"))
}
fn marked(rows: &str, options: Value) -> String {
    format!(
        "<a id=\"test-words\"></a>\n### Renamed heading\n<!-- vocabulary-table: {options} -->\n| Malayalam | English |\n|---|---|\n{rows}\n"
    )
}
fn options() -> Value {
    json!({"kind":"vocabulary","category":"example","cards":true})
}
#[test]
fn labels_control_inclusion() {
    assert!(
        vocabulary::tables(
            "| Malayalam | English |\n|---|---|\n| വാക്ക് | word |\n",
            "test"
        )
        .unwrap()
        .is_empty()
    );
    let t = vocabulary::tables(&marked("| വാക്ക് | word |", options()), "test").unwrap();
    assert_eq!(t[0].anchor, "test-words");
    assert_eq!(vocabulary::words(&t[0]).unwrap()[0].word, "വാക്ക്");
}
#[test]
fn aliases_and_named_columns() {
    let mut o = options();
    o["word"] = json!("Form");
    o["aliases"] = json!("br");
    let text = marked("| our | നമ്മുടെ<br>നമ്മളുടെ |", o)
        .replace("| Malayalam | English |", "| English | Form |");
    let t = vocabulary::tables(&text, "test").unwrap();
    let r = vocabulary::words(&t[0]).unwrap();
    assert_eq!(r[0].word, "നമ്മുടെ");
    assert_eq!(r[0].variants, ["നമ്മളുടെ"]);
    assert_eq!(r[0].meaning, "our");
}
#[test]
fn invalid_contracts_fail() {
    let good = marked("| വാക്ക് | word |", options());
    for broken in [
        good.replace("true", "\"yes\""),
        good.replace("category", "catgory"),
        good.replace(" -->", " broken -->"),
        good.replace("| Malayalam |", "unrelated prose\n| Malayalam |"),
        good.replace("<a id=\"test-words\"></a>", ""),
        good.replace("| word |", "| word | extra |"),
    ] {
        assert!(vocabulary::tables(&broken, "test").is_err(), "{broken}");
    }
}
#[test]
fn excluded_rows_need_reason() {
    for meaning in ["", "(n.)"] {
        assert!(
            vocabulary::tables(&marked(&format!("| പടി | {meaning} |"), options()), "test")
                .is_err()
        );
    }
    let text = marked(
        "| പടി <!-- vocabulary-exclude: missing source meaning --> | |",
        options(),
    );
    let t = vocabulary::tables(&text, "test").unwrap();
    assert!(vocabulary::words(&t[0]).unwrap().is_empty());
    assert!(vocabulary::tables(&text.replace("missing source meaning", ""), "test").is_err());
}
#[test]
fn selected_forms_cannot_disappear() {
    let mut o = options();
    o["cards"] = json!(["നീ"]);
    assert!(vocabulary::tables(&marked("| വാക്ക് | word |", o), "test").is_err());
}
#[test]
fn paradigms_need_seven_cases_once() {
    let rows = [
        "Nominative",
        "Possessive",
        "Dative",
        "Accusative",
        "Addressive",
        "Locative",
        "Instrumental",
    ]
    .map(|c| format!("| {c} | ഞാൻ |\n"))
    .join("");
    let text = format!(
        "<a id=\"pronouns\"></a>\n<!-- vocabulary-table: {{\"kind\":\"paradigm\",\"category\":\"pronoun\",\"cards\":false,\"group\":\"singular\"}} -->\n| Case | First person |\n|---|---|\n{rows}"
    );
    vocabulary::tables(&text, "test").unwrap();
    assert!(vocabulary::tables(&text.replace("| Dative | ഞാൻ |\n", ""), "test").is_err());
    assert!(vocabulary::tables(&(text.clone() + &text), "test").is_err());
}
#[test]
fn catalog_rebuild_is_exact() {
    let current = read_json(root().join("data/vocabulary/moag.json")).unwrap();
    let built = vocabulary::catalog(root()).unwrap();
    assert_eq!(built, current);
    assert_eq!(arr(&built["entries"]).len(), 1123);
    assert_eq!(
        arr(&built["entries"])
            .iter()
            .map(|e| arr(&e["audio"]).len())
            .sum::<usize>(),
        997
    );
}
#[test]
fn essential_function_words_are_studied() {
    let data = read_json(root().join("data/vocabulary/moag.json")).unwrap();
    let forms: BTreeSet<_> = arr(&data["entries"])
        .iter()
        .filter(|e| e["study"] != false)
        .flat_map(|e| std::iter::once(s(&e["malayalam"])).chain(arr(&e["variants"]).iter().map(s)))
        .collect();
    for word in "ഞാൻ നീ നിങ്ങൾ നമ്മൾ ഞങ്ങൾ അവൻ ഇവൻ അവൾ ഇവൾ അയാൾ ഇയാൾ അദ്ദേഹം ഇദ്ദേഹം അവർ ഇവർ എന്റെ നിന്റെ നിങ്ങളുടെ നമ്മുടെ നമ്മളുടെ ഞങ്ങളുടെ അവന്റെ അവളുടെ അവരുടെ എനിക്ക് നിനക്ക് നിങ്ങൾക്ക് നമുക്ക് നമ്മൾക്ക് ഞങ്ങൾക്ക് ആര് എന്ത് ഏത് എവിടെ എപ്പോൾ എങ്ങനെ എത്ര മുകളിൽ താഴെ ഇടയിൽ കുറിച്ച് ശേഷം പകരം നിന്ന് വരെ കൂടെ".split_whitespace(){assert!(forms.contains(word),"{word}");}
}
#[test]
fn case_restrictions_and_reference_only_survive() {
    let d = read_json(root().join("data/vocabulary/moag.json")).unwrap();
    let e = arr(&d["entries"]);
    assert!(e.iter().any(|e| e["study"] == false));
    assert!(
        e.iter()
            .filter(|e| e["study"] == false)
            .all(|e| e["category"] == "postposition")
    );
    let around = e
        .iter()
        .find(|e| e["malayalam"] == "ചുറ്റും" && s(&e["english"]).contains("possessive"))
        .unwrap();
    assert!(!s(&around["english"]).contains("also dative"));
    let near = e
        .iter()
        .find(|e| e["malayalam"] == "അടുത്ത്" && e["origin"] == "reference_table")
        .unwrap();
    assert!(s(&near["english"]).contains("also dative"));
    let alias = e
        .iter()
        .find(|e| e["chapter"] == 22 && e["malayalam"] == "ആർക്കെങ്കിലും")
        .unwrap();
    assert!(arr(&alias["variants"]).contains(&json!("ആർക്കായാലും")));
}
#[test]
fn edited_and_reordered_rows_keep_ids() {
    let old = json!([{"id":"first","chapter":6,"malayalam":"കൂടെ","english":"first sense","source_anchor":"possessive"},{"id":"second","chapter":6,"malayalam":"കൂടെ","english":"second sense","source_anchor":"associative"}]);
    let mut entries = arr(&old).to_vec();
    entries.reverse();
    for e in &mut entries {
        e["english"] = json!(s(&e["english"]).to_string() + " corrected");
        e["id"] = json!("new hash");
    }
    vocabulary::preserve_ids(&mut entries, arr(&old)).unwrap();
    assert_eq!(entries[0]["id"], "second");
    assert_eq!(entries[1]["id"], "first");
}
#[test]
fn social_ranking_labels_cannot_return() {
    for entry in fs::read_dir(root().join("docs")).unwrap() {
        let p = entry.unwrap().path();
        if p.extension().is_some_and(|e| e == "md") {
            let text = fs::read_to_string(&p).unwrap();
            for t in table_re().find_iter(&text) {
                assert!(
                    !re(r"(?i)\b(?:inferior|superior)s?\b|equal to (?:the )?speaker")
                        .is_match(&clean(t.as_str())),
                    "{}",
                    p.display()
                );
            }
        }
    }
}
fn data() -> Value {
    json!({"schema_version":1,"chapters":[{"number":3,"title":"Third"},{"number":1,"title":"First"}],"entries":[{"id":"published-id","chapter":3,"malayalam":"വാക്ക്","english":"word","origin":"textbook","source":"docs/lesson3.md","audio":[]}]})
}
#[test]
fn invalid_card_inputs_fail() {
    let base = data();
    let mut cases = vec![];
    let mut d = base.clone();
    d["schema_version"] = json!(2);
    cases.push(d);
    let mut d = base.clone();
    {
        let duplicate = d["entries"][0].clone();
        d["entries"].as_array_mut().unwrap().push(duplicate);
    };
    cases.push(d);
    let mut d = base.clone();
    d["entries"][0]["chapter"] = json!(2);
    cases.push(d);
    let mut d = base.clone();
    d["chapters"]
        .as_array_mut()
        .unwrap()
        .push(json!({"number":3}));
    cases.push(d);
    let mut d = base.clone();
    d["entries"][0]["study"] = json!("yes");
    cases.push(d);
    for d in cases {
        assert!(anki::validate(&d, &json!({})).is_err());
    }
    for o in [
        json!({"absent":{"meaning":"word"}}),
        json!({"published-id":{"recall":"വാക്ക്"}}),
        json!({"published-id":{"recall":""}}),
        json!({"published-id":{"alternatives":"word"}}),
        json!({"published-id":{"alternatives":[""]}}),
        json!({"published-id":{"typo":"word"}}),
        json!({"published-id":"word"}),
    ] {
        assert!(anki::validate(&base, &o).is_err());
    }
}
#[test]
fn punctuation_collisions_need_reciprocal_answers() {
    let mut d = data();
    d["entries"]
        .as_array_mut()
        .unwrap()
        .push(json!({"id":"second","chapter":3,"malayalam":"മറ്റൊന്ന്","english":"Word!","audio":[]}));
    assert!(anki::validate(&d, &json!({})).is_err());
    assert!(anki::validate(&d, &json!({"published-id":{"alternatives":["മറ്റൊന്ന്"]}})).is_err());
    anki::validate(
        &d,
        &json!({"published-id":{"alternatives":["മറ്റൊന്ന്"]},"second":{"alternatives":["വാക്ക്"]}}),
    )
    .unwrap();
}
#[test]
fn answer_notes_do_not_leak_into_front() {
    let d = data();
    let e = &d["entries"][0];
    let f = anki::fields(
        e,
        &json!({"published-id":{"recall":"a word (noun)","alternatives":["മറ്റൊരു വാക്ക്"],"explanation":"Accept either"}}),
        &d["chapters"][0],
    );
    assert!(f[2].contains("english-meaning"));
    assert!(f[2].contains("english-recall"));
    assert!(!f[2].contains("Also accept"));
    assert!(f[5].contains("Also accept"));
    assert_eq!(f[4], "Third");
}
#[test]
fn prompts_have_separate_lines() {
    assert_eq!(
        anki::format_text("your (plural or polite singular; possessive pronoun)"),
        "<div class=\"prompt-main\">your</div><div class=\"prompt-cue\">plural or polite singular</div><div class=\"prompt-cue\">possessive pronoun</div>"
    );
    let f = anki::format_text("if (you) come (verb (not a noun); polite)");
    assert!(f.contains("prompt-main\">if (you) come"));
    assert!(f.contains("prompt-cue\">verb (not a noun)"));
    assert_eq!(
        anki::format_text("(I) wish to"),
        "<div class=\"prompt-main\">(I) wish to</div>"
    );
    assert!(anki::format_text("say <hello> (a & b)").contains("say &lt;hello&gt;"));
}
#[test]
fn all_published_note_guids_and_fields_match() {
    let d = read_json(root().join("data/vocabulary/moag.json")).unwrap();
    let o = read_json(root().join("data/vocabulary/study.json")).unwrap();
    anki::validate(&d, &o).unwrap();
    let fixtures = read_json(root().join("tests/fixtures/published-notes.json")).unwrap();
    let entries: Vec<_> = arr(&d["entries"])
        .iter()
        .filter(|e| e["study"] != false)
        .collect();
    assert_eq!(entries.len(), arr(&fixtures).len());
    for e in &entries {
        let expected = arr(&fixtures).iter().find(|f| f["id"] == e["id"]).unwrap();
        let chapter = arr(&d["chapters"])
            .iter()
            .find(|c| c["number"] == e["chapter"])
            .unwrap();
        let fields = anki::fields(e, &o, chapter);
        assert_eq!(e["id"], expected["id"]);
        assert_eq!(anki::guid(s(&e["id"])), s(&expected["guid"]));
        assert_eq!(
            hash(fields.join("\x1f")),
            s(&expected["fields_sha256"]),
            "{}",
            e["id"]
        );
    }
    assert_eq!(anki::stable_id("moag-vocab-model-v1"), 1843859663);
    assert_eq!(anki::stable_id("moag-parent"), 1085467152);
}
#[test]
fn audio_rows_stay_distinct() {
    let text = "| Malayalam | English |\n|---|---|\n| നാളെ | tomorrow |\n| പരീക്ഷ | exam |\n";
    let entries = json!([{"transcript":"നാളെ","status":"matched","path":"docs/tomorrow.mp3"},{"transcript":"പരീക്ഷ","status":"matched","path":"docs/exam.mp3"}]);
    let rendered = audio::add_columns(
        text,
        arr(&entries),
        &[vec!["നാളെ".into()], vec!["പരീക്ഷ".into()]],
    )
    .unwrap();
    let tomorrow = rendered.lines().find(|l| l.starts_with("| നാളെ")).unwrap();
    assert!(tomorrow.contains("tomorrow.mp3"));
    assert!(!tomorrow.contains("exam.mp3"));
    assert_eq!(audio::strip_columns(&rendered, true), text);
}
#[test]
fn unverified_clips_never_claim_printed_row() {
    let e = json!([{"transcript":"നാളെ","status":"review","path":"docs/c.mp3"}]);
    let text = "| Malayalam | English |\n|---|---|\n| നാളെ | tomorrow |\n";
    let out = audio::add_columns(text, arr(&e), &[vec!["നാളെ".into()]]).unwrap();
    assert!(
        out.lines()
            .find(|l| l.starts_with("| നാളെ"))
            .unwrap()
            .contains("audio-unmatched")
    );
    assert!(out.contains("Unconfirmed:"));
}
#[test]
fn repaired_recordings_keep_labels_and_placement() {
    let m = read_json(root().join("docs/assets/audio/moag/words/manifest.json")).unwrap();
    for (id, word) in [
        ("lesson_08_word_011", "നാളെ"),
        ("lesson_08_word_012", "പരീക്ഷ"),
        ("lesson_02_word_010", "ആഫീസിൽ"),
        ("lesson_06_word_013", "ധാരാളം"),
        ("lesson_12_word_006", "വയറ്"),
        ("lesson_14_word_025", "കല"),
        ("lesson_25_word_059", "സംഗീതം"),
        ("lesson_24_word_027", "സ്നേഹം"),
    ] {
        let c = arr(&m["clips"])
            .iter()
            .find(|c| s(&c["path"]).ends_with(&format!("/{id}.mp3")))
            .unwrap();
        assert_eq!(c["transcript"], word);
        let text =
            fs::read_to_string(root().join(format!("docs/lesson{}.md", c["lesson"]))).unwrap();
        let line = text
            .lines()
            .find(|l| {
                l.contains(&format!(
                    "data-row-audio-src=\"{}\"",
                    s(&c["path"]).trim_start_matches("docs/")
                ))
            })
            .unwrap();
        assert!(line.contains(word));
        assert!(!line.contains("check match"));
    }
}
#[test]
fn silence_spans_handle_open_eof_silence() {
    assert_eq!(
        audio::parse_spans(
            "silence_start: 1.0\nsilence_end: 1.5\nsilence_start: 2.0\nsilence_end: 3.0",
            3.,
            0.1
        )
        .unwrap(),
        [(0., 1.), (1.5, 2.)]
    );
}
#[test]
fn python_word_semantics_keep_old_fragment_ids() {
    assert_eq!(
        reading::slug("B. Note how -ഉം joins"),
        "b-note-how--u0d09-joins"
    );
    assert_eq!(
        reading::slug("ട്രെയിനിലെ ഒരു രംഗം"),
        "u0d1fu0d30u0d2fu0d28u0d32-u0d12u0d30-u0d30u0d17"
    );
}
#[test]
fn malformed_markdown_tables_fail() {
    for text in [
        "| A | B |\n| row | value |\n",
        "| A | B |\n|---|---|\n| too | many | cells |\n",
        "| | B |\n|---|---|\n",
    ] {
        assert!(reading::validate_tables(text).is_err());
    }
}
#[test]
fn portable_book_has_no_playback_ui_and_preserves_recorded_rows() {
    let d = root().join("docs/lesson8.md");
    let stripped = book::strip_audio(&fs::read_to_string(d).unwrap());
    assert!(!stripped.contains("data-row-audio-src"));
    assert!(!stripped.contains("<audio"));
    assert!(stripped.contains("| നാളെ | tomorrow |"));
    assert!(stripped.contains("| പരീക്ഷ |"));
}
#[test]
fn book_has_unique_anchors_and_no_missing_internal_destinations() {
    let text = book::markdown(root()).unwrap();
    assert!(!text.contains("<audio"));
    assert!(!text.contains("<button"));
    assert!(!re(r"\]\([^)]*\.mp3").is_match(&text));
    let ids: BTreeSet<_> = re(r"\{#([^}]+)\}")
        .captures_iter(&text)
        .map(|c| c[1].to_string())
        .chain(
            re(r#"\bid="([^"]+)""#)
                .captures_iter(&text)
                .map(|c| c[1].to_string()),
        )
        .collect();
    for c in re(r"\]\(#([^)]*)\)").captures_iter(&text) {
        assert!(ids.contains(&c[1]), "missing book destination {}", &c[1]);
    }
    assert!(!text.contains("front-matter-table-of-contents"));
}
#[test]
fn generated_sources_are_fresh() {
    reading::navigation(root(), true).unwrap();
    vocabulary::glossary(root(), true).unwrap();
    malayalam::writing::build(root(), true).unwrap();
}
#[test]
fn no_python_tooling_or_legacy_runtime_can_return() {
    for dir in ["src", "tests", "templates", ".github"] {
        for entry in walkdir::WalkDir::new(root().join(dir))
            .into_iter()
            .filter_map(Result::ok)
        {
            assert!(
                entry.path().extension().is_none_or(|s| s != "py"),
                "Python source: {}",
                entry.path().display()
            );
        }
    }
    assert!(!root().join("scripts").exists());
    assert!(!root().join("requirements").exists());
    for path in [
        "package.json",
        ".github/workflows/epub.yml",
        ".github/workflows/unit-tests.yml",
    ] {
        let text = fs::read_to_string(root().join(path)).unwrap();
        assert!(
            !text.contains("python") && !text.contains("pip install"),
            "obsolete runtime in {path}"
        );
    }
    for name in [
        "docsify@4.js",
        "docsify_search.min.js",
        "docsify-themeable.min.js",
    ] {
        assert!(!root().join("docs/assets").join(name).exists());
    }
}
#[test]
fn archive_paths_cannot_escape_and_hashes_are_checked() {
    let tmp = tempfile::tempdir().unwrap();
    fs::write(tmp.path().join("data.txt"), "source").unwrap();
    let manifest = tmp.path().join("manifest.json");
    write_json(
        &manifest,
        &json!({"files":[{"path":"data.txt","sha256":hash("source"),"bytes":6}]}),
        false,
    )
    .unwrap();
    malayalam::resources::archive(tmp.path(), &manifest, true).unwrap();
    fs::write(tmp.path().join("data.txt"), "changed").unwrap();
    assert!(malayalam::resources::archive(tmp.path(), &manifest, true).is_err());
    write_json(
        &manifest,
        &json!({"files":[{"path":"../outside.txt"}]}),
        false,
    )
    .unwrap();
    assert!(malayalam::resources::archive(tmp.path(), &manifest, true).is_err());
}
#[test]
fn imported_zip_rejects_traversal() {
    use std::io::Write;
    let tmp = tempfile::tempdir().unwrap();
    let archive = tmp.path().join("story.zip");
    let mut zip = zip::ZipWriter::new(fs::File::create(&archive).unwrap());
    zip.start_file("../escape.txt", zip::write::FileOptions::default())
        .unwrap();
    zip.write_all(b"no").unwrap();
    zip.finish().unwrap();
    assert!(malayalam::resources::import_story(&archive, &tmp.path().join("story")).is_err());
    assert!(!tmp.path().join("escape.txt").exists());
}
#[test]
fn package_database_and_embedded_media_follow_published_contract() {
    use std::io::Read;
    let tmp = tempfile::tempdir().unwrap();
    let summary = anki::build(root(), tmp.path(), false).unwrap();
    assert_eq!(summary["notes"], 1085);
    assert_eq!(summary["cards"], 2170);
    let mut zip =
        zip::ZipArchive::new(fs::File::open(tmp.path().join("malayalam-moag.apkg")).unwrap())
            .unwrap();
    let mut bytes = vec![];
    zip.by_name("collection.anki2")
        .unwrap()
        .read_to_end(&mut bytes)
        .unwrap();
    let path = tmp.path().join("collection.anki2");
    fs::write(&path, bytes).unwrap();
    let conn = rusqlite::Connection::open(path).unwrap();
    assert_eq!(
        conn.query_row("select count(*) from notes", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        1085
    );
    assert_eq!(
        conn.query_row("select count(*) from cards", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        2170
    );
    let models: String = conn
        .query_row("select models from col", [], |r| r.get(0))
        .unwrap();
    let models: Value = serde_json::from_str(&models).unwrap();
    let model = &models["1843859663"];
    assert_eq!(
        arr(&model["flds"])
            .iter()
            .map(|f| s(&f["name"]))
            .collect::<Vec<_>>(),
        anki::FIELD_NAMES
    );
    assert_eq!(model["sortf"], 1);
    assert_eq!(model["tmpls"][0]["name"], "Malayalam → English");
    assert_eq!(model["tmpls"][1]["name"], "English → Malayalam");
    assert!(!s(&model["tmpls"][1]["qfmt"]).contains("{{Audio}}"));
    let mut media = String::new();
    zip.by_name("media")
        .unwrap()
        .read_to_string(&mut media)
        .unwrap();
    let media: Value = serde_json::from_str(&media).unwrap();
    assert_eq!(media.as_object().unwrap().len(), 998);
    let data = read_json(root().join("data/vocabulary/moag.json")).unwrap();
    for e in arr(&data["entries"]) {
        if e["study"] == false {
            continue;
        }
        let stored: String = conn
            .query_row(
                "select guid from notes where flds like ?1",
                [format!("{}\u{1f}%", s(&e["id"]))],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(stored, anki::guid(s(&e["id"])));
        for clip in arr(&e["audio"]) {
            let name = format!(
                "moag_{}",
                Path::new(s(&clip["path"]))
                    .file_name()
                    .unwrap()
                    .to_string_lossy()
            );
            let index = media
                .as_object()
                .unwrap()
                .iter()
                .find(|(_, v)| **v == name)
                .unwrap()
                .0;
            let mut bytes = vec![];
            zip.by_name(index).unwrap().read_to_end(&mut bytes).unwrap();
            assert_eq!(hash(bytes), s(&clip["sha256"]));
        }
    }
}
#[test]
fn writing_coverage_and_movement_counts_remain_independent_of_generator() {
    let baseline = read_json(root().join("tests/fixtures/writing-movements.json")).unwrap();
    let models = read_json(root().join("data/writing/models.json")).unwrap();
    assert_eq!(models["shapes"].as_object().unwrap().len(), 93);
    assert_eq!(models["tables"].as_object().unwrap().len(), 20);
    for expected in arr(&baseline) {
        let shape = &models["shapes"][s(&expected["id"])];
        assert_eq!(shape["symbol"], expected["symbol"]);
        assert_eq!(shape["page"], expected["sourcePage"]);
        assert_eq!(
            arr(&shape["strokes"])
                .iter()
                .filter(|stroke| !s(&stroke["guide"]).is_empty())
                .count() as u64,
            expected["movements"].as_u64().unwrap()
        );
    }
}
#[test]
fn wrapped_pdf_bookmark_names_match_known_source_headings() {
    let expected = BTreeSet::from([
        "Contents".into(),
        "Lesson 3: Existence, Possession, and Polite Commands".into(),
        "GoGo".into(),
    ]);
    assert_eq!(
        book::bookmark_title("ContentsContents", &expected).as_deref(),
        Some("Contents")
    );
    assert_eq!(book::bookmark_title("Lesson 3: Existence, Possession, and PoliteLesson 3: Existence, Possession, and PoliteCommands",&expected).as_deref(),Some("Lesson 3: Existence, Possession, and Polite Commands"));
    assert_eq!(
        book::bookmark_title("GoGo", &expected).as_deref(),
        Some("GoGo")
    );
    assert!(book::bookmark_title("unknownunknown", &expected).is_none());
}
