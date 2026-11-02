//! Rebuild reviewed recordings from explicit, checksummed cut recipes.
//! Recognition output is evidence; it cannot silently change a published label.
use crate::{util::*, vocabulary::audio_button};
use anyhow::{Result, ensure};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::Path,
    process::Command,
};
use unicode_normalization::UnicodeNormalization;
pub fn key(text: &str) -> String {
    clean(text)
        .nfc()
        .filter(|c| ('\u{d00}'..='\u{d7f}').contains(c))
        .collect()
}
pub fn cut(source: &Path, destination: &Path, start: f64, end: f64, copy: bool) -> Result<()> {
    ensure!(
        start.is_finite() && end.is_finite() && start >= 0. && end > start,
        "invalid audio cut"
    );
    fs::create_dir_all(destination.parent().unwrap())?;
    let mut c = Command::new("ffmpeg");
    c.args(["-hide_banner", "-loglevel", "error", "-y"]);
    if copy {
        c.args(["-ss", &start.to_string()]);
    }
    c.arg("-i").arg(source);
    if !copy {
        c.args(["-ss", &start.to_string()]);
    }
    c.args([
        "-t",
        &(end - start).to_string(),
        "-map_metadata",
        "-1",
        "-codec:a",
        if copy { "copy" } else { "libmp3lame" },
    ]);
    if !copy {
        c.args(["-q:a", "3"]);
    }
    run(c.arg(destination))
}
pub fn speech_spans(path: &Path, noise: f64, pause: f64, minimum: f64) -> Result<Vec<(f64, f64)>> {
    let output = Command::new("ffmpeg")
        .args(["-hide_banner", "-i"])
        .arg(path)
        .args([
            "-af",
            &format!("silencedetect=noise={noise}dB:d={pause}"),
            "-f",
            "null",
            "-",
        ])
        .output()?;
    ensure!(output.status.success(), "silence detector failed");
    let stderr = String::from_utf8_lossy(&output.stderr);
    let duration = String::from_utf8(crate::util::output(
        Command::new("ffprobe")
            .args([
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
            ])
            .arg(path),
    )?)?
    .trim()
    .parse::<f64>()?;
    parse_spans(&stderr, duration, minimum)
}
pub fn parse_spans(stderr: &str, duration: f64, minimum: f64) -> Result<Vec<(f64, f64)>> {
    let mut start = 0.;
    let mut spans = vec![];
    for c in re(r"silence_(start|end): ([\d.]+)").captures_iter(stderr) {
        let point = c[2].parse::<f64>()?;
        if &c[1] == "start" && point - start >= minimum {
            spans.push((start, point));
        } else if &c[1] == "end" {
            start = point;
        }
    }
    if duration - start >= minimum && spans.last().is_none_or(|(_, end)| start > *end) {
        spans.push((start, duration));
    }
    Ok(spans)
}
pub fn strip_columns(text: &str, drop_recorded: bool) -> String {
    table_re()
        .replace_all(text, |m: &regex::Captures| {
            let lines: Vec<_> = m[0].lines().collect();
            if cells(lines[0]).last().is_none_or(|c| c.trim() != "Audio") {
                return m[0].to_string();
            }
            let mut out = String::new();
            for line in lines {
                if drop_recorded && line.contains("<!-- recorded-audio-row -->") {
                    continue;
                }
                let c = cells(line);
                out += &format!("|{}|\n", c[..c.len() - 1].join("|"));
            }
            out
        })
        .into_owned()
}
/// Exact alternatives determine placement; unverified items stay explicitly separate.
pub fn add_columns(text: &str, entries: &[Value], forms: &[Vec<String>]) -> Result<String> {
    let mut assigned = vec![vec![]; forms.len()];
    let mut extra = vec![];
    for e in entries {
        let matches: Vec<_> = forms
            .iter()
            .enumerate()
            .filter(|(_, row)| row.iter().any(|f| key(f) == key(s(&e["transcript"]))))
            .map(|(i, _)| i)
            .collect();
        if e["status"].as_str().unwrap_or("matched") == "matched" && !matches.is_empty() {
            let preferred = e["textbook_row"].as_u64().map(|n| n as usize);
            let i = preferred
                .filter(|i| matches.contains(i))
                .unwrap_or(matches[0]);
            assigned[i].push(e);
        } else {
            extra.push(e);
        }
    }
    let tables: Vec<_> = table_re()
        .find_iter(text)
        .map(|m| (m.start(), m.end()))
        .collect();
    let row_count = tables
        .iter()
        .map(|(a, b)| text[*a..*b].lines().count().saturating_sub(2))
        .sum::<usize>();
    ensure!(
        row_count == forms.len(),
        "audio table rows changed: {row_count} != {}",
        forms.len()
    );
    let mut result = text.to_string();
    let mut row = 0;
    let mut replacements = vec![];
    for (ti, (start, end)) in tables.iter().enumerate() {
        let lines: Vec<_> = text[*start..*end].lines().collect();
        ensure!(lines.len() >= 2, "audio table missing header");
        let mut out = format!(
            "{} Audio |\n{}---|\n",
            lines[0].trim_end(),
            lines[1].trim_end()
        );
        for line in &lines[2..] {
            let controls = assigned[row]
                .iter()
                .map(|e| audio_button(e, e["written_form"].as_str().unwrap_or(&cells(line)[0])))
                .collect::<Vec<_>>()
                .join(" ");
            out += &format!(
                "{} {} |\n",
                line.trim_end(),
                if controls.is_empty() {
                    "<span class=\"audio-unmatched\" title=\"No aligned recording yet\">—</span>"
                } else {
                    &controls
                }
            );
            row += 1;
        }
        if ti + 1 == tables.len() {
            for e in &extra {
                let unplaced = e["label_review"]["placement"] == "unplaced_recorded_form";
                let uncertain = e["status"].as_str().unwrap_or("matched") != "matched";
                let meaning = if unplaced {
                    "Transcribed; placement in the printed tables needs review"
                } else if uncertain {
                    "Audio-to-word match needs review"
                } else {
                    e["meaning"]
                        .as_str()
                        .filter(|m| !m.is_empty())
                        .unwrap_or("Recorded form")
                };
                let written = format!(
                    "{}{}",
                    if unplaced {
                        "Recorded form: "
                    } else if uncertain {
                        "Unconfirmed: "
                    } else {
                        ""
                    },
                    s(&e["transcript"])
                );
                out += &format!(
                    "| <!-- recorded-audio-row --> {} | {} | {} |\n",
                    esc(&written),
                    meaning.replace('|', "&#124;"),
                    audio_button(e, s(&e["transcript"]))
                );
            }
        }
        replacements.push((*start, *end, out));
    }
    for (start, end, out) in replacements.into_iter().rev() {
        result.replace_range(start..end, &out);
    }
    Ok(result)
}
fn panel(n: u64, title: &str, note: &str, clips: &[&Value]) -> String {
    let options=clips.iter().enumerate().map(|(i,c)|{let secs=(c["end"].as_f64().unwrap()-c["start"].as_f64().unwrap())as u64;format!("<button type=\"button\" data-audio-src=\"{}\" aria-pressed=\"{}\">{} · {:02}:{:02}</button>",s(&c["path"]).trim_start_matches("docs/"),i==0,esc(s(&c["label"])),secs/60,secs%60)}).collect::<String>();
    format!(
        "\n<!-- moag-audio -->\n<div class=\"lesson-audio\">\n<p><strong>{}</strong></p>\n<audio controls preload=\"none\" aria-label=\"Lesson {n}: {}\" src=\"{}\"></audio>\n<div class=\"lesson-audio-cues\">{options}</div>\n<p class=\"lesson-audio-note\">{}</p>\n</div>\n<!-- /moag-audio -->\n",
        esc(title),
        esc(title),
        s(&clips[0]["path"]).trim_start_matches("docs/"),
        esc(note)
    )
}
pub fn build(root: &Path, kind: &str, check: bool) -> Result<()> {
    let config = read_json(root.join("data/audio/build.json"))?;
    let recipe = &config[kind];
    ensure!(recipe.is_object(), "unknown audio group {kind}");
    let mut manifest = recipe["manifest"].clone();
    let old = read_json(root.join(s(&recipe["output"])))?;
    let reviewed = read_json(root.join("data/audio/moag/reviewed-vocabulary.json"))?;
    let mut checked = BTreeMap::<String, String>::new();
    let mut paths = BTreeSet::new();
    for clip in manifest["clips"].as_array_mut().unwrap() {
        let path = s(&clip["path"]).to_string();
        ensure!(paths.insert(path.clone()), "duplicate clip path");
        ensure!(
            !Path::new(&path).is_absolute()
                && !Path::new(&path)
                    .components()
                    .any(|c| matches!(c, std::path::Component::ParentDir)),
            "clip path escapes repository"
        );
        let prior = arr(&old["clips"]).iter().find(|c| c["path"] == path);
        let source = s(&clip["source"]).to_string();
        let expected = if !clip["source_sha256"].is_null() {
            s(&clip["source_sha256"]).to_string()
        } else {
            arr(&reviewed["lessons"])
                .iter()
                .find(|r| r["lesson"] == clip["lesson"])
                .map(|r| s(&r["source_sha256"]).to_string())
                .ok_or_else(|| anyhow::anyhow!("source hash missing"))?
        };
        let actual = if let Some(v) = checked.get(&source) {
            v.clone()
        } else {
            let v = digest(inside(root, &source)?)?;
            checked.insert(source.clone(), v.clone());
            v
        };
        ensure!(actual == expected, "original recording changed: {source}");
        let destination = root.join(&path);
        let same_cut = prior.is_some_and(|p| {
            ["start", "end", "lesson", "repair"]
                .iter()
                .all(|k| p[*k] == clip[*k])
                && (kind == "sections" || p["source"] == clip["source"])
        });
        let current_hash = if destination.exists() {
            Some(digest(&destination)?)
        } else {
            None
        };
        let bytes_match = prior.is_some_and(|p| current_hash.as_deref() == p["sha256"].as_str());
        if check {
            ensure!(
                same_cut && bytes_match,
                "clip cut, source or bytes changed: {path}"
            );
        } else if !same_cut || !destination.exists() {
            if let Some(audio) = clip["repair"]["audio"].as_str() {
                let p = inside(root, audio)?;
                ensure!(
                    digest(&p)? == s(&clip["repair"]["audio_sha256"]),
                    "approved audio changed"
                );
                fs::create_dir_all(destination.parent().unwrap())?;
                fs::copy(p, &destination)?;
            } else {
                cut(
                    &root.join(&source),
                    &destination,
                    clip["start"].as_f64().unwrap(),
                    clip["end"].as_f64().unwrap(),
                    kind == "sections",
                )?;
            }
        } else {
            ensure!(bytes_match, "clip bytes changed unexpectedly: {path}");
        }
        clip["sha256"] = json!(if same_cut {
            current_hash.unwrap_or(digest(&destination)?)
        } else {
            digest(&destination)?
        });
        if kind == "sections" {
            clip.as_object_mut().unwrap().remove("source");
            clip.as_object_mut().unwrap().remove("source_sha256");
        }
    }
    for rec in arr(&manifest["recordings"]) {
        let source = inside(root, s(&rec["source"]))?;
        ensure!(
            digest(&source)? == s(&rec["sha256"]),
            "row recording source changed"
        );
        let dest = root.join(s(&rec["path"]));
        if !check {
            fs::create_dir_all(dest.parent().unwrap())?;
            fs::copy(&source, &dest)?;
        }
        ensure!(digest(&dest)? == s(&rec["sha256"]), "row recording changed");
    }
    if kind == "sections" {
        for n in 1..=25 {
            let p = root.join(format!("docs/lesson{n}.md"));
            let original = fs::read_to_string(&p)?;
            let mut text = re(r"(?s)\n<!-- moag-audio -->\n.*?<!-- /moag-audio -->\n")
                .replace_all(&original, "")
                .into_owned();
            for recipe in arr(&recipe["panels"]).iter().filter(|p| p["lesson"] == n) {
                let heading = re(&format!(
                    "(?m)^#{{2,3}} {}\n",
                    regex::escape(s(&recipe["heading"]))
                ));
                let position = heading
                    .find(&text)
                    .ok_or_else(|| anyhow::anyhow!("missing audio heading"))?
                    .end();
                let clips = arr(&recipe["clips"])
                    .iter()
                    .map(|path| {
                        arr(&manifest["clips"])
                            .iter()
                            .find(|c| c["path"] == *path)
                            .ok_or_else(|| anyhow::anyhow!("unknown panel clip"))
                    })
                    .collect::<Result<Vec<_>>>()?;
                text.insert_str(
                    position,
                    &panel(n, s(&recipe["title"]), s(&recipe["note"]), &clips),
                );
            }
            write(p, &text, check)?;
        }
    }
    // Word/letter buttons retain their source-local row positions; validate every
    // association against explicit approved decisions and rewrite metadata in place.
    if kind == "words" {
        word_players(root, &manifest, &reviewed, check)?;
    }
    if kind == "letters" {
        letter_players(root, recipe, &manifest, check)?;
    }
    let clip_count = arr(&manifest["clips"]).len();
    if check {
        ensure!(manifest == old, "audio manifest changed");
    } else {
        write_json(root.join(s(&recipe["output"])), &manifest, false)?;
    }
    println!(
        "{} {kind} clips; {} verified source recordings",
        clip_count,
        checked.len()
    );
    Ok(())
}
fn vocabulary_body(text: &str, heading: &str) -> Result<(usize, usize)> {
    let r = re(&format!("(?m)^(#{{2,3}}) {}\n", regex::escape(heading)));
    let h = r
        .captures(text)
        .ok_or_else(|| anyhow::anyhow!("missing {heading} heading"))?;
    let start = h.get(0).unwrap().end();
    let end = re(&format!("(?m)^#{{1,{}}} ", h[1].len()))
        .find(&text[start..])
        .map(|m| start + m.start())
        .unwrap_or(text.len());
    Ok((start, end))
}
fn alternatives(text: &str) -> Vec<String> {
    let text = re(r"<!--.*?-->").replace_all(text, "");
    let primary = re(r"<br>|\(").split(&text).next().unwrap_or("");
    let mut forms: Vec<_> = re(r",| or | / ")
        .split(primary)
        .map(|f| {
            f.trim_matches(|c: char| c.is_whitespace() || "-*".contains(c))
                .to_string()
        })
        .collect();
    forms.extend(
        re(r"[\u{0d00}-\u{0d7f}]+(?:[ \t]+[\u{0d00}-\u{0d7f}]+)*")
            .find_iter(&text[primary.len()..])
            .map(|m| m.as_str().to_string()),
    );
    forms.retain(|f| !key(f).is_empty());
    forms
}
pub fn word_players(root: &Path, manifest: &Value, reviewed: &Value, check: bool) -> Result<()> {
    for record in arr(&reviewed["lessons"]) {
        let n = record["lesson"].as_u64().unwrap();
        let page = root.join(format!("docs/lesson{n}.md"));
        let original = fs::read_to_string(&page)?;
        let block_re =
            re(r"(?s)\n<!-- moag-vocabulary-words -->\n.*?<!-- /moag-vocabulary-words -->\n");
        let mut text = strip_columns(&block_re.replace_all(&original, ""), true);
        let (start, end) = vocabulary_body(&text, "Vocabulary")?;
        let mut forms: Vec<Vec<String>> = arr(&record["textbook_vocabulary"])
            .iter()
            .map(|r| {
                let mut f = vec![s(&r["malayalam"]).to_string()];
                f.extend(alternatives(s(&r["malayalam"])));
                f
            })
            .collect();
        let mut entries = vec![];
        let mut reference = vec![];
        for word in arr(&record["words"]) {
            let id = s(&word["id"]);
            let clip = arr(&manifest["clips"])
                .iter()
                .find(|c| {
                    Path::new(s(&c["path"]))
                        .file_stem()
                        .is_some_and(|s| s == id)
                })
                .ok_or_else(|| anyhow::anyhow!("missing reviewed clip {id}"))?;
            let mut entry = clip.clone();
            entry["textbook_row"] = word["textbook_row"].clone();
            if word["label_review"]["placement"] == "vocabulary" {
                let i = word["textbook_row"]
                    .as_u64()
                    .ok_or_else(|| anyhow::anyhow!("reviewed placement missing row"))?
                    as usize;
                ensure!(i < forms.len(), "reviewed row missing");
                forms[i].push(s(&entry["transcript"]).to_string());
            }
            if word["reference_entry"] == true {
                entry["written_form"] = entry["transcript"].clone();
                reference.push(entry);
            } else {
                entries.push(entry);
            }
        }
        let body = add_columns(&text[start..end], &entries, &forms)?;
        text.replace_range(start..end, &body);
        let block = format!(
            "\n<!-- moag-vocabulary-words -->\n<div class=\"lesson-audio\">\n<p><strong>Selected vocabulary recording</strong></p>\n<audio data-table-audio-player controls preload=\"none\" aria-label=\"Lesson {n}: select a word in the vocabulary table\"></audio>\n<p class=\"lesson-audio-note\">Use the Audio column to hear a word. Recorded variants appear beside their written entry; additional recorded forms are included in the same table. Unconfirmed recordings stay in rows marked “check match” until their word is verified. A dash means no aligned recording yet.</p>\n</div>\n<!-- /moag-vocabulary-words -->\n"
        );
        let existing = re(r"(?s)^\n<!-- moag-audio -->\n.*?<!-- /moag-audio -->\n")
            .find(&text[start..])
            .map(|m| m.end())
            .unwrap_or(0);
        text.insert_str(start + existing, &block);
        if !reference.is_empty() {
            let (start, end) = vocabulary_body(&text, "Reference List")?;
            let mut forms = vec![];
            for t in table_re().find_iter(&text[start..end]) {
                for line in t.as_str().lines().skip(2) {
                    let c = cells(line);
                    forms.push(if c.len() == 4 {
                        vec![c[2].trim().to_string()]
                    } else {
                        vec![]
                    });
                }
            }
            let body = add_columns(&text[start..end], &reference, &forms)?;
            text.replace_range(start..end, &body);
        }
        write(page, &text, check)?;
    }
    let mut w = csv::WriterBuilder::new()
        .terminator(csv::Terminator::Any(b'\n'))
        .from_writer(vec![]);
    w.write_record([
        "lesson",
        "transcript",
        "meaning",
        "status",
        "start_seconds",
        "end_seconds",
        "clip",
    ])?;
    for c in arr(&manifest["clips"]) {
        w.write_record([
            c["lesson"].to_string(),
            s(&c["transcript"]).into(),
            s(&c["meaning"]).into(),
            s(&c["status"]).into(),
            c["start"].to_string(),
            c["end"].to_string(),
            s(&c["path"]).into(),
        ])?;
    }
    for lesson in arr(&manifest["lessons"]) {
        for e in arr(&lesson["printed_entries_without_match"]) {
            w.write_record([
                lesson["lesson"].to_string(),
                s(&e["malayalam"]).into(),
                s(&e["meaning"]).into(),
                "not_aligned".into(),
                String::new(),
                String::new(),
                String::new(),
            ])?;
        }
    }
    write(
        root.join("data/audio/moag/vocabulary-transcripts.csv"),
        &String::from_utf8(w.into_inner()?)?,
        check,
    )?;
    Ok(())
}
pub fn letter_players(root: &Path, recipe: &Value, manifest: &Value, check: bool) -> Result<()> {
    let page = root.join("docs/alphabet.md");
    let original = fs::read_to_string(&page)?;
    let mut text = strip_columns(
        &re(r"(?s)\n<!-- letter-audio -->\n.*?<!-- /letter-audio -->\n\n")
            .replace_all(&original, ""),
        true,
    );
    let mut forms = vec![];
    for t in table_re().find_iter(&text) {
        for line in t.as_str().lines().skip(2) {
            forms.push(vec![cells(line)[0].clone()]);
        }
    }
    let clips: Vec<_> = arr(&manifest["clips"])
        .iter()
        .map(|c| {
            let mut c = c.clone();
            c["transcript"] = c["symbol"].clone();
            c["status"] = json!("matched");
            c
        })
        .collect();
    text = add_columns(&text, &clips, &forms)?;
    let mut blocks = vec![];
    for group in arr(&recipe["groups"]) {
        let key = s(&group["id"]);
        let title = s(&group["title"]);
        blocks.push(format!("<div class=\"lesson-audio\">\n<p><strong>{title}</strong></p>\n<audio controls preload=\"none\" aria-label=\"{title}: full row or selected letter\" src=\"assets/ut-austin/letters/{key}.mp3\"></audio>\n<div class=\"lesson-audio-cues\"><button type=\"button\" data-audio-src=\"assets/ut-austin/letters/{key}.mp3\" aria-pressed=\"true\">Full row</button></div>\n</div>"));
    }
    let block = format!(
        "\n<!-- letter-audio -->\n<a id=\"letter-audio\"></a>\n<a id=\"alphabet-listen-to-the-alphabet-and-individual-letters\"></a><!-- reading-anchor -->\n### Listen to the Alphabet and Individual Letters\n\nUse the Audio column beside each letter below. Consonants include the inherent vowel. The full alphabet and row recitations are also available.\n\n<div class=\"lesson-audio\">\n<p><strong>Complete alphabet recitation</strong></p>\n<audio data-table-audio-player controls preload=\"none\" aria-label=\"Complete Malayalam alphabet recitation\" src=\"assets/ut-austin/alphabet.mp3\"></audio>\n<div class=\"lesson-audio-cues\"><button type=\"button\" data-audio-src=\"assets/ut-austin/alphabet.mp3\" aria-pressed=\"true\">Full alphabet</button></div>\n</div>\n\n<details><summary>Full vowel and consonant row recitations</summary>\n\n{}\n</details>\n\nRecordings: [UT Austin, Malayalam Pronunciation: The Basics](https://malayalam.la.utexas.edu/resources/pronunciation-the-basics/), shared under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Individual clips are excerpts; full row recordings are unchanged. [Recording provenance and clip times](assets/ut-austin/letters/manifest.json).\n<!-- /letter-audio -->\n",
        blocks.join("\n\n")
    );
    ensure!(
        text.contains("**Vowels:**"),
        "alphabet table insertion point missing"
    );
    text = text.replacen("**Vowels:**", &(block + "\n**Vowels:**"), 1);
    write(page, &text, check)
}
