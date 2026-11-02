use anyhow::{Context, Result, ensure};
use regex::Regex;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{fs, path::Path, process::Command};

pub fn re(pattern: &str) -> Regex {
    {
        use std::sync::{OnceLock, RwLock};
        static CACHE: OnceLock<RwLock<std::collections::BTreeMap<String, Regex>>> = OnceLock::new();
        let cache = CACHE.get_or_init(Default::default);
        if let Some(r) = cache.read().unwrap().get(pattern) {
            return r.clone();
        }
        let r = Regex::new(pattern).expect("valid built-in pattern");
        cache.write().unwrap().insert(pattern.into(), r.clone());
        r
    }
}
pub fn read_json(path: impl AsRef<Path>) -> Result<Value> {
    let p = path.as_ref();
    serde_json::from_slice(&fs::read(p).with_context(|| p.display().to_string())?)
        .with_context(|| p.display().to_string())
}
pub fn json_text(value: &Value) -> Result<String> {
    Ok(serde_json::to_string_pretty(value)? + "\n")
}
pub fn write(path: impl AsRef<Path>, text: &str, check: bool) -> Result<()> {
    let p = path.as_ref();
    if check {
        ensure!(
            fs::read_to_string(p).with_context(|| p.display().to_string())? == text,
            "{} is stale",
            p.display()
        );
    } else {
        if let Some(parent) = p.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(p, text)?;
    }
    Ok(())
}
pub fn write_json(path: impl AsRef<Path>, value: &Value, check: bool) -> Result<()> {
    let p = path.as_ref();
    if check {
        ensure!(read_json(p)? == *value, "{} is stale", p.display());
        Ok(())
    } else {
        if p.exists() && read_json(p)? == *value {
            return Ok(());
        }
        write(p, &json_text(value)?, false)
    }
}
pub fn hash(bytes: impl AsRef<[u8]>) -> String {
    format!("{:x}", Sha256::digest(bytes.as_ref()))
}
pub fn digest(path: impl AsRef<Path>) -> Result<String> {
    Ok(hash(fs::read(path)?))
}
pub fn esc(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#x27;")
}
pub fn s(value: &Value) -> &str {
    value.as_str().unwrap_or("")
}
pub fn arr(value: &Value) -> &[Value] {
    value.as_array().map(Vec::as_slice).unwrap_or(&[])
}
pub fn ml(text: &str) -> bool {
    text.chars().any(|c| ('\u{d00}'..='\u{d7f}').contains(&c))
}
pub fn clean(text: &str) -> String {
    let t = re(r"(?s)<!--.*?-->").replace_all(text, "");
    let t = re(r"<br\s*/?>").replace_all(&t, "; ");
    let t = re(r"<[^>]*>").replace_all(&t, "");
    html_escape::decode_html_entities(&t)
        .replace("\\*", "*")
        .replace("\\|", "|")
        .trim()
        .to_string()
}
pub fn cells(line: &str) -> Vec<String> {
    let mut parts = vec![];
    let mut start = 0;
    let mut escaped = false;
    for (i, c) in line.trim().char_indices() {
        if c == '|' && !escaped {
            parts.push(line.trim()[start..i].to_string());
            start = i + 1;
        }
        escaped = c == '\\' && !escaped;
    }
    if parts.len() > 1 {
        parts.remove(0);
    }
    parts
}
pub fn table_re() -> Regex {
    re(r"(?m)(?:^\|[^\n]*\n)+")
}
pub fn run(command: &mut Command) -> Result<()> {
    let description = format!("{command:?}");
    let status = command.status().with_context(|| description.clone())?;
    ensure!(status.success(), "{description} failed: {status}");
    Ok(())
}
pub fn output(command: &mut Command) -> Result<Vec<u8>> {
    let description = format!("{command:?}");
    let result = command.output().with_context(|| description.clone())?;
    ensure!(
        result.status.success(),
        "{description}: {}",
        String::from_utf8_lossy(&result.stderr)
    );
    Ok(result.stdout)
}
pub fn inside(root: &Path, relative: &str) -> Result<std::path::PathBuf> {
    let canonical = root.canonicalize()?;
    let path = root.join(relative).canonicalize()?;
    ensure!(
        path.starts_with(canonical),
        "path escapes repository: {relative}"
    );
    Ok(path)
}
