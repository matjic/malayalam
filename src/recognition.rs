//! Optional native Whisper evidence generation. Publishing never trusts ASR labels.
use crate::util::*;
use anyhow::{Result, ensure};
use serde_json::json;
use std::{fs, path::Path, process::Command};
pub fn transcribe(
    input: &Path,
    model: &Path,
    output: &Path,
    executable: &str,
    language: &str,
) -> Result<()> {
    ensure!(
        input.is_file() && model.is_file(),
        "input and native Whisper model files are required"
    );
    let temp = tempfile::tempdir()?;
    let wav = temp.path().join("input.wav");
    run(Command::new("ffmpeg")
        .args(["-v", "error", "-y", "-i"])
        .arg(input)
        .args(["-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le"])
        .arg(&wav))?;
    let prefix = temp.path().join("recognition");
    run(Command::new(executable)
        .arg("-m")
        .arg(model)
        .arg("-f")
        .arg(wav)
        .args(["-l", language, "-ojf", "-of"])
        .arg(&prefix))?;
    let evidence = read_json(prefix.with_extension("json"))?;
    let report = json!({"schema_version":1,"engine":"whisper.cpp","source":input.to_string_lossy(),"source_sha256":digest(input)?,"model":model.file_name().unwrap().to_string_lossy(),"model_sha256":digest(model)?,"language":language,"evidence":evidence,"review_status":"unreviewed"});
    write_json(output, &report, false)?;
    Ok(())
}
pub fn review(root: &Path, output: &Path) -> Result<()> {
    let data = read_json(root.join("docs/assets/audio/moag/words/manifest.json"))?;
    let mut html="<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width\"><title>Vocabulary audio review</title><style>body{font-family:system-ui;max-width:70rem;margin:auto;padding:2rem}td,th{text-align:left;padding:.5rem}audio{max-width:18rem}textarea{width:100%;min-height:4rem}</style><h1>Vocabulary audio review</h1><p>Recognition is evidence. Confirm the word, placement, and cut before editing the reviewed audio recipe.</p><table><tr><th>Clip</th><th>Word / meaning</th><th>Evidence</th><th>Recording</th></tr>".to_string();
    let base = url::Url::from_directory_path(root)
        .map_err(|_| anyhow::anyhow!("invalid repository path"))?;
    for c in arr(&data["clips"]) {
        let path = s(&c["path"]);
        html += &format!(
            "<tr><td>{}<br>{}–{} s</td><td lang=\"ml\">{}<br>{}</td><td>{}<br>{}</td><td><audio controls preload=\"none\" src=\"{}\"></audio></td></tr>",
            esc(Path::new(path).file_stem().unwrap().to_str().unwrap()),
            c["start"],
            c["end"],
            esc(s(&c["transcript"])),
            esc(s(&c["meaning"])),
            esc(s(&c["status"])),
            esc(s(&c["alignment_warning"])),
            esc(base.join(path)?.as_str())
        );
    }
    html += "</table></html>";
    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(output, html)?;
    Ok(())
}
