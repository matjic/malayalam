use anyhow::{Context, Result, bail};
use lol_html::{RewriteStrSettings, element, html_content::ContentType, rewrite_str};
use pulldown_cmark::{Event, Parser, Tag, TagEnd, html};
use serde::Serialize;
use std::{
    cell::RefCell,
    collections::{BTreeMap, BTreeSet},
    fs,
    hash::{DefaultHasher, Hasher},
    path::Path,
    rc::Rc,
};
use url::Url;
use walkdir::WalkDir;

use crate::{
    content::{Book, Page, markdown_options},
    routes::{base_path, local_link},
};

pub fn escape(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
}

pub fn render_markdown(source: &str, page: Option<&Page>) -> String {
    let mut heading = 0;
    let events = Parser::new_ext(source, markdown_options()).map(|event| match event {
        Event::Start(Tag::Heading {
            level,
            id,
            classes,
            attrs,
        }) => {
            if let Some(page) = page {
                let info = &page.headings[heading];
                heading += 1;
                Event::Start(Tag::Heading {
                    level,
                    id: info.owned_id.then(|| info.id.clone().into()),
                    classes,
                    attrs,
                })
            } else {
                Event::Start(Tag::Heading {
                    level,
                    id,
                    classes,
                    attrs,
                })
            }
        }
        other => other,
    });
    let mut rendered = String::new();
    html::push_html(&mut rendered, events);
    rendered
}

fn rewrite_links(source: &str, page: &Page, book: &Book, base: &str) -> Result<String> {
    let output = rewrite_str(source, RewriteStrSettings::new()
        .append_element_content_handler(element!("a[href], img[src], audio[src], video[src], source[src], iframe[src], [data-audio-src], [data-row-audio-src]", |el| {
            for attr in ["href", "src", "data-audio-src", "data-row-audio-src"] {
                if let Some(value) = el.get_attribute(attr) {
                    let rewritten = local_link(&value, &page.stem, &book.routes, base)?;
                    el.set_attribute(attr, &rewritten)?;
                }
            }
            Ok(())
        })))?;
    Ok(output)
}

fn article(page: &Page, book: &Book, base: &str) -> Result<String> {
    let rendered = rewrite_links(
        &render_markdown(&page.markdown, Some(page)),
        page,
        book,
        base,
    )?;
    let mut heading = 0;
    Ok(rewrite_str(
        &rendered,
        RewriteStrSettings::new().append_element_content_handler(element!(
            "h1, h2, h3, h4, h5, h6",
            |el| {
                let info = &page.headings[heading];
                heading += 1;
                let aliases = info
                    .aliases
                    .iter()
                    .map(|id| {
                        format!(
                            "<span class=\"legacy-anchor\" id=\"{}\"></span>",
                            escape(id)
                        )
                    })
                    .collect::<String>();
                el.prepend(
                    &format!(
                        "{aliases}<a href=\"#{}\" data-id=\"{}\" class=\"anchor\"><span>",
                        escape(&info.id),
                        escape(&info.id)
                    ),
                    ContentType::Html,
                );
                el.append("</span></a>", ContentType::Html);
                Ok(())
            }
        )),
    )?)
}

fn sidebar(page: &Page, book: &Book, base: &str) -> Result<String> {
    let rendered = rewrite_links(&render_markdown(&book.sidebar, None), page, book, base)?;
    let mut toc = String::from("<ul class=\"app-sub-sidebar\">");
    let (mut parent, mut children) = (false, false);
    for heading in page
        .headings
        .iter()
        .filter(|h| h.level == 2 || h.level == 3)
    {
        if heading.level == 2 {
            if children {
                toc.push_str("</ul>");
                children = false;
            }
            if parent {
                toc.push_str("</li>");
            }
            parent = true;
        } else if parent && !children {
            toc.push_str("<ul class=\"app-sub-sidebar\">");
            children = true;
        }
        toc.push_str(&format!(
            "<li class=\"toc-level-{}\"><a class=\"section-link\" href=\"#{}\">{}</a>",
            heading.level,
            escape(&heading.id),
            escape(&heading.title)
        ));
        if heading.level == 3 {
            toc.push_str("</li>");
        }
    }
    if children {
        toc.push_str("</ul>");
    }
    if parent {
        toc.push_str("</li>");
    }
    toc.push_str("</ul>");
    Ok(rewrite_str(
        &rendered,
        RewriteStrSettings::new().append_element_content_handler(element!("a[href]", |el| {
            if el.get_attribute("href").as_deref() == Some(&page.route) {
                el.set_attribute("class", "active")?;
                el.set_attribute("aria-current", "page")?;
                el.after(&toc, ContentType::Html);
            }
            Ok(())
        })),
    )?)
}

fn document(
    page: &Page,
    book: &Book,
    base: &str,
    body: &str,
    runtime: &BTreeMap<String, String>,
) -> Result<String> {
    let legacy = &runtime["legacy-redirect"];
    let scripts = [
        "page",
        "navigation",
        "writing",
        "audio",
        "vocabulary-glossary",
        "search",
    ]
    .iter()
    .map(|name| format!("<script defer src=\"{}\"></script>", runtime[*name]))
    .collect::<String>();
    let styles = [
        "vue",
        "navigation",
        "reading",
        "writing",
        "footer",
        "audio",
        "vocabulary-glossary",
        "site",
    ]
    .iter()
    .map(|name| format!("<link rel=\"stylesheet\" href=\"{base}assets/{name}.css\">"))
    .collect::<Vec<_>>()
    .join("\n");
    let routes = serde_json::to_string(&book.routes)?.replace('<', "\\u003c");
    let license = if page.stem.starts_with("practice") {
        "https://creativecommons.org/licenses/by-sa/4.0/"
    } else {
        "https://github.com/matjic/malayalam/blob/main/LICENSE.md"
    };
    let footer = format!(
        "<footer class=\"site-footer\">An open-source digital edition · <a href=\"https://github.com/matjic/malayalam\">Source on GitHub</a> · <a href=\"{license}\">{}License</a></footer>",
        if page.stem.starts_with("practice") {
            "Supplement "
        } else {
            ""
        }
    );
    let description = escape(&page.title);
    let sidebar = sidebar(page, book, base)?;
    Ok(format!(
        r##"<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
<title>{description} — Malayalam: A University Course</title><meta name="description" content="{description}">
<link rel="canonical" href="https://ml.matj.io{}">{styles}
<script id="site-routes" type="application/json">{routes}</script>
<script type="module" src="{legacy}" data-base="{base}"></script>
</head><body class="ready sticky" data-page="{}" data-base="{base}"><main>
<button class="sidebar-toggle" type="button" aria-label="Toggle navigation" aria-controls="site-navigation"><div class="sidebar-toggle-button" aria-hidden="true"><span></span><span></span><span></span></div></button>
<aside class="sidebar" id="site-navigation" aria-label="Site navigation">
<div class="search"><div class="input-wrap"><input type="search" aria-label="Search text" placeholder="Type to search"><button class="clear-button" type="button" aria-label="Clear search"><svg width="26" height="24" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="#ccc"/><path stroke="white" stroke-width="2" d="M8.25,8.25,15.75,15.75 M8.25,15.75,15.75,8.25"/></svg></button></div><div class="results-panel" aria-live="polite"></div></div>
<h1 class="app-name"><a class="app-name-link" href="{base}">Malayalam: A University Course</a></h1><div class="sidebar-nav">{sidebar}</div></aside>
<section class="content"><article class="markdown-section" id="main">{body}{footer}</article></section></main>
{scripts}
</body></html>"##,
        escape(&page.route),
        escape(&page.stem)
    ))
}

#[derive(Serialize)]
pub struct SearchEntry {
    title: String,
    url: String,
    body: String,
}

fn search_entries(page: &Page) -> Vec<SearchEntry> {
    let mut entries = vec![];
    let mut title = page.title.clone();
    let mut url = page.route.clone();
    let mut text = String::new();
    let mut heading = 0;
    let mut in_heading = false;
    for event in Parser::new_ext(&page.markdown, markdown_options()) {
        match event {
            Event::Start(Tag::Heading { .. }) => {
                if !text.trim().is_empty() {
                    entries.push(SearchEntry {
                        title,
                        url,
                        body: text.trim().into(),
                    });
                }
                text = String::new();
                let h = &page.headings[heading];
                heading += 1;
                title = if h.level == 1 {
                    page.title.clone()
                } else {
                    format!("{} — {}", page.title, h.title)
                };
                url = format!("{}#{}", page.route, h.id);
                in_heading = true;
            }
            Event::End(TagEnd::Heading(_)) => in_heading = false,
            Event::Text(t) | Event::Code(t) if !in_heading => {
                text.push_str(&t);
                text.push(' ');
            }
            Event::SoftBreak | Event::HardBreak => text.push(' '),
            _ => {}
        }
    }
    if !text.trim().is_empty() {
        entries.push(SearchEntry {
            title,
            url,
            body: text.trim().into(),
        });
    }
    entries
}

pub fn build(root: &Path, output: &Path, base: &str) -> Result<()> {
    let base = base_path(base)?;
    let book = Book::load(root, &base)?;
    fs::create_dir_all(output)?;
    let output = output.canonicalize()?;
    let docs = root.join("docs").canonicalize()?;
    if output.starts_with(&docs) || docs.starts_with(&output) {
        bail!("output must be separate from source docs");
    }
    for entry in WalkDir::new(&docs)
        .follow_links(false)
        .into_iter()
        .filter_entry(|entry| {
            entry.depth() == 0 || !entry.file_name().to_string_lossy().starts_with('.')
        })
    {
        let entry = entry?;
        if entry.file_type().is_symlink() {
            bail!(
                "source symlinks are not supported: {}",
                entry.path().display()
            );
        }
        if !entry.file_type().is_file() {
            continue;
        }
        let relative = entry.path().strip_prefix(&docs)?;
        if relative == Path::new("index.html") {
            continue;
        }
        // Source Markdown and standalone review pages remain downloadable.
        let target = output.join(relative);
        fs::create_dir_all(target.parent().unwrap())?;
        fs::copy(entry.path(), target)?;
    }
    let original = root.join("Moag-Malayalam-CompleteTextbook.pdf");
    if original.is_file() {
        fs::copy(original, output.join("Moag-Malayalam-CompleteTextbook.pdf"))?;
    }
    for name in ["malayalam.epub", "malayalam.pdf"] {
        let artifact = root.join("dist").join(name);
        if artifact.is_file() {
            fs::copy(artifact, output.join(name))?;
        }
    }
    // New file names prevent cached Docsify-era hooks from running on static
    // pages. Content changes also invalidate each script independently.
    fs::create_dir_all(output.join("assets/runtime"))?;
    let mut runtime = BTreeMap::new();
    for name in [
        "page",
        "navigation",
        "writing",
        "audio",
        "vocabulary-glossary",
        "search",
        "legacy-redirect",
    ] {
        let source = fs::read(root.join(format!("docs/assets/{name}.js")))?;
        let mut hash = DefaultHasher::new();
        hash.write(&source);
        let filename = format!("{name}-{:016x}.js", hash.finish());
        fs::write(output.join("assets/runtime").join(&filename), source)?;
        runtime.insert(name.into(), format!("{base}assets/runtime/{filename}"));
    }
    let mut search = vec![];
    for page in book.pages.values() {
        let body = article(page, &book, &base).with_context(|| page.stem.clone())?;
        let file = output
            .join(page.route.strip_prefix(&base).unwrap())
            .join("index.html");
        fs::create_dir_all(file.parent().unwrap())?;
        fs::write(file, document(page, &book, &base, &body, &runtime)?)?;
        search.extend(search_entries(page));
    }
    fs::write(
        output.join("assets/search-index.json"),
        serde_json::to_vec(&search)?,
    )?;
    fs::write(
        output.join("routes.json"),
        serde_json::to_vec_pretty(&book.routes)?,
    )?;
    fs::write(output.join(".nojekyll"), "")?;
    let mut not_found = book.pages["README"].clone();
    not_found.stem = "404".into();
    not_found.route = format!("{base}404.html");
    not_found.title = "Page not found".into();
    not_found.headings.clear();
    fs::write(
        output.join("404.html"),
        document(
            &not_found,
            &book,
            &base,
            &format!(
                "<h1>Page not found</h1><p>Visit the <a href=\"{base}contents/\">contents</a> to find a lesson.</p>"
            ),
            &runtime,
        )?,
    )?;
    check(&output, &base, false)?;
    println!(
        "Rendered {} pages; {} search sections; Docsify styles preserved.",
        book.pages.len(),
        search.len()
    );
    Ok(())
}

/// Validate final HTML, including links in raw HTML and media data attributes.
pub fn check(output: &Path, base: &str, require_exports: bool) -> Result<()> {
    let base = base_path(base)?;
    let routes: BTreeMap<String, String> =
        serde_json::from_slice(&fs::read(output.join("routes.json"))?)?;
    let origin = Url::parse("https://render.invalid/")?;
    let mut pages = BTreeMap::<String, BTreeSet<String>>::new();
    let mut links = Vec::new();
    for route in routes.values() {
        let file = output
            .join(route.strip_prefix(&base).context("route outside base")?)
            .join("index.html");
        let source = fs::read_to_string(&file)?;
        let ids = Rc::new(RefCell::new(BTreeSet::new()));
        let found_links = Rc::new(RefCell::new(Vec::<String>::new()));
        let id_set = ids.clone();
        let link_set = found_links.clone();
        rewrite_str(
            &source,
            RewriteStrSettings::new()
                .append_element_content_handler(element!("[id]", move |el| {
                    let id = el.get_attribute("id").unwrap();
                    if !id_set.borrow_mut().insert(id.clone()) {
                        return Err(format!("duplicate HTML id: {id}").into());
                    }
                    Ok(())
                }))
                .append_element_content_handler(element!(
                    "[href], [src], [data-audio-src], [data-row-audio-src]",
                    move |el| {
                        for attr in ["href", "src", "data-audio-src", "data-row-audio-src"] {
                            if let Some(value) = el.get_attribute(attr) {
                                link_set.borrow_mut().push(value);
                            }
                        }
                        Ok(())
                    }
                )),
        )
        .with_context(|| file.display().to_string())?;
        pages.insert(route.clone(), ids.borrow().clone());
        links.extend(
            found_links
                .borrow()
                .iter()
                .map(|link| (route.clone(), link.clone())),
        );
    }
    let mut errors = Vec::new();
    for (page, link) in &links {
        let current = origin.join(page)?;
        let target = current
            .join(link)
            .with_context(|| format!("{page}: {link}"))?;
        if target.origin() != origin.origin() {
            continue;
        }
        let path = target.path();
        if let Some(ids) = pages.get(path) {
            if let Some(fragment) = target.fragment().filter(|f| !f.is_empty()) {
                let decoded = percent_encoding::percent_decode_str(fragment).decode_utf8()?;
                if !ids.contains(decoded.as_ref()) {
                    errors.push(format!("{page}: missing anchor {link}"));
                }
            }
        } else {
            let Some(relative) = path.strip_prefix(&base) else {
                errors.push(format!("{page}: outside base: {link}"));
                continue;
            };
            if !require_exports && matches!(relative, "malayalam.epub" | "malayalam.pdf") {
                continue;
            }
            let decoded = percent_encoding::percent_decode_str(relative).decode_utf8()?;
            if !output.join(decoded.as_ref()).is_file() {
                errors.push(format!("{page}: missing asset {link}"));
            }
        }
    }
    if !errors.is_empty() {
        bail!("{} broken links:\n{}", errors.len(), errors.join("\n"));
    }
    println!(
        "Checked {} rendered pages and {} links/media references.",
        pages.len(),
        links.len()
    );
    Ok(())
}
