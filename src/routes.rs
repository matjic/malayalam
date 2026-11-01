use anyhow::{Result, bail};
use std::collections::BTreeMap;
use url::Url;

/// A deployment prefix is explicit, including for GitHub project sites.
pub fn base_path(base: &str) -> Result<String> {
    if !base.starts_with('/')
        || base.contains(['?', '#', '\\'])
        || !base
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"/-_.".contains(&c))
        || base.split('/').any(|p| matches!(p, "." | ".."))
        || base.starts_with("//")
    {
        bail!("base must be a local absolute path without traversal, query or fragment");
    }
    Ok(format!("{}/", base.trim_end_matches('/')))
}

pub fn page_path(stem: &str, base: &str) -> String {
    if stem == "README" {
        base.into()
    } else {
        format!("{base}{stem}/")
    }
}

/// Ordinary anchors/assets stay distinct from Markdown page routes.
pub fn local_link(
    href: &str,
    current: &str,
    routes: &BTreeMap<String, String>,
    base: &str,
) -> Result<String> {
    if href.is_empty() {
        return Ok(href.into());
    }
    if href.starts_with('#') && !href.starts_with("#/") {
        return Ok(href.into());
    }
    if href.starts_with("//") || Url::parse(href).is_ok() {
        return Ok(href.into());
    }
    if let Some(repository_file) = href.strip_prefix("../")
        && !repository_file.starts_with("docs/")
    {
        return Ok(format!(
            "https://github.com/matjic/malayalam/blob/main/{repository_file}"
        ));
    }
    if let Some(old) = href.strip_prefix("#/") {
        return legacy_link(old, routes, base)
            .ok_or_else(|| anyhow::anyhow!("unknown legacy route: {href}"));
    }
    // Markdown sources live at one level. Root all asset links at the deploy
    // prefix, so a lesson's trailing slash cannot change audio/image paths.
    let parsed = Url::parse("https://content.invalid/")?.join(href)?;
    let path = parsed.path().trim_start_matches('/');
    let query = parsed.query().map(|q| format!("?{q}")).unwrap_or_default();
    let fragment = parsed
        .fragment()
        .map(|f| format!("#{f}"))
        .unwrap_or_default();
    if path.ends_with(".md") {
        let stem = path.trim_start_matches("docs/").trim_end_matches(".md");
        if let Some(route) = routes.get(stem) {
            return Ok(format!("{route}{query}{fragment}"));
        }
        if path.starts_with('_') || path.starts_with("assets/") {
            return Ok(format!("{base}{path}{query}{fragment}"));
        }
        bail!("{current}: unknown Markdown page {href}");
    }
    Ok(format!("{base}{path}{query}{fragment}"))
}

pub fn legacy_link(old: &str, routes: &BTreeMap<String, String>, _base: &str) -> Option<String> {
    let parsed = Url::parse(&format!("https://legacy.invalid/{old}")).ok()?;
    if parsed.host_str()? != "legacy.invalid" {
        return None;
    }
    let stem = parsed.path().trim_matches('/').trim_end_matches(".md");
    let stem = if stem.is_empty() || stem.eq_ignore_ascii_case("readme") {
        "README"
    } else {
        stem
    };
    let mut target = Url::parse("https://legacy.invalid/")
        .ok()?
        .join(routes.get(stem)?)
        .ok()?;
    let mut anchor = parsed.fragment().map(str::to_owned);
    for (key, value) in parsed.query_pairs() {
        if key == "id" {
            if anchor.is_none() {
                anchor = Some(value.into_owned());
            }
        } else {
            target.query_pairs_mut().append_pair(&key, &value);
        }
    }
    target.set_fragment(anchor.as_deref());
    Some(format!(
        "{}{}{}",
        target.path(),
        target.query().map(|q| format!("?{q}")).unwrap_or_default(),
        target
            .fragment()
            .map(|f| format!("#{f}"))
            .unwrap_or_default()
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    fn routes() -> BTreeMap<String, String> {
        [
            ("README".into(), "/malayalam/".into()),
            ("lesson8".into(), "/malayalam/lesson8/".into()),
        ]
        .into()
    }
    #[test]
    fn fragments_and_base_paths() {
        assert_eq!(
            legacy_link(
                "lesson8?id=section-8-1&s=pronouns",
                &routes(),
                "/malayalam/"
            ),
            Some("/malayalam/lesson8/?s=pronouns#section-8-1".into())
        );
        assert_eq!(
            legacy_link("README.md", &routes(), "/malayalam/"),
            Some("/malayalam/".into())
        );
        assert_eq!(
            local_link("#section-8-1", "lesson8", &routes(), "/malayalam/").unwrap(),
            "#section-8-1"
        );
        assert_eq!(
            local_link("assets/audio/a.mp3", "lesson8", &routes(), "/malayalam/").unwrap(),
            "/malayalam/assets/audio/a.mp3"
        );
        assert_eq!(
            local_link("lesson8.md#section-8-1", "README", &routes(), "/malayalam/").unwrap(),
            "/malayalam/lesson8/#section-8-1"
        );
    }
    #[test]
    fn prefixes_and_unknown_routes_are_checked() {
        for bad in [
            "https://evil.invalid/",
            "//evil",
            "/../",
            "/a?b",
            "/a#b",
            "/a\" onload=\"bad/",
        ] {
            assert!(base_path(bad).is_err());
        }
        assert!(legacy_link("unknown", &routes(), "/").is_none());
        assert!(local_link("missing.md", "README", &routes(), "/").is_err());
    }
}
