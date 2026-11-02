//! Shared portable book preparation; Pandoc is native, PDF is printed by Chromium.
use crate::{audio::strip_columns, reading::documents, util::*};
use anyhow::{Context, Result, ensure};
use serde_json::{Value, json};
use std::{
    collections::BTreeSet,
    fs,
    path::{Path, PathBuf},
    process::{Command, Stdio},
    thread,
    time::{Duration, Instant},
};
const CREDIT: &str = "Original textbook by Rodney F. Moag. Digital adaptation and modifications by Mathew Jacob. This independently prepared digital edition includes corrections, redrawn writing models, audio integration, and added practice material; it was not published by Rodney F. Moag.";
pub fn paths(root: &Path) -> Result<Vec<PathBuf>> {
    let mut p = ["README", "digital-edition", "practice"]
        .map(|s| root.join(format!("docs/{s}.md")))
        .to_vec();
    p.extend(documents(root)?);
    p.extend(["proofreading-review", "technical-notes"].map(|s| root.join(format!("docs/{s}.md"))));
    Ok(p)
}
fn slug(s: &str) -> String {
    re(r"\s+")
        .replace_all(
            &re(r"[^\p{L}\p{N}_\s-]").replace_all(&s.to_lowercase(), ""),
            "-",
        )
        .trim_matches('-')
        .into()
}
pub fn strip_audio(input: &str) -> String {
    let mut text = re(r"(?s)<!-- letter-audio -->.*?<!-- /letter-audio -->")
        .replace_all(input, "")
        .into_owned();
    text = strip_columns(&text, false);
    let mut ranges = vec![];
    let mut start = None;
    let mut depth = 0;
    for tag in re(r"</?div\b[^>]*>").find_iter(&text) {
        if tag.as_str().starts_with("</") {
            if let Some(begin) = start {
                depth -= 1;
                if depth == 0 {
                    ranges.push((begin, tag.end()));
                    start = None;
                }
            }
        } else if start.is_some() {
            depth += 1;
        } else if tag.as_str().contains("class=\"lesson-audio\"") {
            start = Some(tag.start());
            depth = 1;
        }
    }
    for (a, b) in ranges.into_iter().rev() {
        text.replace_range(a..b, "\n\n");
    }
    text = re(r"(?s)<audio\b.*?</audio>")
        .replace_all(&text, "")
        .into_owned();
    text = re(r"(?s)<button\b[^>]*data-(?:row-)?audio-src=[^>]*>.*?</button>")
        .replace_all(&text, "")
        .into_owned();
    text = re(r"(?i)\[([^\]]+)\]\([^)]*\.(?:mp3|wav|ogg|m4a)(?:[?#][^)]*)?\)")
        .replace_all(&text, "$1")
        .into_owned();
    text = re(r#"(?si)<a\b[^>]*href=["'][^"']*\.(?:mp3|wav|ogg|m4a)[^"']*["'][^>]*>(.*?)</a>"#)
        .replace_all(&text, "$1")
        .into_owned();
    text=re(r"(?m)^.*\[Listen to the Alphabet and Individual Letters\].*\n|^Use the \[individual letter players\].*\n").replace_all(&text,"").into_owned();
    text
}
pub fn compact(text: &str, filename: &str) -> String {
    if !re(r"^lesson\d+\.md$").is_match(filename) {
        return text.into();
    }
    let r = re(r"(?m)^(#{2,3}) Vocabulary\n");
    let Some(h) = r.captures(text) else {
        return text.into();
    };
    let start = h.get(0).unwrap().end();
    let end = re(&format!("(?m)^#{{1,{}}} ", h[1].len()))
        .find(&text[start..])
        .map(|m| start + m.start())
        .unwrap_or(text.len());
    let body=table_re().replace_all(&text[start..end],|m:&regex::Captures|{let lines:Vec<_>=m[0].lines().collect();let headers:Vec<_>=cells(lines[0]).iter().map(|c|clean(c)).collect();if headers.len()!=2||headers[0]!="Malayalam"||!["English","Meaning"].contains(&headers[1].as_str()){return m[0].to_string();}let mut out="::: {.vocabulary-list}\n\n".to_string();for line in &lines[2..]{let c=cells(line);let class=if clean(&c[0]).chars().count()>20{"vocabulary-entry .vocabulary-entry-long"}else{"vocabulary-entry"};out+=&format!("::: {{.{class}}}\n\n<span class=\"vocabulary-term\" lang=\"ml\">{}</span> <span class=\"vocabulary-definition\">{}</span>\n\n:::\n\n",c[0].trim(),c[1].trim());}out+":::\n"});
    format!("{}{}{}", &text[..start], body, &text[end..])
}
pub fn prepare(root: &Path, path: &Path, chapters: &BTreeSet<String>) -> Result<String> {
    let filename = path.file_name().unwrap().to_str().unwrap();
    let stem = path.file_stem().unwrap().to_str().unwrap();
    let mut text = compact(&strip_audio(&fs::read_to_string(path)?), filename);
    text = re(r"(?s)<!-- reading-navigation -->.*?<!-- /reading-navigation -->")
        .replace_all(&text, "")
        .into_owned();
    if filename == "front-matter.md" {
        text = re(r#"(?s)<a id="front-matter-table-of-contents"></a>.*"#)
            .replace_all(&text, "")
            .into_owned();
    }
    text = re(r"\[([^\]]+)\]\(contents\.md(?:#[^)]*)?\)")
        .replace_all(&text, "$1")
        .into_owned();
    text = re(r"(?s)<!-- epub-download -->.*?<!-- /epub-download -->")
        .replace_all(&text, "")
        .into_owned();
    text = re(r"(?s)<a\b([^>]*)>(.*?)</a>")
        .replace_all(&text, |c: &regex::Captures| {
            let href_re = re(r#"href=["']([^"']+)["']"#);
            let Some(h) = href_re.captures(&c[1]) else {
                return c[0].to_string();
            };
            let mut href = html_escape::decode_html_entities(&h[1]).into_owned();
            if !re(r"^(?:[a-zA-Z][\w+.-]*:|#|/)").is_match(&href)
                && !re(r"^[\w-]+\.md(?:#|$)").is_match(&href)
            {
                href = format!("https://ml.matj.io/{href}");
            }
            format!("[{}]({href})", clean(&c[2]))
        })
        .into_owned();
    text = re(r#"<a id="([^"]+)"></a><!-- reading-anchor -->\n(#{1,6} [^\n]+)"#)
        .replace_all(&text, |c: &regex::Captures| {
            format!("{} {{#{}}}", &c[2], &c[1])
        })
        .into_owned();
    text = re(r#"<a id="([^"]+)"></a>"#)
        .replace_all(&text, "\n\n[]{#$1}\n\n")
        .into_owned();
    if !re(r"(?m)^# .*\{#").is_match(&text) {
        text = re(r"(?m)^(# [^\n]+)")
            .replacen(&text, 1, |c: &regex::Captures| {
                format!("{} {{#{stem}}}", &c[1])
            })
            .into_owned();
    }
    text = re(r"(?m)^(#{1,6}) ([^\n]+)$")
        .replace_all(&text, |c: &regex::Captures| {
            if re(r"\{#[^}]+\}$").is_match(&c[0]) {
                c[0].to_string()
            } else {
                format!("{} {{#{stem}-{}}}", &c[0], slug(&c[2]))
            }
        })
        .into_owned();
    text = re(r"<br\s*/?>").replace_all(&text, "<br />").into_owned();
    let link_re = re(r"\(([\w-]+\.md)(?:#([^\s)]+))?\)");
    let mut changes = vec![];
    for c in link_re.captures_iter(&text) {
        let name = &c[1];
        let fragment = c.get(2).map(|m| m.as_str()).unwrap_or("");
        let mut f = fragment.to_string();
        let target = if !chapters.contains(name) {
            format!(
                "(https://github.com/matjic/malayalam/blob/main/docs/{name}{})",
                if f.is_empty() {
                    String::new()
                } else {
                    format!("#{f}")
                }
            )
        } else {
            if !f.is_empty() {
                let raw = fs::read_to_string(root.join("docs").join(name))?;
                for h in re(r"(?m)^(#{1,6}) (.+)$").captures_iter(&raw) {
                    if slug(&h[2]) == fragment {
                        let before = &raw[..h.get(0).unwrap().start()];
                        f = re(r#"<a id="([^"]+)"></a><!-- reading-anchor -->\n$"#)
                            .captures(before)
                            .map(|c| c[1].to_string())
                            .unwrap_or_else(|| {
                                format!("{}-{fragment}", name.trim_end_matches(".md"))
                            });
                        break;
                    }
                }
            }
            format!(
                "(#{})",
                if f.is_empty() {
                    name.trim_end_matches(".md")
                } else {
                    &f
                }
            )
        };
        let m = c.get(0).unwrap();
        changes.push((m.start(), m.end(), target));
    }
    for (a, b, t) in changes.into_iter().rev() {
        text.replace_range(a..b, &t);
    }
    text = re(r"</?details[^>]*>").replace_all(&text, "").into_owned();
    text = re(r"<summary>(.*?)</summary>")
        .replace_all(&text, "\n\n**$1**\n\n")
        .into_owned();
    text=re(r#"(?s)<figure\b[^>]*>\s*<img src="([^"]+)" alt="([^"]+)"[^>]*>\s*<figcaption[^>]*>(.*?)</figcaption>\s*</figure>"#).replace_all(&text,|c:&regex::Captures|format!("\n\n![{}]({})\n\n{}\n\n",html_escape::decode_html_entities(&c[2]),&c[1],&c[3])).into_owned();
    let diagrams = re(r"!\[[^\]]*\]\((assets/writing/[^)]+\.svg)\)");
    let mut changes = vec![];
    for (index, c) in diagrams.captures_iter(&text).enumerate() {
        let mut svg = fs::read_to_string(root.join("docs").join(&c[1]))?;
        let prefix = format!("epub-{stem}-{}-", index + 1);
        let ids: Vec<_> = re(r#"\bid="([^"]+)""#)
            .captures_iter(&svg)
            .map(|c| c[1].to_string())
            .collect();
        for id in ids {
            svg = svg
                .replace(&format!("id=\"{id}\""), &format!("id=\"{prefix}{id}\""))
                .replace(&format!("url(#{id})"), &format!("url(#{prefix}{id})"));
        }
        svg = re(r#"aria-labelledby="([^"]+)""#)
            .replace_all(&svg, |c: &regex::Captures| {
                format!(
                    "aria-labelledby=\"{}\"",
                    c[1].split_whitespace()
                        .map(|id| format!("{prefix}{id}"))
                        .collect::<Vec<_>>()
                        .join(" ")
                )
            })
            .into_owned();
        svg = re(r#" style="[^"]*""#)
            .replace_all(&svg, "")
            .replace("\"#557467\"", "\"currentColor\"");
        for attr in ["stroke", "stroke-width"] {
            svg = re(&format!(r#"(<text\b[^>]*?) {attr}="[^"]*""#))
                .replace_all(&svg, "$1")
                .into_owned();
        }
        let class = if c[1].contains("/symbols/") {
            "writing-symbol"
        } else {
            "writing-table"
        };
        svg = svg.replacen("<svg ", &format!("<svg class=\"{class}\" "), 1);
        let m = c.get(0).unwrap();
        changes.push((m.start(), m.end(), format!("\n\n{}\n\n", svg.trim())));
    }
    for (a, b, t) in changes.into_iter().rev() {
        text.replace_range(a..b, &t);
    }
    text = re(r"</?div[^>]*>").replace_all(&text, "").into_owned();
    text = re(r"\((assets/[^)]+\.json)\)")
        .replace_all(
            &text,
            "(https://raw.githubusercontent.com/matjic/malayalam/main/docs/$1)",
        )
        .into_owned();
    if filename == "practice-pronunciation.md" {
        text=text.replace("The players below use UT Austin recordings. The complete recordings contain more examples than the selected words listed here.","Recordings for this listening practice are available on the website. The written examples and exercises are retained here.");
    }
    if filename == "digital-edition.md" {
        text=re(r"Lessons 1–25 include section clips.*?complete answer key\.").replace_all(&text,"Audio playback is available in the website edition; audio players and recording links are omitted from this book.").into_owned();
        text = text.replace(
            "an ebook has not been published by this change.",
            "this EPUB retains chapter and section navigation.",
        );
    }
    text = re(r"(?s)<!--.*?-->").replace_all(&text, "").into_owned();
    Ok(text)
}
pub fn markdown(root: &Path) -> Result<String> {
    let paths = paths(root)?;
    let chapters = paths
        .iter()
        .map(|p| p.file_name().unwrap().to_string_lossy().to_string())
        .collect();
    paths
        .iter()
        .map(|p| prepare(root, p, &chapters))
        .collect::<Result<Vec<_>>>()
        .map(|v| v.join("\n\n"))
}
pub fn build(root: &Path, output: &Path, pdf: bool, chrome: Option<&Path>) -> Result<()> {
    let kind = if pdf { "PDF" } else { "EPUB" };
    let content = format!(
        "# About this {kind} {{#{}-notes}}\n\n{CREDIT}\n\nThis edition includes the textbook and added practice lessons. Audio playback is available separately on the website and in the Anki decks. Reading answers are always visible. Use the linked contents and reader bookmarks to navigate.\n\n{}",
        kind.to_lowercase(),
        markdown(root)?
    );
    let temp = tempfile::tempdir()?;
    let source = temp.path().join("book.md");
    fs::write(&source, &content)?;
    if let Some(p) = output.parent() {
        fs::create_dir_all(p)?;
    }
    let output = std::path::absolute(output)?;
    let mut c = Command::new("pandoc");
    c.arg(&source).args(["--from=markdown-auto_identifiers","--toc","--toc-depth=1","--metadata=title:Malayalam: A University Course and Reference Grammar","--metadata=author:Rodney F. Moag (original textbook)","--metadata=subtitle:Digital adaptation by Mathew Jacob","--metadata=publisher:Mathew Jacob (digital edition)","--metadata=lang:en","--metadata=rights:Creative Commons Attribution-NonCommercial-ShareAlike 4.0; added practice material retains its credited reuse terms."]).arg(format!("--resource-path={}",root.join("docs").display())).current_dir(root.join("docs"));
    if !pdf {
        c.args(["--to=epub3", "--epub-chapter-level=1"])
            .arg(format!(
                "--css={}",
                root.join("templates/epub.css").display()
            ));
        let mut fonts = vec![];
        for f in fs::read_dir(root.join("docs/assets/fonts/book"))? {
            let p = f?.path();
            if p.extension().is_some_and(|x| x == "ttf") {
                fonts.push(p);
            }
        }
        ensure!(fonts.len() == 8, "expected eight book fonts");
        fonts.sort();
        for f in fonts {
            c.arg(format!("--epub-embed-font={}", f.display()));
        }
        run(c.arg("-o").arg(&output))?;
    } else {
        let html = temp.path().join("book.html");
        run(c
            .args(["--to=html5", "--standalone"])
            .arg(format!(
                "--template={}",
                root.join("templates/pdf.html").display()
            ))
            .arg("-o")
            .arg(&html))?;
        let doc = fs::read_to_string(&html)?;
        let base = url::Url::from_directory_path(root.join("docs"))
            .map_err(|_| anyhow::anyhow!("invalid book base"))?;
        let css = fs::read_to_string(root.join("templates/pdf.css"))?;
        let css = re(r"url\('\.\./docs/").replace_all(&css, &format!("url('{base}"));
        let doc=doc.replace("</head>",&format!("<style>{css}</style></head>")).replacen("<body>","<body><div class=\"titlepage\"><p class=\"kicker\">A UNIVERSITY COURSE</p><h1>Malayalam</h1><p class=\"subtitle\">A University Course and Reference Grammar</p><p class=\"author\">Original textbook by Rodney F. Moag</p><p class=\"adaptation\">Digital adaptation and modifications<br>by Mathew Jacob</p><p class=\"edition\">Independent adaptation of the fourth edition<br>Not published by Rodney F. Moag</p></div>",1);
        let doc = doc.replace("src=\"assets/", &format!("src=\"{base}assets/"));
        fs::write(&html, doc)?;
        print_pdf(&html, &output, chrome)?;
        normalize_bookmarks(root, &output)?;
    }
    println!(
        "Built {} ({} bytes)",
        output.display(),
        fs::metadata(&output)?.len()
    );
    Ok(())
}

/// Chromium can repeat a heading's first rendered line in the outline name.
/// Match only a known source heading with an exact repeated prefix, ignoring
/// line-wrap whitespace. Destinations and outline hierarchy stay unchanged.
pub fn bookmark_title(title: &str, expected: &BTreeSet<String>) -> Option<String> {
    let compact = |text: &str| {
        text.chars()
            .filter(|c| !c.is_whitespace())
            .collect::<String>()
    };
    let actual = compact(title);
    for original in expected {
        let wanted = compact(original);
        if actual == wanted {
            return Some(original.clone());
        }
        if let Some(prefix) = actual.strip_suffix(&wanted)
            && !prefix.is_empty()
            && wanted.starts_with(prefix)
        {
            return Some(original.clone());
        }
    }
    None
}
fn normalize_bookmarks(root: &Path, path: &Path) -> Result<()> {
    let content = markdown(root)?;
    let mut expected = BTreeSet::from(["Contents".to_string(), "About this PDF".into()]);
    for capture in re(r"(?m)^#{1,6} (.+?)(?: \{#[^}]+\})?$").captures_iter(&content) {
        expected.insert(clean(&capture[1]));
    }
    let mut doc = lopdf::Document::load(path)?;
    for object in doc.objects.values_mut() {
        let Ok(dictionary) = object.as_dict_mut() else {
            continue;
        };
        if !dictionary.has(b"Dest") && !dictionary.has(b"A") {
            continue;
        }
        let Ok(title) = dictionary.get(b"Title").and_then(lopdf::decode_text_string) else {
            continue;
        };
        if let Some(original) = bookmark_title(&title, &expected) {
            dictionary.set("Title", lopdf::text_string(&original));
        }
    }
    doc.save(path)?;
    Ok(())
}
struct Browser(std::process::Child);
impl Drop for Browser {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}

fn start_browser(
    mut command: Command,
    profile: &Path,
    timeout: Duration,
) -> Result<(Browser, u16)> {
    let diagnostics = profile.join("chrome-stderr.log");
    command
        .stdout(Stdio::null())
        .stderr(fs::File::create(&diagnostics)?);
    let mut browser = Browser(
        command
            .spawn()
            .with_context(|| format!("launching {command:?}"))?,
    );
    let port_file = profile.join("DevToolsActivePort");
    let deadline = Instant::now() + timeout;
    loop {
        let stderr = || fs::read_to_string(&diagnostics).unwrap_or_default();
        if let Some(status) = browser.0.try_wait()? {
            anyhow::bail!(
                "Chromium exited before becoming ready ({status}):\n{}",
                stderr()
            );
        }
        // Chrome can create the file before finishing its first line.
        if let Ok(contents) = fs::read_to_string(&port_file)
            && let Some(port) = contents
                .lines()
                .next()
                .and_then(|line| line.parse::<u16>().ok())
            && port != 0
        {
            return Ok((browser, port));
        }
        ensure!(
            Instant::now() < deadline,
            "Chromium did not become ready within {timeout:?}:\n{}",
            stderr()
        );
        thread::sleep(Duration::from_millis(50));
    }
}

pub fn print_pdf(html: &Path, output: &Path, chrome: Option<&Path>) -> Result<()> {
    use base64::Engine;
    let executable = chrome
        .map(Path::to_path_buf)
        .or_else(|| std::env::var_os("CHROME").map(PathBuf::from))
        .unwrap_or_else(|| {
            if cfg!(target_os = "macos") {
                PathBuf::from("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            } else {
                PathBuf::from("chromium")
            }
        });
    let temp = tempfile::tempdir()?;
    let mut command = Command::new(executable);
    command
        .args([
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-dev-shm-usage",
            "--remote-debugging-port=0",
        ])
        .arg(format!("--user-data-dir={}", temp.path().display()))
        .arg("about:blank");
    let (_browser, port) = start_browser(command, temp.path(), Duration::from_secs(30))?;
    let targets: Value = serde_json::from_str(
        &ureq::get(format!("http://127.0.0.1:{port}/json/list"))
            .call()?
            .body_mut()
            .read_to_string()?,
    )?;
    let endpoint = arr(&targets)
        .iter()
        .find(|v| v["type"] == "page")
        .and_then(|v| v["webSocketDebuggerUrl"].as_str())
        .ok_or_else(|| anyhow::anyhow!("missing Chrome page"))?;
    let (mut ws, _) = tungstenite::connect(endpoint)?;
    if let tungstenite::stream::MaybeTlsStream::Plain(socket) = ws.get_mut() {
        socket.set_read_timeout(Some(Duration::from_secs(120)))?;
    }
    let mut id = 0;
    let mut call = |method: &str, params: Value| -> Result<Value> {
        id += 1;
        ws.send(tungstenite::Message::Text(
            json!({"id":id,"method":method,"params":params})
                .to_string()
                .into(),
        ))?;
        loop {
            let message = ws.read()?;
            if let tungstenite::Message::Text(text) = message {
                let value: Value = serde_json::from_str(&text)?;
                if value["id"] == id {
                    ensure!(
                        value["error"].is_null(),
                        "Chrome {method}: {}",
                        value["error"]
                    );
                    return Ok(value["result"].clone());
                }
            }
        }
    };
    call("Page.enable", json!({}))?;
    let url = url::Url::from_file_path(html).map_err(|_| anyhow::anyhow!("invalid HTML path"))?;
    let result = call("Page.navigate", json!({"url":url.as_str()}))?;
    ensure!(result["errorText"].is_null(), "Chrome navigation failed");
    // Wait for load, decoded images, and all eight embedded font faces before printing.
    let loaded = call(
        "Runtime.evaluate",
        json!({"expression":"new Promise((resolve,reject)=>{const ready=async()=>{try{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));resolve({ready:document.readyState,images:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length});}catch(e){reject(String(e));}};if(document.readyState==='complete')ready();else window.addEventListener('load',ready,{once:true});})","awaitPromise":true,"returnByValue":true}),
    )?;
    ensure!(
        loaded["exceptionDetails"].is_null() && loaded["result"]["value"]["images"] == 0,
        "print resources failed: {loaded}"
    );
    let result = call(
        "Page.printToPDF",
        json!({"printBackground":true,"preferCSSPageSize":true,"generateDocumentOutline":true,"generateTaggedPDF":true,"displayHeaderFooter":false,"transferMode":"ReturnAsStream"}),
    )?;
    let handle = s(&result["stream"]);
    let mut file = fs::File::create(output)?;
    use std::io::Write;
    loop {
        let chunk = call("IO.read", json!({"handle":handle,"size":1_048_576}))?;
        let bytes = if chunk["base64Encoded"] == true {
            base64::engine::general_purpose::STANDARD.decode(s(&chunk["data"]))?
        } else {
            s(&chunk["data"]).as_bytes().to_vec()
        };
        file.write_all(&bytes)?;
        if chunk["eof"] == true {
            break;
        }
    }
    call("IO.close", json!({"handle":handle}))?;
    Ok(())
}
pub fn check_lists(root: &Path) -> Result<()> {
    fn plain(v: &Value) -> String {
        if v["t"] == "Str" {
            return s(&v["c"]).to_string() + " ";
        }
        if ["SoftBreak", "LineBreak"].contains(&s(&v["t"])) {
            return "\n".into();
        }
        if let Some(a) = v.as_array() {
            return a.iter().map(plain).collect();
        }
        plain_children(v)
    }
    fn plain_children(v: &Value) -> String {
        if v.is_object() {
            plain(&v["c"])
        } else {
            String::new()
        }
    }
    fn inspect(v: &Value) -> Result<()> {
        if let Some(a) = v.as_array() {
            for c in a {
                inspect(c)?;
            }
        } else if v.is_object() {
            if ["Table", "CodeBlock", "RawBlock"].contains(&s(&v["t"])) {
                return Ok(());
            }
            if v["t"] == "Para" && v["c"][0]["t"] != "Strong" {
                let text = plain(&v["c"]);
                ensure!(
                    !re(r"(?:^|\n)\s*\d+\.\s").is_match(&text),
                    "numbered paragraph outside list: {}",
                    text.chars().take(160).collect::<String>()
                );
            }
            inspect(&v["c"])?;
        }
        Ok(())
    }
    let temp = tempfile::tempdir()?;
    let p = temp.path().join("book.md");
    fs::write(&p, markdown(root)?)?;
    let ast: Value = serde_json::from_slice(&crate::util::output(
        Command::new("pandoc")
            .args(["-f", "markdown-auto_identifiers", "-t", "json"])
            .arg(p),
    )?)?;
    inspect(&ast["blocks"])?;
    println!("Book list structure checked");
    Ok(())
}
pub fn validate_pdf(root: &Path, path: &Path) -> Result<()> {
    let doc = lopdf::Document::load(path)?;
    ensure!(!doc.is_encrypted(), "encrypted PDF");
    let pages = doc.get_pages();
    ensure!(pages.len() > 100, "incomplete PDF");
    let text = String::from_utf8(crate::util::output(
        Command::new("pdftotext").arg(path).arg("-"),
    )?)?;
    ensure!(
        text.chars().count() > 100_000
            && text
                .chars()
                .filter(|c| ('\u{d00}'..='\u{d7f}').contains(c))
                .count()
                > 10_000,
        "searchable Malayalam text missing"
    );
    ensure!(!text.contains('\u{fffd}'), "unmapped characters in PDF");
    let mut titles = vec![];
    let mut internal = 0;
    let mut external = 0;
    let mut fonts = vec![];
    for object in doc.objects.values() {
        let Ok(d) = object.as_dict() else {
            continue;
        };
        if let Ok(title) = d.get(b"Title").and_then(|t| t.as_str()) {
            let title = if title.starts_with(&[254, 255]) {
                String::from_utf16_lossy(
                    &title[2..]
                        .as_chunks::<2>()
                        .0
                        .iter()
                        .map(|c| u16::from_be_bytes([c[0], c[1]]))
                        .collect::<Vec<_>>(),
                )
            } else {
                String::from_utf8_lossy(title).into_owned()
            };
            titles.push(title);
        }
        if let Ok(name) = d.get(b"BaseFont").and_then(|n| n.as_name()) {
            let name = String::from_utf8_lossy(name);
            if name.contains("Malayalam") || name.contains("SourceSerif") {
                fonts.push(name.into_owned());
            }
        }
        if d.get(b"Type").and_then(|t| t.as_name()).ok() == Some(b"FontDescriptor") {
            ensure!(
                [b"FontFile".as_slice(), b"FontFile2", b"FontFile3"]
                    .iter()
                    .any(|k| d.has(k)),
                "font not embedded"
            );
        }
    }
    let normalize = |s: &str| s.split_whitespace().collect::<Vec<_>>().join(" ");
    ensure!(
        titles.iter().filter(|t| *t == "Contents").count() == 1,
        "expected one generated contents bookmark; first titles: {:?}",
        &titles[..titles.len().min(8)]
    );
    ensure!(
        !titles.iter().any(|t| t == "Table of Contents"),
        "printed contents leaked into PDF"
    );
    for p in paths(root)? {
        let raw = fs::read_to_string(p)?;
        let title = re(r"(?m)^# (.+)$").captures(&raw).unwrap()[1].to_string();
        ensure!(
            titles.iter().any(|t| normalize(t) == normalize(&title)),
            "missing chapter bookmark: {title}"
        );
    }
    ensure!(
        fonts.iter().any(|f| f.contains("Malayalam"))
            && fonts.iter().any(|f| f.contains("SourceSerif")),
        "book fonts missing"
    );
    for page_id in pages.values() {
        let p = doc.get_object(*page_id)?.as_dict()?;
        if let Ok(media) = p.get(b"MediaBox").and_then(|m| m.as_array()) {
            let width = media[2].as_float()?;
            let height = media[3].as_float()?;
            ensure!(
                (width - 595.28).abs() < 1. && (height - 841.89).abs() < 1.,
                "expected A4 pages"
            );
        }
        for a in doc.get_page_annotations(*page_id)? {
            if a.has(b"Dest") {
                internal += 1;
            }
            if let Ok(action) = a.get(b"A") {
                let action = match action {
                    lopdf::Object::Reference(id) => doc.get_object(*id)?,
                    v => v,
                };
                if let Ok(d) = action.as_dict() {
                    if let Ok(uri) = d.get(b"URI").and_then(|u| u.as_str()) {
                        external += 1;
                        let uri = String::from_utf8_lossy(uri);
                        ensure!(
                            !uri.starts_with("file:")
                                && !re(r"(?i)\.(mp3|wav|ogg|m4a)(?:[?#]|$)").is_match(&uri),
                            "local/audio PDF link: {uri}"
                        );
                    } else if d.get(b"S").and_then(|s| s.as_name()).ok() == Some(b"GoTo") {
                        internal += 1;
                    }
                }
            }
        }
    }
    ensure!(
        internal > 100 && external > 10,
        "PDF navigation missing: {internal}/{external}"
    );
    let bbox = String::from_utf8(crate::util::output(
        Command::new("pdftotext").args(["-bbox"]).arg(path).arg("-"),
    )?)?;
    let xml = roxmltree::Document::parse_with_options(
        &bbox,
        roxmltree::ParsingOptions {
            allow_dtd: true,
            ..Default::default()
        },
    )?;
    for page in xml.descendants().filter(|n| n.tag_name().name() == "page") {
        let width = page.attribute("width").unwrap().parse::<f64>()?;
        let height = page.attribute("height").unwrap().parse::<f64>()?;
        for word in page.descendants().filter(|n| n.tag_name().name() == "word") {
            for (attr, limit) in [
                ("xMin", width),
                ("xMax", width),
                ("yMin", height),
                ("yMax", height),
            ] {
                let n = word.attribute(attr).unwrap().parse::<f64>()?;
                ensure!(
                    n >= -1. && n <= limit + 1.,
                    "PDF text outside page: {}",
                    word.text().unwrap_or("")
                );
            }
        }
    }
    println!(
        "Validated {} searchable A4 pages, {} bookmarks, embedded fonts, {internal} internal links, {external} external links",
        pages.len(),
        titles.len()
    );
    Ok(())
}
pub fn check_pdf_layout(root: &Path) -> Result<()> {
    let temp = tempfile::tempdir()?;
    let source = temp.path().join("layout.md");
    let sample = "# Layout sample\n\nLAYOUT ORIGIN\n\n| Malayalam | English |\n|---|---|\n| നമസ്കാരം | Hello |\n| പഠിക്കുന്നു | Is studying |\n\n## Vocabulary\n\n| Malayalam | English |\n|---|---|\n| അവൻ | Normal meaning |\n| ആഘോഷിക്കപ്പെടുക (past: ആഘോഷിക്കപ്പെട്ടു) | Long meaning |\n";
    fs::write(&source, compact(sample, "lesson20.md"))?;
    let html = temp.path().join("layout.html");
    run(Command::new("pandoc")
        .arg(&source)
        .args([
            "--from=markdown-auto_identifiers",
            "--to=html5",
            "--standalone",
            "--metadata=title:Layout sample",
        ])
        .arg(format!(
            "--template={}",
            root.join("templates/pdf.html").display()
        ))
        .arg("-o")
        .arg(&html))?;
    let base = url::Url::from_directory_path(root.join("docs")).unwrap();
    let css = fs::read_to_string(root.join("templates/pdf.css"))?;
    let css = css.replace("url('../docs/", &format!("url('{base}"));
    let input=fs::read_to_string(&html)?.replace("</head>",&format!("<style>{css}\n.vocabulary-list{{column-count:1;width:81.5mm}}table tbody td:last-child{{text-align:right}}</style></head>"));
    ensure!(
        !input.contains("max-width: 36em"),
        "browser template styles leaked into PDF"
    );
    fs::write(&html, input)?;
    let pdf = temp.path().join("layout.pdf");
    print_pdf(&html, &pdf, None)?;
    let bbox = String::from_utf8(crate::util::output(
        Command::new("pdftotext").arg("-bbox").arg(&pdf).arg("-"),
    )?)?;
    let doc = roxmltree::Document::parse_with_options(
        &bbox,
        roxmltree::ParsingOptions {
            allow_dtd: true,
            ..Default::default()
        },
    )?;
    let words: Vec<_> = doc
        .descendants()
        .filter(|n| n.tag_name().name() == "word")
        .collect();
    let origin = words
        .iter()
        .find(|n| n.text() == Some("LAYOUT"))
        .ok_or_else(|| anyhow::anyhow!("missing layout text"))?;
    ensure!(
        (origin.attribute("xMin").unwrap().parse::<f64>()? - 20. * 72. / 25.4).abs() < 1.,
        "unexpected body margin"
    );
    let hello = words.iter().find(|n| n.text() == Some("Hello")).unwrap();
    let right = 595.28 - 21.5 * 72. / 25.4;
    ensure!(
        (hello.attribute("xMax").unwrap().parse::<f64>()? - right).abs() < 1.,
        "table does not fill text area"
    );
    let normal = words.iter().find(|n| n.text() == Some("Normal")).unwrap();
    let long = words.iter().find(|n| n.text() == Some("Long")).unwrap();
    ensure!(
        (normal.attribute("xMin").unwrap().parse::<f64>()?
            - long.attribute("xMin").unwrap().parse::<f64>()?)
        .abs()
            < 1.,
        "vocabulary meanings misaligned"
    );
    println!("PDF margins, full-width tables, and short/long vocabulary alignment passed");
    Ok(())
}

#[cfg(all(test, unix))]
mod browser_tests {
    use super::*;

    #[test]
    fn browser_exit_reports_status_and_stderr() {
        let profile = tempfile::tempdir().unwrap();
        let mut command = Command::new("sh");
        command.args(["-c", "echo 'No usable sandbox!' >&2; exit 23"]);
        let error = start_browser(command, profile.path(), Duration::from_secs(5))
            .err()
            .expect("browser should fail")
            .to_string();
        assert!(error.contains("exited before becoming ready"));
        assert!(error.contains("23"));
        assert!(error.contains("No usable sandbox!"));
    }

    #[test]
    fn browser_startup_timeout_retains_diagnostics() {
        let profile = tempfile::tempdir().unwrap();
        let mut command = Command::new("sh");
        command.args([
            "-c",
            "echo 'waiting for browser initialization' >&2; exec sleep 30",
        ]);
        let error = start_browser(command, profile.path(), Duration::from_millis(500))
            .err()
            .expect("browser should time out")
            .to_string();
        assert!(error.contains("did not become ready"));
        assert!(error.contains("waiting for browser initialization"));
    }

    #[test]
    fn browser_startup_reads_control_port() {
        let profile = tempfile::tempdir().unwrap();
        let mut command = Command::new("sh");
        command.args(["-c", "printf '4321\\n/devtools/browser/test\\n' > \"$1/DevToolsActivePort\"; exec sleep 30", "fake-chrome"])
            .arg(profile.path());
        let (_browser, port) =
            start_browser(command, profile.path(), Duration::from_secs(5)).unwrap();
        assert_eq!(port, 4321);
    }
}
