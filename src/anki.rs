//! APKG compatibility: six fields, two templates, stable model/deck IDs and GUIDs.
use crate::util::*;
use anyhow::{Result, ensure};
use genanki_rs::{Deck, Field, Model, Note, Package, Template};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::Path,
};

pub const FIELD_NAMES: [&str; 6] = [
    "EntryID",
    "Malayalam",
    "English",
    "Audio",
    "Chapter",
    "Source",
];
pub fn stable_id(text: &str) -> i64 {
    1_000_000_000
        + i64::from(u32::from_be_bytes(
            Sha256::digest(text.as_bytes())[..4].try_into().unwrap(),
        )) % 1_000_000_000
}
pub fn guid(text: &str) -> String {
    let alphabet=b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&()*+,-./:;<=>?@[]^_`{|}~";
    let mut n = u64::from_be_bytes(Sha256::digest(text.as_bytes())[..8].try_into().unwrap());
    let mut out = vec![];
    while n > 0 {
        out.push(alphabet[(n % 91) as usize]);
        n /= 91;
    }
    out.reverse();
    String::from_utf8(out).unwrap()
}
pub fn format_text(text: &str) -> String {
    let mut main = text.trim();
    let mut cues = vec![];
    while main.ends_with(')') {
        let mut depth = 0;
        let mut start = None;
        for (i, c) in main.char_indices().rev() {
            if c == ')' {
                depth += 1;
            } else if c == '(' {
                depth -= 1;
                if depth == 0 {
                    start = Some(i);
                    break;
                }
            }
        }
        let Some(i) = start else {
            break;
        };
        if main[..i].trim().is_empty() {
            break;
        }
        cues.insert(0, &main[i + 1..main.len() - 1]);
        main = main[..i].trim_end();
    }
    let mut out = format!("<div class=\"prompt-main\">{}</div>", esc(main));
    for cue in cues {
        let mut depth = 0;
        let mut start = 0;
        for (i, c) in cue.char_indices() {
            match c {
                '(' => depth += 1,
                ')' => depth -= 1,
                ';' if depth == 0 => {
                    let line = cue[start..i].trim();
                    if !line.is_empty() {
                        out += &format!("<div class=\"prompt-cue\">{}</div>", esc(line));
                    }
                    start = i + 1;
                }
                _ => {}
            }
        }
        let last = cue[start..].trim();
        if !last.is_empty() {
            out += &format!("<div class=\"prompt-cue\">{}</div>", esc(last));
        }
    }
    out
}
pub fn meaning<'a>(entry: &'a Value, study: &'a Value) -> &'a str {
    study[s(&entry["id"])]["meaning"]
        .as_str()
        .unwrap_or_else(|| s(&entry["english"]))
}
pub fn recall<'a>(entry: &'a Value, study: &'a Value) -> &'a str {
    study[s(&entry["id"])]["recall"]
        .as_str()
        .unwrap_or_else(|| meaning(entry, study))
}
pub fn validate(data: &Value, study: &Value) -> Result<()> {
    ensure!(data["schema_version"] == 1, "unsupported vocabulary schema");
    ensure!(study.is_object(), "study metadata must be object");
    let mut chapters = BTreeSet::new();
    for c in arr(&data["chapters"]) {
        ensure!(
            c["number"].as_u64().is_some_and(|n| n > 0)
                && chapters.insert(c["number"].as_u64().unwrap()),
            "invalid/duplicate chapter"
        );
    }
    let mut ids = BTreeSet::new();
    let mut groups: BTreeMap<String, Vec<&Value>> = BTreeMap::new();
    for e in arr(&data["entries"]) {
        let id = s(&e["id"]);
        ensure!(!id.is_empty() && ids.insert(id), "duplicate/empty ID");
        ensure!(
            chapters.contains(&e["chapter"].as_u64().unwrap_or(0)),
            "unknown chapter: {id}"
        );
        ensure!(
            e["study"].is_null() || e["study"].is_boolean(),
            "invalid study selection: {id}"
        );
        let o = &study[id];
        if !o.is_null() {
            ensure!(
                o.is_object()
                    && o.as_object().unwrap().keys().all(|k| [
                        "meaning",
                        "recall",
                        "explanation",
                        "alternatives"
                    ]
                    .contains(&k.as_str())),
                "invalid study metadata: {id}"
            );
            for f in ["meaning", "recall", "explanation"] {
                ensure!(
                    o[f].is_null() || !s(&o[f]).trim().is_empty(),
                    "empty/invalid {f}: {id}"
                );
            }
            ensure!(
                o["alternatives"].is_null()
                    || (o["alternatives"].is_array()
                        && arr(&o["alternatives"])
                            .iter()
                            .all(|a| !s(a).trim().is_empty())),
                "invalid alternatives: {id}"
            );
        }
        ensure!(
            !s(&e["malayalam"]).trim().is_empty()
                && !meaning(e, study).trim().is_empty()
                && !ml(meaning(e, study)),
            "English card text needs review: {id}"
        );
        let prompt = recall(e, study);
        ensure!(
            !prompt.trim().is_empty() && !ml(prompt),
            "recall needs review: {id}"
        );
        if e["study"] == false {
            continue;
        }
        let normalized = re(r"[^\w]+")
            .replace_all(&prompt.to_lowercase(), " ")
            .trim()
            .to_string();
        ensure!(
            !normalized.is_empty() && !re(r"^(n|adj|adv|v|noun|verb)$").is_match(&normalized),
            "incomplete recall: {id}"
        );
        ensure!(
            !re(r"(?i)\b(?:inferior|superior)s?\b").is_match(meaning(e, study)),
            "social ranking label: {id}"
        );
        groups.entry(normalized).or_default().push(e);
    }
    for id in study.as_object().unwrap().keys() {
        ensure!(ids.contains(id.as_str()), "unused study override: {id}");
    }
    for (prompt, group) in groups {
        let words: BTreeSet<_> = group.iter().map(|e| s(&e["malayalam"])).collect();
        if words.len() < 2 {
            continue;
        }
        for e in group {
            let accepted: BTreeSet<_> = std::iter::once(s(&e["malayalam"]))
                .chain(arr(&e["variants"]).iter().map(s))
                .chain(arr(&study[s(&e["id"])]["alternatives"]).iter().map(s))
                .collect();
            ensure!(
                words.is_subset(&accepted),
                "ambiguous recall prompt: {prompt}: {}",
                e["id"]
            );
        }
    }
    Ok(())
}
pub fn fields(e: &Value, study: &Value, chapter: &Value) -> Vec<String> {
    let mut sounds = String::new();
    for c in arr(&e["audio"]) {
        let name = Path::new(s(&c["path"]))
            .file_name()
            .unwrap()
            .to_string_lossy();
        let variant = if c["transcript"] != e["malayalam"] {
            format!(
                "<div class=\"variant\" lang=\"ml\">Recorded: {}</div>",
                esc(s(&c["transcript"]))
            )
        } else {
            String::new()
        };
        sounds += &format!("<div class=\"recording\">{variant}[sound:moag_{name}]</div>");
    }
    let o = &study[s(&e["id"])];
    let mut source = String::new();
    if ml(s(&e["english"])) {
        source += &format!(
            "<div class=\"lesson-note\">Lesson note: {}</div>",
            esc(s(&e["english"]))
        );
    }
    let mut alternatives = vec![];
    for a in arr(&o["alternatives"]).iter().chain(arr(&e["variants"])) {
        if !alternatives.contains(&s(a)) {
            alternatives.push(s(a));
        }
    }
    if !alternatives.is_empty() {
        source += "<div class=\"alternatives\"><div>Also accept:</div><ul>";
        for a in alternatives {
            source += &format!("<li lang=\"ml\">{}</li>", esc(a));
        }
        source += "</ul></div>";
    }
    for note in arr(&e["notes"]) {
        source += &format!(
            "<div class=\"lesson-note\">Source note: {}</div>",
            esc(s(note))
        );
    }
    if let Some(explanation) = o["explanation"].as_str() {
        source += &format!("<div class=\"usage-note\">{}</div>", esc(explanation));
    }
    let page = Path::new(s(&e["source"]))
        .file_stem()
        .unwrap()
        .to_string_lossy();
    let mut url = format!("https://matjic.github.io/malayalam/#/{page}");
    if let Some(anchor) = e["source_anchor"].as_str() {
        url += &format!("?id={anchor}");
    }
    source += &format!("<a href=\"{}\">Open lesson</a>", esc(&url));
    vec![
        s(&e["id"]).into(),
        esc(s(&e["malayalam"])),
        format!(
            "<div class=\"english-meaning\">{}</div><div class=\"english-recall\">{}</div>",
            format_text(meaning(e, study)),
            format_text(recall(e, study))
        ),
        sounds,
        esc(s(&chapter["title"])),
        source,
    ]
}
pub fn build(root: &Path, output: &Path, site_copy: bool) -> Result<Value> {
    let data = read_json(root.join("data/vocabulary/moag.json"))?;
    let study = read_json(root.join("data/vocabulary/study.json"))?;
    validate(&data, &study)?;
    let model=Model::new(stable_id("moag-vocab-model-v1"),"Malayalam Moag Vocabulary v1",FIELD_NAMES.iter().map(|n|Field::new(n)).collect(),vec![
 Template::new("Malayalam → English").qfmt("<div class=\"chapter\">{{Chapter}}</div><div class=\"ml\" lang=\"ml\">{{Malayalam}}</div>").afmt("{{FrontSide}}<hr id=\"answer\"><div>{{English}}</div>{{Audio}}<div class=\"source\">{{Source}}</div>"),
 Template::new("English → Malayalam").qfmt("<div class=\"chapter\">{{Chapter}}</div><div class=\"recall-question\">{{English}}</div>").afmt("{{FrontSide}}<hr id=\"answer\"><div class=\"ml\" lang=\"ml\">{{Malayalam}}</div><div>{{English}}</div>{{Audio}}<div class=\"source\">{{Source}}</div>")]).css(&fs::read_to_string(root.join("templates/anki.css"))?).sort_field_index(1);
    let chapters: BTreeMap<_, _> = arr(&data["chapters"])
        .iter()
        .map(|c| (c["number"].as_u64().unwrap(), c))
        .collect();
    let mut decks: BTreeMap<_, _> = chapters
        .iter()
        .map(|(n, c)| {
            (
                *n,
                Deck::new(
                    stable_id(&format!("moag-chapter-{n}")),
                    &format!("Malayalam::Lesson {n:02}"),
                    &esc(s(&c["title"])),
                ),
            )
        })
        .collect();
    let tmp = tempfile::tempdir()?;
    let mut media = BTreeMap::new();
    let selected: Vec<_> = arr(&data["entries"])
        .iter()
        .filter(|e| e["study"] != false)
        .collect();
    for e in &selected {
        for c in arr(&e["audio"]) {
            let p = inside(root, s(&c["path"]))?;
            ensure!(
                digest(&p)? == s(&c["sha256"]),
                "audio checksum mismatch: {}",
                p.display()
            );
            let name = format!("moag_{}", p.file_name().unwrap().to_string_lossy());
            if let Some(old) = media.insert(name.clone(), p.clone()) {
                ensure!(old == p, "media basename collision: {name}");
            }
        }
        let n = e["chapter"].as_u64().unwrap();
        let f = fields(e, &study, chapters[&n]);
        let note = Note::new(model.clone(), f.iter().map(String::as_str).collect())?
            .guid(guid(s(&e["id"])))
            .tags([
                format!("moag::lesson_{n:02}"),
                format!("moag::{}", s(&e["origin"])),
                format!(
                    "audio::{}",
                    if f[3].is_empty() {
                        "unavailable"
                    } else {
                        "available"
                    }
                ),
            ]);
        decks.get_mut(&n).unwrap().add_note(note);
    }
    let fonts: Vec<_> = fs::read_dir(root.join("docs/assets/fonts"))?
        .filter_map(Result::ok)
        .map(|e| e.path())
        .filter(|p| {
            p.file_name()
                .unwrap()
                .to_string_lossy()
                .ends_with("RuDNG1bFn6E.woff2")
        })
        .collect();
    ensure!(fonts.len() == 1, "expected one Malayalam deck font");
    let audio_files = media.len();
    media.insert("_malayalam_noto.woff2".into(), fonts[0].clone());
    let mut staged = vec![];
    for (name, p) in media {
        let target = tmp.path().join(name);
        fs::copy(p, &target)?;
        staged.push(target.to_string_lossy().to_string());
    }
    let parent = Deck::new(
        stable_id("moag-parent"),
        "Malayalam",
        "Moag chapter vocabulary with embedded recordings. See the accompanying README for gradual lesson study.",
    );
    let mut all = vec![parent];
    all.extend(decks.into_values());
    let mut package = Package::new(all, staged.iter().map(String::as_str).collect())?;
    let archive = tmp.path().join("malayalam-moag.apkg");
    package.write_to_file(archive.to_str().unwrap())?;
    // The crate assigns every new card due=0. Retain the published lesson order.
    let patched = tmp.path().join("ordered.apkg");
    rewrite_due(&archive, &patched)?;
    fs::create_dir_all(output)?;
    fs::copy(&patched, output.join("malayalam-moag.apkg"))?;
    let with_audio = selected
        .iter()
        .filter(|e| !arr(&e["audio"]).is_empty())
        .count();
    let summary = json!({"notes":selected.len(),"cards":selected.len()*2,"chapters":chapters.len(),"notes_with_audio":with_audio,"audio_files":audio_files,"notes_without_audio":selected.len()-with_audio,"reference_only_entries":arr(&data["entries"]).len()-selected.len()});
    write_json(output.join("summary.json"), &summary, false)?;
    fs::copy(
        root.join("data/vocabulary/README.md"),
        output.join("README.md"),
    )?;
    if site_copy {
        fs::copy(&patched, root.join("docs/assets/decks/malayalam-moag.apkg"))?;
    }
    println!("{} notes; {} cards", selected.len(), selected.len() * 2);
    Ok(summary)
}
fn rewrite_due(input: &Path, output: &Path) -> Result<()> {
    use std::io::{Read, Write};
    let mut zip = zip::ZipArchive::new(fs::File::open(input)?)?;
    let temp = tempfile::tempdir()?;
    let mut out = zip::ZipWriter::new(fs::File::create(output)?);
    for i in 0..zip.len() {
        let mut file = zip.by_index(i)?;
        let mut bytes = vec![];
        file.read_to_end(&mut bytes)?;
        if file.name() == "collection.anki2" {
            let db = temp.path().join("col.anki2");
            fs::write(&db, &bytes)?;
            let conn = rusqlite::Connection::open(&db)?;
            conn.execute_batch(
                "UPDATE cards SET due=(SELECT count(*) FROM notes n WHERE n.id<=cards.nid);",
            )?;
            drop(conn);
            bytes = fs::read(db)?;
        }
        out.start_file(
            file.name(),
            zip::write::FileOptions::default().compression_method(zip::CompressionMethod::Deflated),
        )?;
        out.write_all(&bytes)?;
    }
    out.finish()?;
    Ok(())
}
