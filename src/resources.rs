//! Native archive and transcription maintenance, shared across source collections.
use crate::util::*;
use anyhow::{Result, ensure};
use scraper::{Html, Selector};
use serde_json::json;
use std::{
    collections::{BTreeMap, BTreeSet, VecDeque},
    fs,
    io::{Read, Write},
    path::Path,
    process::Command,
};
use url::Url;
fn selector(s: &str) -> Selector {
    Selector::parse(s).expect("built-in selector")
}
fn safe_target(root: &Path, relative: &str) -> Result<std::path::PathBuf> {
    ensure!(
        !Path::new(relative).is_absolute()
            && !Path::new(relative)
                .components()
                .any(|c| matches!(c, std::path::Component::ParentDir)),
        "archive path escapes root: {relative}"
    );
    let p = root.join(relative);
    if p.exists() {
        inside(root, relative)?;
    } else {
        let mut ancestor = p.parent().unwrap();
        while !ancestor.exists() {
            ancestor = ancestor.parent().unwrap();
        }
        ensure!(
            ancestor.canonicalize()?.starts_with(root.canonicalize()?),
            "archive symlink escapes root"
        );
    }
    Ok(p)
}
fn fetch(url: &str, path: &Path) -> Result<()> {
    let u = Url::parse(url)?;
    ensure!(
        ["http", "https"].contains(&u.scheme()),
        "unsupported download protocol"
    );
    if let Some(p) = path.parent() {
        fs::create_dir_all(p)?;
    }
    let mut response = ureq::get(url)
        .header("User-Agent", "Malayalam-learning-resource-archive/1.0")
        .call()?;
    let tmp = path.with_extension("download-part");
    let mut out = fs::File::create(&tmp)?;
    std::io::copy(&mut response.body_mut().as_reader(), &mut out)?;
    out.flush()?;
    fs::rename(tmp, path)?;
    Ok(())
}
/// Restore missing files from their manifest, checking size, digest and format.
/// Existing files are never replaced by a failed download.
pub fn archive(root: &Path, manifest_path: &Path, check: bool) -> Result<()> {
    let mut manifest = read_json(manifest_path)?;
    let directory = manifest_path.parent().unwrap();
    let field = if manifest["records"].is_array() {
        "records"
    } else {
        "files"
    };
    ensure!(
        manifest[field].is_array(),
        "manifest needs files or records"
    );
    let records = manifest[field].as_array_mut().unwrap();
    let mut count = 0;
    for r in records {
        let Some(relative) = r["path"].as_str().map(str::to_string) else {
            continue;
        };
        let path = safe_target(directory, &relative)?;
        if !path.exists() && !check {
            let url = r["download_url"]
                .as_str()
                .or_else(|| r["url"].as_str())
                .ok_or_else(|| anyhow::anyhow!("no download URL: {relative}"))?;
            fetch(url, &path)?;
        }
        let bytes = fs::read(&path)?;
        if !r["sha256"].is_null() {
            ensure!(
                hash(&bytes) == s(&r["sha256"]),
                "archive checksum changed: {relative}"
            );
        }
        if !r["bytes"].is_null() {
            ensure!(
                bytes.len() as u64 == r["bytes"].as_u64().unwrap_or(u64::MAX),
                "archive size changed: {relative}"
            );
        }
        match path
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_lowercase()
            .as_str()
        {
            "pdf" => {
                ensure!(bytes.starts_with(b"%PDF-"), "not a PDF: {relative}");
                run(Command::new("pdfinfo")
                    .arg(&path)
                    .stdout(std::process::Stdio::null()))?;
            }
            "zip" => {
                let mut archive = zip::ZipArchive::new(std::io::Cursor::new(&bytes))?;
                for i in 0..archive.len() {
                    let mut member = archive.by_index(i)?;
                    let mut sink = std::io::sink();
                    std::io::copy(&mut member, &mut sink)?;
                }
            }
            "mp3" | "mp4" | "wav" | "m4a" | "ogg" | "webm" | "mov" => {
                run(Command::new("ffprobe")
                    .args([
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "json",
                    ])
                    .arg(&path)
                    .stdout(std::process::Stdio::null()))?;
            }
            _ => {}
        }
        count += 1;
    }
    // Validate offline HTML links as well as archive checksums.
    let mut links = 0;
    for e in walkdir::WalkDir::new(directory)
        .into_iter()
        .filter_map(Result::ok)
    {
        let path = e.path();
        if !e.file_type().is_file()
            || path.extension().is_none_or(|e| e != "html")
            || path
                .components()
                .any(|c| c.as_os_str() == "raw" || c.as_os_str() == "external")
        {
            continue;
        }
        let html = Html::parse_document(&fs::read_to_string(path)?);
        for node in html.select(&selector("[href], [src], [poster]")) {
            for attr in ["href", "src", "poster"] {
                if let Some(link) = node.value().attr(attr) {
                    if Url::parse(link).is_ok() || link.starts_with(['#', '/']) {
                        continue;
                    }
                    let target = link.split(['#', '?']).next().unwrap();
                    let target = percent_encoding::percent_decode_str(target).decode_utf8()?;
                    ensure!(
                        path.parent().unwrap().join(target.as_ref()).exists(),
                        "broken archive link {} -> {link}",
                        path.display()
                    );
                    links += 1;
                }
            }
        }
    }
    let _ = root;
    println!("Validated {count} archive files and {links} relative links");
    Ok(())
}
/// Archive an explicitly bounded set of public pages and assets; original
/// credits and source HTML are retained. No scripts run in the offline copy.
pub fn collect(
    seeds: &[String],
    destination: &Path,
    scope: Option<&str>,
    maximum: usize,
) -> Result<()> {
    ensure!(
        !seeds.is_empty() && maximum > 0,
        "provide seed URLs and a positive limit"
    );
    fs::create_dir_all(destination)?;
    let mut queue: VecDeque<_> = seeds.iter().cloned().collect();
    let mut seen = BTreeSet::new();
    let mut pages = vec![];
    let mut assets = BTreeMap::new();
    let mut failures = vec![];
    while let Some(url) = queue.pop_front() {
        if seen.len() >= maximum {
            break;
        }
        if !seen.insert(url.clone()) {
            continue;
        }
        let base = Url::parse(&url)?;
        let name = base
            .path_segments()
            .and_then(|mut s| s.next_back())
            .filter(|s| !s.is_empty())
            .unwrap_or("index.html");
        let name = if name.ends_with(".html") {
            name.to_string()
        } else {
            format!("{name}.html")
        };
        let name = format!("{}-{name}", &hash(&url)[..12]);
        let path = destination.join("raw").join(&name);
        let result = (|| -> Result<_> {
            if !path.exists() {
                fetch(&url, &path)?;
            }
            let source = fs::read_to_string(&path)?;
            let tree = Html::parse_document(&source);
            let main = tree
                .select(&selector("article, .entry-content, main, body"))
                .next()
                .ok_or_else(|| anyhow::anyhow!("page has no content"))?;
            let title = tree
                .select(&selector("h1, title"))
                .next()
                .map(|e| e.text().collect::<String>())
                .unwrap_or_else(|| url.clone());
            for node in main.select(&selector(
                "a[href], img[src], audio[src], source[src], video[src], link[href]",
            )) {
                let value = node
                    .value()
                    .attr("src")
                    .or_else(|| node.value().attr("href"))
                    .unwrap();
                let Ok(mut target) = base.join(value) else {
                    continue;
                };
                target.set_fragment(None);
                if !["http", "https"].contains(&target.scheme()) {
                    continue;
                }
                let extension = Path::new(target.path())
                    .extension()
                    .and_then(|e| e.to_str())
                    .unwrap_or("")
                    .to_lowercase();
                if [
                    "pdf", "mp3", "mp4", "wav", "m4a", "ogg", "webm", "mov", "png", "jpg", "jpeg",
                    "gif", "svg", "css", "zip", "txt",
                ]
                .contains(&extension.as_str())
                {
                    assets.entry(target.to_string()).or_insert_with(|| {
                        format!(
                            "assets/{}-{}",
                            &hash(target.as_str())[..12],
                            target
                                .path_segments()
                                .and_then(|mut s| s.next_back())
                                .unwrap_or("asset")
                        )
                    });
                } else if scope.is_some_and(|s| target.as_str().starts_with(s))
                    && !seen.contains(target.as_str())
                {
                    queue.push_back(target.to_string());
                }
            }
            Ok((title, source, main.text().collect::<Vec<_>>().join(" ")))
        })();
        match result {
            Ok((title, source, text)) => pages.push((url, name, title, source, text)),
            Err(e) => failures.push(json!({"url":url,"error":e.to_string()})),
        }
    }
    let mut local: BTreeMap<String, String> = pages
        .iter()
        .map(|(u, n, _, _, _)| (u.clone(), format!("pages/{n}")))
        .collect();
    for (url, path) in assets {
        let p = safe_target(destination, &path)?;
        match if p.exists() { Ok(()) } else { fetch(&url, &p) } {
            Ok(()) => {
                local.insert(url, path);
            }
            Err(e) => failures.push(json!({"url":url,"error":e.to_string()})),
        }
    }
    fs::create_dir_all(destination.join("pages"))?;
    let mut records = vec![];
    for (url, name, title, source, text) in pages {
        let base = Url::parse(&url)?;
        let mut html = re(r"(?si)<script\b[^>]*>.*?</script>")
            .replace_all(&source, "")
            .into_owned();
        html = re(r#"\b(src|href)=(["'])([^"']*)["']"#)
            .replace_all(&html, |c: &regex::Captures| {
                let v = &c[3];
                let target = base.join(v);
                let value = target
                    .map(|u| {
                        local
                            .get(u.as_str())
                            .map(|p| format!("../{p}"))
                            .unwrap_or_else(|| u.to_string())
                    })
                    .unwrap_or_else(|_| v.into());
                format!("{}={}{}{}", &c[1], &c[2], esc(&value), &c[2])
            })
            .into_owned();
        let banner = format!(
            "<p>Offline reading copy. <a href=\"{}\">Original website</a>. Original credits and notices retained. Interactive tools require the original website.</p>",
            esc(&url)
        );
        html = re(r"(?i)(<body\b[^>]*>)")
            .replacen(&html, 1, |c: &regex::Captures| format!("{}{banner}", &c[1]))
            .into_owned();
        fs::write(destination.join("pages").join(&name), html)?;
        fs::write(
            destination.join("pages").join(&name).with_extension("txt"),
            text + "\n",
        )?;
        records.push(json!({"url":url,"path":format!("raw/{name}"),"title":title,"status":"downloaded","bytes":source.len(),"sha256":hash(source)}));
    }
    for (url, path) in &local {
        if path.starts_with("assets/") {
            let p = destination.join(path);
            records.push(json!({"url":url,"path":path,"status":"downloaded","bytes":fs::metadata(&p)?.len(),"sha256":digest(p)?}));
        }
    }
    let mut index="<!doctype html><meta charset=\"utf-8\"><title>Malayalam source archive</title><h1>Source archive</h1><p>Original credits and license notices retained.</p><ul>".to_string();
    for (u, p) in local.iter().filter(|(_, p)| p.starts_with("pages/")) {
        index += &format!("<li><a href=\"{}\">{}</a></li>", esc(p), esc(u));
    }
    index += "</ul>";
    fs::write(destination.join("index.html"), index)?;
    write_json(
        destination.join("manifest.json"),
        &json!({"schema_version":1,"records":records,"failures":failures,"scope":scope,"maximum_pages":maximum}),
        false,
    )?;
    Ok(())
}
/// Import authorized StoryWeaver downloads without loosening ZIP path checks.
pub fn import_story(archive: &Path, destination: &Path) -> Result<()> {
    fs::create_dir_all(destination)?;
    let mut zip = zip::ZipArchive::new(fs::File::open(archive)?)?;
    let mut records = vec![];
    for i in 0..zip.len() {
        let mut file = zip.by_index(i)?;
        let name = file.name().to_string();
        ensure!(
            Path::new(&name).file_name().and_then(|n| n.to_str()) == Some(name.as_str()),
            "unexpected ZIP path"
        );
        let path = safe_target(destination, &name)?;
        let mut bytes = vec![];
        file.read_to_end(&mut bytes)?;
        if path.extension().is_some_and(|s| s == "pdf") {
            ensure!(bytes.starts_with(b"%PDF-"), "not a PDF");
        }
        fs::write(&path, &bytes)?;
        records.push(json!({"path":name,"bytes":bytes.len(),"sha256":hash(&bytes)}));
    }
    let credits: Vec<_> = fs::read_dir(destination)?
        .filter_map(Result::ok)
        .map(|e| e.path())
        .filter(|p| {
            p.file_name()
                .unwrap()
                .to_string_lossy()
                .starts_with("StoryWeaverAttribution_")
        })
        .collect();
    ensure!(
        !credits.is_empty()
            && credits
                .iter()
                .all(|p| fs::read_to_string(p).is_ok_and(|t| t.contains("CC BY 4.0"))),
        "original attribution missing"
    );
    for p in records.iter().filter(|r| s(&r["path"]).ends_with(".pdf")) {
        let pdf = destination.join(s(&p["path"]));
        run(Command::new("pdftotext")
            .arg("-layout")
            .arg(&pdf)
            .arg(pdf.with_extension("txt")))?;
    }
    write_json(
        destination.join("import.json"),
        &json!({"archive_sha256":digest(archive)?,"files":records,"license":"CC BY 4.0"}),
        false,
    )?;
    Ok(())
}

pub fn assemble_books(root: &Path, check: bool) -> Result<()> {
    let mut plan = read_json(root.join("data/books/transcription-plan.json"))?
        .as_array()
        .ok_or_else(|| anyhow::anyhow!("invalid transcription plan"))?
        .clone();
    plan.extend([
        json!({"collection":"malayalam-mission","slug":"part-2","pages":83}),
        json!({"collection":"malayalam-mission","slug":"part-3","pages":76}),
        json!({"collection":"ciil","slug":"phonetic-reader","pages":80}),
    ]);
    let mut reports = vec![];
    for book in plan {
        let collection = s(&book["collection"]);
        let slug = s(&book["slug"]);
        let directory = root.join(format!("data/books/{collection}/markdown/{slug}"));
        let total = book["pages"]
            .as_u64()
            .ok_or_else(|| anyhow::anyhow!("book page count missing"))?;
        let mut missing = vec![];
        let mut pages = vec![];
        let mut uncertain = vec![];
        for n in 1..=total {
            let path = directory.join(format!("page-{n:03}.md"));
            if !path.exists() {
                missing.push(n);
                continue;
            }
            let text = fs::read_to_string(&path)?;
            ensure!(
                !text.trim().is_empty()
                    && re(&format!("(?m)^(?:# )?PDF page:? 0*{n}(?:\\D|$)")).is_match(&text),
                "empty page or wrong PDF metadata: {}",
                path.display()
            );
            for (line, text) in text.lines().enumerate() {
                if text.contains("[unclear") {
                    uncertain.push(json!({"pdf_page":n,"line":line+1,"text":text}));
                }
            }
            pages.push((n, text));
        }
        let mut report = book.clone();
        report["method"] = json!("Visual transcription; no OCR");
        report["transcribed_pages"] = json!(pages.len());
        report["missing_pdf_pages"] = json!(missing);
        report["uncertain_fragments"] = json!(uncertain);
        if missing.is_empty() {
            let title = if collection == "malayalam-mission" {
                format!("Kanikkonna — Part {}", slug.trim_start_matches("part-"))
            } else if slug == "phonetic-reader" {
                "Malayalam Phonetic Reader".into()
            } else {
                slug.split('-')
                    .map(|s| {
                        let mut c = s.chars();
                        c.next()
                            .map(|f| f.to_uppercase().to_string() + c.as_str())
                            .unwrap_or_default()
                    })
                    .collect::<Vec<_>>()
                    .join(" ")
            };
            let mut chunks = vec![format!(
                "# {title}\n\nVisual transcription draft. The source PDF remains authoritative for exact layout, illustrations, and typography.\n"
            )];
            for (n, text) in pages {
                let text = text
                    .replace("](images/", &format!("]({slug}/images/"))
                    .replace("](../review-images/", "](review-images/");
                chunks.push(format!("<a id=\"pdf-page-{n:03}\"></a>\n\n## PDF page {n:03}\n\n[Separate page transcription]({slug}/page-{n:03}.md)\n\n{}\n",text.trim_end()));
            }
            let output = directory.parent().unwrap().join(format!("{slug}.md"));
            let text = chunks.join("\n---\n\n");
            write(&output, &text, check)?;
            report["combined_sha256"] = json!(hash(&text));
            if check {
                check_markdown_links(&output)?;
            }
        } else {
            ensure!(!check, "incomplete transcription {slug}: {missing:?}");
        }
        write_json(directory.join("coverage.json"), &report, check)?;
        reports.push(report);
    }
    write_json(
        root.join("data/books/transcription-progress.json"),
        &json!(reports),
        check,
    )?;
    Ok(())
}
fn check_markdown_links(path: &Path) -> Result<()> {
    let text = fs::read_to_string(path)?;
    for c in re(r"\]\(([^)]+)\)").captures_iter(&text) {
        let target = &c[1];
        if target.starts_with('#') || Url::parse(target).is_ok() {
            continue;
        }
        let target = target.split('#').next().unwrap();
        ensure!(
            path.parent().unwrap().join(target).exists(),
            "broken transcription link: {} -> {target}",
            path.display()
        );
    }
    Ok(())
}
