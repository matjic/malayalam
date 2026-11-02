//! Source-local table contracts and stable published vocabulary identities.
use crate::util::*;
use anyhow::{Result, ensure};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::Path,
};

const CASES: [&str; 7] = [
    "Nominative",
    "Possessive",
    "Dative",
    "Accusative",
    "Addressive",
    "Locative",
    "Instrumental",
];
#[derive(Debug, Clone)]
pub struct Table {
    pub options: Value,
    pub headers: Vec<String>,
    pub rows: Vec<Vec<String>>,
    pub anchor: String,
}
#[derive(Debug, Clone)]
pub struct Word {
    pub word: String,
    pub meaning: String,
    pub variants: Vec<String>,
    pub notes: Vec<String>,
    pub study: bool,
    pub raw: String,
}

pub fn tables(text: &str, source: &str) -> Result<Vec<Table>> {
    let marker = re(r"(?s)<!--\s*vocabulary-table:\s*(.*?)\s*-->");
    ensure!(
        re(r"<!--\s*vocabulary-table\b").find_iter(text).count() == marker.find_iter(text).count(),
        "{source}: malformed table marker"
    );
    let mut result = vec![];
    let mut groups: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for m in marker.captures_iter(text) {
        let mut o: Value = serde_json::from_str(&m[1])?;
        let allowed = [
            "kind", "category", "cards", "word", "meaning", "aliases", "case", "group", "chapter",
            "origin",
        ];
        ensure!(
            o.is_object()
                && o.as_object()
                    .unwrap()
                    .keys()
                    .all(|k| allowed.contains(&k.as_str())),
            "{source}: invalid table contract"
        );
        ensure!(
            ["vocabulary", "reference", "paradigm"].contains(&s(&o["kind"]))
                && !s(&o["category"]).trim().is_empty(),
            "{source}: invalid table kind/category"
        );
        let c = &o["cards"];
        ensure!(
            c.is_boolean()
                || (c.is_array()
                    && !arr(c).is_empty()
                    && arr(c)
                        .iter()
                        .all(|v| v.is_string() && !s(v).trim().is_empty())),
            "{source}: invalid cards selection"
        );
        ensure!(
            o["kind"] == "vocabulary" || c == false,
            "{source}: reference/paradigm cannot generate cards"
        );
        ensure!(
            o["aliases"].is_null() || o["aliases"] == "br",
            "{source}: unsupported aliases"
        );
        ensure!(
            o["origin"].is_null() || ["textbook", "reference_table"].contains(&s(&o["origin"])),
            "{source}: invalid origin"
        );
        for f in ["word", "meaning"] {
            ensure!(
                o[f].is_null() || !s(&o[f]).trim().is_empty(),
                "{source}: invalid column name"
            );
        }
        if !o["chapter"].is_null() {
            ensure!(
                o["chapter"].as_u64().is_some_and(|n| (1..=25).contains(&n)),
                "{source}: invalid chapter"
            );
        }
        if !o["case"].is_null() {
            let case = s(&o["case"]).to_lowercase();
            ensure!(
                CASES.iter().any(|x| x.to_lowercase() == case) || case == "associative",
                "{source}: unknown case"
            );
            o["case"] = json!(case);
        }
        let rest = text[m.get(0).unwrap().end()..].trim_start();
        let t = table_re()
            .find(rest)
            .filter(|v| v.start() == 0)
            .ok_or_else(|| anyhow::anyhow!("{source}: marker must immediately precede table"))?;
        let raw: Vec<_> = t.as_str().lines().map(cells).collect();
        ensure!(
            raw.len() >= 3 && raw[1].iter().all(|c| re(r"^\s*:?-{3,}:?\s*$").is_match(c)),
            "{source}: invalid table header/separator"
        );
        let headers: Vec<_> = raw[0].iter().map(|x| clean(x)).collect();
        ensure!(
            headers.iter().all(|h| !h.is_empty())
                && headers.iter().collect::<BTreeSet<_>>().len() == headers.len(),
            "{source}: empty or repeated headers"
        );
        ensure!(
            raw[2..].iter().all(|r| r.len() == headers.len()),
            "{source}: inconsistent table columns"
        );
        let before = &text[..m.get(0).unwrap().start()];
        let anchor = re(r#"<a id="([^"]+)"></a>"#)
            .captures_iter(before)
            .last()
            .map(|c| c[1].to_string())
            .ok_or_else(|| anyhow::anyhow!("{source}: table needs anchor"))?;
        let table = Table {
            options: o,
            headers,
            rows: raw[2..].to_vec(),
            anchor,
        };
        if table.options["kind"] == "vocabulary" {
            words(&table)?;
        } else {
            ensure!(
                table.rows.iter().flatten().all(|c| !clean(c).is_empty()),
                "{source}: empty reference cell"
            );
            if table.options["kind"] == "paradigm" {
                ensure!(
                    table.headers[0] == "Case" && !s(&table.options["group"]).is_empty(),
                    "{source}: invalid paradigm"
                );
                groups
                    .entry(s(&table.options["group"]).into())
                    .or_default()
                    .extend(table.rows.iter().map(|r| clean(&r[0])));
            }
        }
        result.push(table);
    }
    for (g, found) in groups {
        ensure!(
            found.len() == 7
                && found.iter().map(String::as_str).collect::<BTreeSet<_>>()
                    == CASES.into_iter().collect(),
            "{source}: paradigm {g} needs each of seven cases once"
        );
    }
    Ok(result)
}
pub fn words(t: &Table) -> Result<Vec<Word>> {
    let column = |key: &str, default: &str| -> Result<usize> {
        let name = t.options[key].as_str().unwrap_or(default);
        t.headers
            .iter()
            .position(|h| h == name)
            .ok_or_else(|| anyhow::anyhow!("missing column {name}"))
    };
    let w = column("word", "Malayalam")?;
    let e = column("meaning", "English")?;
    let mut result = vec![];
    let mut available = BTreeSet::new();
    for row in &t.rows {
        let raw = row.join("|");
        let exclusions: Vec<_> = re(r"(?s)<!--\s*vocabulary-exclude:\s*(.*?)\s*-->")
            .captures_iter(&raw)
            .map(|c| c[1].to_string())
            .collect();
        if !exclusions.is_empty() {
            ensure!(
                exclusions.len() == 1 && !exclusions[0].trim().is_empty(),
                "excluded row needs one reason"
            );
            continue;
        }
        let mut meaning = clean(&row[e]);
        ensure!(
            !meaning.is_empty() && !re(r"(?i)^\(?\s*(?:n|adj|adv|v)\.?\s*\)?$").is_match(&meaning),
            "incomplete vocabulary meaning"
        );
        let mut notes = vec![];
        let mut forms = vec![];
        if t.options["aliases"] == "br" {
            notes = re(r"\[([^]]+)\]")
                .captures_iter(&clean(&row[w]))
                .map(|c| c[1].into())
                .collect();
            let raw_word = re(r"(?s)<!--.*?-->|\[[^]]*\]").replace_all(&row[w], "");
            for f in re(r"<br\s*/?>").split(&raw_word) {
                let f = clean(f).trim_start_matches('*').trim().to_string();
                if !f.is_empty() && !forms.contains(&f) {
                    forms.push(f);
                }
            }
            if let Some(first) = forms.first_mut()
                && let Some(c) = re(r"\s+(\([^)]*\))$").captures(first)
            {
                meaning.push(' ');
                meaning.push_str(&c[1]);
                *first = first[..c.get(0).unwrap().start()].trim_end().into();
            }
        } else {
            forms.push(clean(&row[w]));
        }
        ensure!(
            !forms.is_empty() && forms.iter().all(|f| ml(f)),
            "vocabulary needs Malayalam forms"
        );
        available.extend(forms.clone());
        let study = t.options["cards"].as_bool().unwrap_or_else(|| {
            arr(&t.options["cards"])
                .iter()
                .any(|v| forms.iter().any(|f| f == s(v)))
        });
        result.push(Word {
            word: forms[0].clone(),
            meaning,
            variants: forms[1..].to_vec(),
            notes,
            study,
            raw,
        });
    }
    for selected in arr(&t.options["cards"]) {
        ensure!(
            available.contains(s(selected)),
            "selected practice form disappeared: {selected}"
        );
    }
    Ok(result)
}
fn id(n: u64, kind: &str, word: &str, meaning: &str) -> String {
    format!(
        "moag-{n:02}-{}",
        &hash(format!("{n}\0{kind}{word}\0{meaning}"))[..16]
    )
}
fn append(entry: &mut Value, key: &str, values: &[Value]) {
    if values.is_empty() {
        return;
    }
    if entry[key].is_null() {
        entry[key] = json!([]);
    }
    let a = entry[key].as_array_mut().unwrap();
    for v in values {
        if !a.contains(v) {
            a.push(v.clone());
        }
    }
}
pub fn preserve_ids(entries: &mut [Value], old: &[Value]) -> Result<()> {
    let mut pending: BTreeSet<_> = (0..entries.len()).collect();
    let mut used = BTreeSet::new();
    for fields in [
        &["malayalam", "english"][..],
        &["malayalam", "source_anchor"],
        &["malayalam"],
        &["english"],
    ] {
        for i in pending.clone() {
            if fields.iter().any(|f| entries[i][*f].is_null()) {
                continue;
            }
            let matches = |v: &Value| {
                v["chapter"] == entries[i]["chapter"]
                    && fields.iter().all(|f| v[*f] == entries[i][*f])
            };
            let candidates: Vec<_> = old
                .iter()
                .filter(|v| !used.contains(s(&v["id"])) && matches(v))
                .collect();
            let competing = pending.iter().filter(|j| matches(&entries[**j])).count();
            if candidates.len() == 1 && competing == 1 {
                entries[i]["id"] = candidates[0]["id"].clone();
                used.insert(s(&entries[i]["id"]).to_string());
                pending.remove(&i);
            }
        }
    }
    for i in pending {
        ensure!(
            !old.iter().any(|v| v["id"] == entries[i]["id"]),
            "ambiguous vocabulary identity: {}",
            entries[i]["id"]
        );
    }
    ensure!(
        entries
            .iter()
            .map(|v| s(&v["id"]))
            .collect::<BTreeSet<_>>()
            .len()
            == entries.len(),
        "duplicate entry ID"
    );
    Ok(())
}

/// Original source identities survive consolidation, including their audio and glosses.
pub fn occurrences(entry: &Value) -> Vec<&Value> {
    if entry["occurrences"].is_array() {
        arr(&entry["occurrences"]).iter().collect()
    } else {
        vec![entry]
    }
}

pub fn word_key(word: &str) -> String {
    use unicode_normalization::UnicodeNormalization;
    word.split(" (")
        .next()
        .unwrap_or(word)
        .trim()
        .nfc()
        .collect()
}

/// Only an explicit, source-bound editorial decision may merge different glosses.
pub fn consolidate(entries: Vec<Value>, review: &Value) -> Result<Vec<Value>> {
    ensure!(
        review["words"].is_array(),
        "missing vocabulary duplicate review"
    );
    let by_id: BTreeMap<_, _> = entries.iter().map(|e| (s(&e["id"]), e)).collect();
    ensure!(by_id.len() == entries.len(), "duplicate source identity");
    let mut decisions = BTreeMap::new();
    let mut covered = BTreeSet::new();
    for word in arr(&review["words"]) {
        let key = s(&word["word"]);
        ensure!(
            !key.is_empty() && word["groups"].is_array(),
            "invalid duplicate review"
        );
        for group in arr(&word["groups"]) {
            ensure!(
                !s(&group["reason"]).trim().is_empty(),
                "missing merge rationale: {key}"
            );
            let members = arr(&group["members"]);
            ensure!(!members.is_empty(), "empty duplicate group: {key}");
            let canonical = s(&members[0]["id"]);
            let mut merged = (*by_id
                .get(canonical)
                .ok_or_else(|| anyhow::anyhow!("unknown canonical ID: {canonical}"))?)
            .clone();
            let mut originals = vec![];
            for member in members {
                let id = s(&member["id"]);
                let e = by_id
                    .get(id)
                    .ok_or_else(|| anyhow::anyhow!("unknown reviewed ID: {id}"))?;
                ensure!(covered.insert(id), "repeated review membership: {id}");
                ensure!(
                    word_key(s(&e["malayalam"])) == key && e["english"] == member["english"],
                    "stale duplicate review: {id}"
                );
                originals.push((*e).clone());
                for field in ["audio", "variants", "notes", "references"] {
                    append(&mut merged, field, arr(&e[field]));
                }
            }
            // Introduce a shared note with its earliest selected occurrence.
            let first = originals
                .iter()
                .filter(|e| e["study"] != false)
                .min_by_key(|e| e["chapter"].as_u64().unwrap());
            if let Some(first) = first {
                merged["chapter"] = first["chapter"].clone();
                merged["study"] = json!(true);
            } else {
                merged["study"] = json!(false);
            }
            if !group["cue"].is_null() {
                ensure!(
                    !s(&group["cue"]).trim().is_empty(),
                    "empty sense cue: {key}"
                );
                merged["sense"] = group["cue"].clone();
            }
            if !group["meaning"].is_null() {
                ensure!(
                    !s(&group["meaning"]).trim().is_empty(),
                    "empty consolidated meaning: {key}"
                );
                merged["english"] = group["meaning"].clone();
            }
            if originals.len() > 1 {
                merged["occurrences"] = json!(originals);
            }
            ensure!(
                decisions.insert(canonical, merged).is_none(),
                "duplicate canonical ID"
            );
        }
    }
    let mut words: BTreeMap<String, Vec<&Value>> = BTreeMap::new();
    for e in &entries {
        words
            .entry(word_key(s(&e["malayalam"])))
            .or_default()
            .push(e);
    }
    for (word, group) in words {
        if group.len() > 1 {
            ensure!(
                group.iter().all(|e| covered.contains(s(&e["id"]))),
                "unreviewed repeated word: {word}"
            );
        }
    }
    let mut result = vec![];
    for entry in entries {
        let id = s(&entry["id"]);
        if let Some(merged) = decisions.remove(id) {
            result.push(merged);
        } else if !covered.contains(id) {
            result.push(entry);
        }
    }
    Ok(result)
}
pub fn catalog(root: &Path) -> Result<Value> {
    let manifest = read_json(root.join("docs/assets/audio/moag/words/manifest.json"))?;
    let audio: BTreeMap<_, _> = arr(&manifest["clips"])
        .iter()
        .map(|c| (s(&c["path"]).trim_start_matches("docs/").to_string(), c))
        .collect();
    let mut chapters = vec![];
    let mut entries: Vec<Value> = vec![];
    let mut seen = BTreeSet::new();
    let mut references = vec![];
    for n in 1..=25u64 {
        let source = format!("docs/lesson{n}.md");
        let text = fs::read_to_string(root.join(&source))?;
        let title = re(r"(?m)^# (.+)$").captures(&text).unwrap()[1].to_string();
        chapters.push(json!({"number":n,"title":title,"source":source}));
        let mut identities = BTreeMap::new();
        for t in tables(&text, &source)? {
            if t.options["kind"] != "vocabulary" {
                continue;
            }
            if t.options["origin"] == "reference_table" {
                references.push((n, source.clone(), t));
                continue;
            }
            for row in words(&t)? {
                let key = (row.word.clone(), row.meaning.clone());
                let i = *identities.entry(key).or_insert_with(|| {
                    let origin = if row.raw.contains("<!-- recorded-audio-row -->") {
                        "recorded_addition"
                    } else { "textbook" };
                    let mut entry = json!({"id":id(n,"",&row.word,&row.meaning),"chapter":n,"malayalam":row.word,"english":row.meaning,"origin":origin,"source":source,"audio":[]});
                    if !row.study { entry["study"] = json!(false); }
                    if t.options["category"] != "vocabulary" {
                        entry["category"] = t.options["category"].clone();
                    }
                    if !row.variants.is_empty() { entry["variants"] = json!(row.variants); }
                    if !row.notes.is_empty() { entry["notes"] = json!(row.notes); }
                    entries.push(entry);
                    entries.len()-1
                });
                for c in re(r#"data-row-audio-src="([^"]+)""#).captures_iter(&row.raw) {
                    let path = &c[1];
                    let clip = audio
                        .get(path)
                        .ok_or_else(|| anyhow::anyhow!("unknown audio {path}"))?;
                    ensure!(clip["status"] == "matched", "unverified clip {path}");
                    if seen.insert(path.to_string()) {
                        entries[i]["audio"].as_array_mut().unwrap().push(json!({"path":format!("docs/{path}"),"transcript":clip["transcript"],"sha256":clip["sha256"]}));
                    }
                }
            }
        }
        for (path, c) in &audio {
            if c["lesson"] != n || seen.contains(path) {
                continue;
            }
            ensure!(
                n == 24
                    && c["transcript"] == "സ്നേഹം"
                    && text.contains(&format!("data-row-audio-src=\"{path}\"")),
                "recording lost source placement: {path}"
            );
            entries.push(json!({"id":id(n,"reference\0",s(&c["transcript"]),s(&c["meaning"])),"chapter":n,"malayalam":c["transcript"],"english":c["meaning"],"origin":"reference_list","source":source,"audio":[{"path":format!("docs/{path}"),"transcript":c["transcript"],"sha256":c["sha256"]}]}));
            seen.insert(path.clone());
        }
    }
    let mut appendices: Vec<_> = fs::read_dir(root.join("docs"))?
        .filter_map(Result::ok)
        .map(|e| e.path())
        .filter(|p| {
            p.file_name()
                .unwrap()
                .to_string_lossy()
                .starts_with("appendix-")
                && p.extension().is_some_and(|e| e == "md")
        })
        .collect();
    appendices.sort();
    for p in appendices {
        let source = format!("docs/{}", p.file_name().unwrap().to_string_lossy());
        for t in tables(&fs::read_to_string(p)?, &source)? {
            if t.options["kind"] == "vocabulary" {
                let n = t.options["chapter"]
                    .as_u64()
                    .filter(|n| (1..=25).contains(n))
                    .ok_or_else(|| anyhow::anyhow!("appendix table needs chapter"))?;
                references.push((n, source.clone(), t));
            }
        }
    }
    let published = entries.len();
    for (n, source, t) in references {
        for mut row in words(&t)? {
            if let Some(i) = t.headers.iter().position(|h| h == "Type") {
                row.meaning += if clean(row.raw.split('|').collect::<Vec<_>>()[i]) == "Adjectives" {
                    " (adjective)"
                } else {
                    " (pronoun)"
                };
            }
            if let Some(case) = t.options["case"].as_str() {
                row.meaning += &format!(
                    " (postposition; after a {case} noun{})",
                    if case == "possessive" && !row.raw.contains("\\*") {
                        "; also dative in colloquial speech"
                    } else {
                        ""
                    }
                );
            }
            let mut matches: Vec<_> = entries
                .iter()
                .enumerate()
                .filter(|(_, v)| {
                    v["chapter"] == n && v["malayalam"] == row.word && v["english"] == row.meaning
                })
                .map(|(i, _)| i)
                .collect();
            if matches.is_empty()
                && !["postposition", "demonstrative"].contains(&s(&t.options["category"]))
            {
                matches = entries[..published]
                    .iter()
                    .enumerate()
                    .filter(|(_, v)| v["chapter"] == n && v["malayalam"] == row.word)
                    .map(|(i, _)| i)
                    .collect();
            }
            let i = if matches.len() == 1 {
                let i = matches[0];
                if entries[i]["study"] == false && row.study {
                    entries[i]["study"] = json!(true);
                }
                append(&mut entries[i], "variants", arr(&json!(row.variants)));
                append(&mut entries[i], "notes", arr(&json!(row.notes)));
                i
            } else {
                let mut e = json!({"id":id(n,"reference-table\0",&row.word,&row.meaning),"chapter":n,"malayalam":row.word,"english":row.meaning,"origin":"reference_table","source":source,"source_anchor":t.anchor,"category":t.options["category"],"study":row.study,"audio":[]});
                if !row.variants.is_empty() {
                    e["variants"] = json!(row.variants);
                }
                if !row.notes.is_empty() {
                    e["notes"] = json!(row.notes);
                }
                entries.push(e);
                entries.len() - 1
            };
            append(
                &mut entries[i],
                "references",
                &[json!({"source":source,"anchor":t.anchor,"category":t.options["category"]})],
            );
        }
    }
    ensure!(seen.len() == audio.len(), "audio omitted from catalog");
    let old = read_json(root.join("data/vocabulary/moag.json"))?;
    let old: Vec<_> = arr(&old["entries"])
        .iter()
        .flat_map(occurrences)
        .cloned()
        .collect();
    preserve_ids(&mut entries, &old)?;
    let review = read_json(root.join("data/vocabulary/duplicates.json"))?;
    let entries = consolidate(entries, &review)?;
    Ok(
        json!({"schema_version":1,"title":"Malayalam — Moag","license":"CC-BY-NC-SA-4.0","source_of_truth":"Explicit vocabulary-table comments in lesson and appendix Markdown; reviewed sense consolidation in data/vocabulary/duplicates.json; audio paths and checksums from the word manifest.","chapters":chapters,"entries":entries}),
    )
}
pub fn build(root: &Path, check: bool) -> Result<()> {
    let data = catalog(root)?;
    write_json(root.join("data/vocabulary/moag.json"), &data, check)?;
    let mut report = csv::WriterBuilder::new()
        .delimiter(b'\t')
        .from_writer(vec![]);
    report.write_record([
        "RetiredEntryID",
        "CanonicalEntryID",
        "Malayalam",
        "OriginalMeaning",
        "AnkiSearch",
    ])?;
    for entry in arr(&data["entries"]) {
        for original in occurrences(entry) {
            if original["id"] != entry["id"] && original["study"] != false {
                report.write_record([
                    s(&original["id"]),
                    s(&entry["id"]),
                    s(&original["malayalam"]),
                    s(&original["english"]),
                    &format!("EntryID:{}", s(&original["id"])),
                ])?;
            }
        }
    }
    write(
        root.join("data/vocabulary/merged-notes.tsv"),
        &String::from_utf8(report.into_inner()?)?,
        check,
    )?;
    println!("{} vocabulary entries", arr(&data["entries"]).len());
    Ok(())
}

pub fn audio_button(clip: &Value, written: &str) -> String {
    use unicode_normalization::UnicodeNormalization;
    let key = |t: &str| {
        clean(t)
            .nfc()
            .filter(|c| ('\u{d00}'..='\u{d7f}').contains(c))
            .collect::<String>()
    };
    let label = s(&clip["transcript"]);
    let unplaced = clip["label_review"]["placement"] == "unplaced_recorded_form";
    let review = if clip["status"].as_str().unwrap_or("matched") != "matched" {
        if unplaced {
            " · check placement"
        } else {
            " · check match"
        }
    } else {
        ""
    };
    let primary = re(r"<br\s*/?>|\(").split(written).next().unwrap_or("");
    let variant = if key(primary) != key(label) {
        format!(" <span lang=\"ml\">{}</span>", esc(label))
    } else {
        String::new()
    };
    format!(
        "<button type=\"button\" class=\"row-audio-button\" data-row-audio-src=\"{}\" data-audio-label=\"{}\" aria-label=\"Play {}{review}\" title=\"Play {}{review}\" aria-pressed=\"false\">▶{variant}{review}</button>",
        esc(s(&clip["path"]).trim_start_matches("docs/")),
        esc(label),
        esc(label),
        esc(label)
    )
}

pub fn glossary(root: &Path, check: bool) -> Result<()> {
    let data = read_json(root.join("data/vocabulary/moag.json"))?;
    #[derive(Default)]
    struct Group {
        audio: Vec<Value>,
        sources: BTreeSet<(u64, String, String)>,
        variants: BTreeSet<String>,
    }
    let mut groups: BTreeMap<(String, String), Group> = BTreeMap::new();
    for e in arr(&data["entries"]) {
        let g = groups
            .entry((s(&e["malayalam"]).into(), s(&e["english"]).into()))
            .or_default();
        g.audio.extend_from_slice(arr(&e["audio"]));
        for original in occurrences(e) {
            let n = original["chapter"].as_u64().unwrap();
            g.sources.insert((
                n,
                s(&original["source"]).into(),
                original["source_anchor"]
                    .as_str()
                    .map(str::to_string)
                    .unwrap_or_else(|| format!("lesson{n}-vocabulary")),
            ));
            for reference in arr(&original["references"]) {
                g.sources.insert((
                    n,
                    s(&reference["source"]).into(),
                    s(&reference["anchor"]).into(),
                ));
            }
        }
        g.variants
            .extend(arr(&e["variants"]).iter().map(|v| s(v).to_string()));
    }
    let mut letters: BTreeMap<char, Vec<_>> = BTreeMap::new();
    for ((w, m), g) in groups.iter() {
        let letter = w
            .chars()
            .find(|c| matches!(c,'\u{d05}'..='\u{d3a}'|'\u{d7a}'..='\u{d7f}'))
            .unwrap_or('O');
        letters.entry(letter).or_default().push((w, m, g));
    }
    let count = groups.len();
    let mut out = format!(
        "<!-- Generated by cargo run -- glossary; edit lesson tables and rebuild the vocabulary catalog. -->\n# Vocabulary Glossary\n\nBrowse {count} word-and-meaning entries from all 25 lessons and selected reference tables. The glossary includes reference-only entries as well as the forms selected for Anki. Repeated entries are combined; different meanings remain separate.\n\nThis generated vocabulary index complements the [original textbook glossary](glossary.md). Lesson links open the vocabulary tables. A dash in the Audio column means no recording is available.\n\n<div class=\"vocabulary-glossary-controls\">\n<label for=\"vocabulary-query\">Search Malayalam or English</label>\n<input id=\"vocabulary-query\" type=\"search\" placeholder=\"Word or meaning…\" autocomplete=\"off\">\n<label for=\"vocabulary-chapter\">Lesson</label>\n<select id=\"vocabulary-chapter\"><option value=\"\">All lessons</option>"
    );
    for n in 1..=25 {
        out += &format!("<option value=\"{n}\">Lesson {n:02}</option>");
    }
    out += &format!(
        "</select>\n<p id=\"vocabulary-count\" role=\"status\" aria-live=\"polite\">{count} entries</p>\n</div>\n\n<div class=\"lesson-audio\"><p><strong>Selected vocabulary recording</strong></p><audio data-table-audio-player controls preload=\"none\" aria-label=\"Select a glossary recording\"></audio></div>\n\nJump to a letter: "
    );
    out += &letters
        .keys()
        .map(|l| format!("[{l}](#vocabulary-letter-{:x})", *l as u32))
        .collect::<Vec<_>>()
        .join(" · ");
    out += "\n\n";
    for (letter, rows) in letters {
        out += &format!(
            "<a id=\"vocabulary-letter-{:x}\"></a>\n## {letter}\n\n| Malayalam | English | Lessons / Sources | Audio |\n|---|---|---|---|\n",
            letter as u32
        );
        for (word, meaning, g) in rows {
            let links = g
                .sources
                .iter()
                .map(|(n, source, anchor)| {
                    let name = Path::new(source).file_name().unwrap().to_string_lossy();
                    let label = if name.starts_with("appendix-") {
                        format!("Appendix {}", name.chars().nth(9).unwrap().to_uppercase())
                    } else {
                        n.to_string()
                    };
                    format!(
                        "<a href=\"{name}#{anchor}\" data-vocabulary-chapter=\"{n}\">{label}</a>"
                    )
                })
                .collect::<Vec<_>>()
                .join(" · ");
            let controls = g
                .audio
                .iter()
                .map(|c| audio_button(c, word))
                .collect::<Vec<_>>()
                .join(" ");
            let display = std::iter::once(word.as_str())
                .chain(g.variants.iter().map(String::as_str))
                .map(|w| esc(w).replace('|', "&#124;"))
                .collect::<Vec<_>>()
                .join("<br>");
            out += &format!(
                "| {display} | {} | {links} | {} |\n",
                esc(meaning).replace('|', "&#124;"),
                if controls.is_empty() {
                    "—"
                } else {
                    &controls
                }
            );
        }
        out += '\n'.to_string().as_str();
    }
    write(
        root.join("docs/vocabulary-glossary.md"),
        &(out.trim_end().to_string() + "\n"),
        check,
    )
}
