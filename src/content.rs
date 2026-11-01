use anyhow::{Context, Result, bail};
use pulldown_cmark::{Event, Options, Parser, Tag, TagEnd};
use regex::Regex;
use serde::Serialize;
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::Path,
};

use crate::routes::page_path;

#[derive(Clone, Debug, Serialize)]
pub struct Heading {
    pub level: u8,
    pub title: String,
    pub id: String,
    pub owned_id: bool,
    pub aliases: Vec<String>,
}

#[derive(Clone, Debug)]
pub struct Page {
    pub stem: String,
    pub markdown: String,
    pub title: String,
    pub route: String,
    pub headings: Vec<Heading>,
    pub anchors: BTreeSet<String>,
}

pub struct Book {
    pub pages: BTreeMap<String, Page>,
    pub routes: BTreeMap<String, String>,
    pub sidebar: String,
}

pub fn markdown_options() -> Options {
    Options::ENABLE_TABLES
        | Options::ENABLE_FOOTNOTES
        | Options::ENABLE_STRIKETHROUGH
        | Options::ENABLE_TASKLISTS
}

/// Docsify's readable heading aliases coexist with the source's stable anchors.
pub fn heading_slug(title: &str) -> String {
    let punctuation = "\\'!\"#$%&()*+,./:;<=>?@[]^`{|}~";
    let cleaned: String = title
        .trim()
        .chars()
        .filter(|c| {
            !matches!(*c as u32, 0x2000..=0x206f | 0x2e00..=0x2e7f) && !punctuation.contains(*c)
        })
        .map(|c| {
            if c.is_whitespace() {
                '-'
            } else {
                c.to_ascii_lowercase()
            }
        })
        .collect();
    let collapsed = Regex::new(r"-+").unwrap().replace_all(&cleaned, "-");
    if collapsed.starts_with(|c: char| c.is_ascii_digit()) {
        format!("_{collapsed}")
    } else {
        collapsed.into_owned()
    }
}

impl Page {
    pub fn parse(stem: &str, markdown: String, base: &str) -> Result<Self> {
        let explicit = Regex::new(r#"\bid="([^"]+)""#)?;
        let mut anchors: BTreeSet<String> = explicit
            .captures_iter(&markdown)
            .map(|m| m[1].to_owned())
            .collect();
        let explicit_anchors = anchors.clone();
        let mut headings = Vec::new();
        let mut current: Option<(u8, String)> = None;
        let mut used = BTreeMap::<String, usize>::new();
        for event in Parser::new_ext(&markdown, markdown_options()) {
            match event {
                Event::Start(Tag::Heading { level, .. }) => {
                    current = Some((level as u8, String::new()))
                }
                Event::Text(t) | Event::Code(t) => {
                    if let Some((_, title)) = &mut current {
                        title.push_str(&t);
                    }
                }
                Event::SoftBreak | Event::HardBreak => {
                    if let Some((_, title)) = &mut current {
                        title.push(' ');
                    }
                }
                Event::End(TagEnd::Heading(_)) => {
                    let (level, title) = current.take().unwrap();
                    let slug = heading_slug(&title);
                    let count = used.entry(slug.clone()).or_default();
                    let id = if *count == 0 {
                        slug
                    } else {
                        format!("{slug}-{}", count)
                    };
                    *count += 1;
                    let owned_id = !explicit_anchors.contains(&id);
                    anchors.insert(id.clone());
                    // Markdown links already in the book also use the unprefixed
                    // numeric slug; retain it alongside Docsify's `_123` alias.
                    let aliases = id
                        .strip_prefix('_')
                        .filter(|s| s.starts_with(|c: char| c.is_ascii_digit()))
                        .filter(|s| !anchors.contains(*s))
                        .map(|s| vec![s.to_owned()])
                        .unwrap_or_default();
                    anchors.extend(aliases.iter().cloned());
                    headings.push(Heading {
                        level,
                        title,
                        id,
                        owned_id,
                        aliases,
                    });
                }
                _ => {}
            }
        }
        let title = headings
            .iter()
            .find(|h| h.level == 1)
            .context("page needs an H1")?
            .title
            .clone();
        Ok(Self {
            stem: stem.into(),
            markdown,
            title,
            route: page_path(stem, base),
            headings,
            anchors,
        })
    }
}

impl Book {
    pub fn load(root: &Path, base: &str) -> Result<Self> {
        let mut pages: BTreeMap<String, Page> = BTreeMap::new();
        for entry in fs::read_dir(root.join("docs"))? {
            let path = entry?.path();
            if path.extension().and_then(|e| e.to_str()) != Some("md") {
                continue;
            }
            let stem = path
                .file_stem()
                .unwrap()
                .to_str()
                .context("non-UTF8 page name")?;
            if stem.starts_with('_') {
                continue;
            }
            if !stem.chars().all(|c| c.is_ascii_alphanumeric() || c == '-') {
                bail!("unsupported page name: {stem}");
            }
            pages.insert(
                stem.into(),
                Page::parse(stem, fs::read_to_string(&path)?, base)
                    .with_context(|| path.display().to_string())?,
            );
        }
        if !pages.contains_key("README") {
            bail!("missing home page");
        }
        let routes = pages
            .iter()
            .map(|(key, page)| (key.clone(), page.route.clone()))
            .collect();
        let sidebar = generate_sidebar(&pages)?;
        Ok(Self {
            pages,
            routes,
            sidebar,
        })
    }
}

fn title_case(text: &str) -> String {
    let mut previous_letter = false;
    text.chars()
        .flat_map(|c| {
            let result = if previous_letter {
                c.to_lowercase().collect::<String>()
            } else {
                c.to_uppercase().collect::<String>()
            };
            previous_letter = c.is_alphabetic();
            result.chars().collect::<Vec<_>>()
        })
        .collect()
}

pub fn generate_sidebar(pages: &BTreeMap<String, Page>) -> Result<String> {
    let source_page = Regex::new(r"Source: PDF page (\d+)")?;
    let mut book = Vec::new();
    for page in pages.values() {
        if let Some(first) = source_page
            .captures_iter(&page.markdown)
            .filter_map(|m| m[1].parse::<u32>().ok())
            .min()
        {
            book.push((first, page.stem.clone()));
        }
    }
    book.sort();
    let mut order = Vec::new();
    for (_, stem) in book {
        order.push(stem.clone());
        let practice = match stem.as_str() {
            "alphabet" => Some("practice-pronunciation"),
            "lesson2" => Some("practice-sandhi"),
            "lesson7" => Some("practice-dialogues"),
            _ => None,
        };
        if let Some(practice) = practice {
            if !pages.contains_key(practice) {
                bail!("missing practice lesson: {practice}");
            }
            order.push(practice.into());
        }
    }
    let link = |stem: &str| {
        let page = &pages[stem];
        let title = if page.title == page.title.to_uppercase() {
            title_case(&page.title)
        } else {
            page.title.clone()
        };
        format!("* [{title}]({stem}.md)")
    };
    let mut lines = vec![
        "<!-- Generated by cargo run -- sidebar; edit document titles instead. -->".into(),
        String::new(),
        "* [Home](README.md)".into(),
        "* [Contents](contents.md)".into(),
        "* [Reading the digital edition](digital-edition.md)".into(),
        "* [Practice lesson guide](practice.md)".into(),
    ];
    lines.extend(order.iter().map(|s| link(s)));
    let extras: Vec<_> = pages
        .keys()
        .filter(|s| {
            !order.contains(s)
                && ![
                    "README",
                    "contents",
                    "digital-edition",
                    "practice",
                    "technical-notes",
                ]
                .contains(&s.as_str())
        })
        .collect();
    if !extras.is_empty() {
        lines.extend([String::new(), "* Review and supporting material".into()]);
        lines.extend(extras.into_iter().map(|s| format!("  {}", link(s))));
    }
    if pages.contains_key("technical-notes") {
        lines.extend([String::new(), link("technical-notes")]);
    }
    Ok(lines.join("\n") + "\n")
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn source_anchors_survive_and_heading_ids_do_not_duplicate_them() {
        let page = Page::parse(
            "appendix-a",
            "<a id=\"appendix-a\"></a>\n# Appendix A\n\n## Words\n\n## Words\n".into(),
            "/",
        )
        .unwrap();
        assert!(!page.headings[0].owned_id);
        assert_eq!(page.headings[2].id, "words-1");
        assert!(page.anchors.contains("appendix-a"));
    }
}
