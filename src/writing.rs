//! Editable writing geometry is data; Rust renders the diagrams and chapter grids.
use crate::util::*;
use anyhow::{Result, ensure};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path};
#[derive(Clone)]
struct Xml {
    tag: String,
    attrs: Vec<(String, String)>,
    text: String,
    children: Vec<Xml>,
}
impl Xml {
    fn new(tag: &str, attrs: &[(&str, String)]) -> Self {
        Self {
            tag: tag.into(),
            attrs: attrs
                .iter()
                .map(|(k, v)| (k.to_string(), v.clone()))
                .collect(),
            text: String::new(),
            children: vec![],
        }
    }
    fn child(&mut self, tag: &str, attrs: &[(&str, String)], text: &str) {
        let mut x = Self::new(tag, attrs);
        x.text = text.into();
        self.children.push(x);
    }
    fn render(&self, level: usize) -> String {
        let pad = "  ".repeat(level);
        let mut out = format!("{pad}<{}", self.tag);
        for (k, v) in &self.attrs {
            out += &format!(" {k}=\"{}\"", esc(v));
        }
        if self.children.is_empty() && self.text.is_empty() {
            return out + " />\n";
        }
        out += '>'.to_string().as_str();
        if !self.text.is_empty() {
            out += &esc(&self.text);
        }
        if !self.children.is_empty() {
            out += '\n'.to_string().as_str();
            for child in &self.children {
                out += &child.render(level + 1);
            }
            out += &pad;
        }
        out += &format!("</{}>\n", self.tag);
        out
    }
}
fn a(key: &str, value: impl ToString) -> (&str, String) {
    (key, value.to_string())
}
fn draw(key: &str, shape: &Value) -> Xml {
    let mut group = Xml::new("g", &[a("data-symbol", key)]);
    let mut ink = Xml::new(
        "g",
        &[
            a("class", "writing-ink"),
            a("fill", "none"),
            a("stroke", "currentColor"),
            a("stroke-width", 4),
            a("stroke-linecap", "round"),
            a("stroke-linejoin", "round"),
            a("style", "stroke-width:var(--writing-stroke-width,4)"),
        ],
    );
    let mut guides = Xml::new(
        "g",
        &[
            a("class", "writing-guides"),
            a("fill", "none"),
            a("stroke", "#557467"),
            a("stroke-width", "1.6"),
            a("stroke-linecap", "round"),
            a("stroke-linejoin", "round"),
            a("style", "stroke:var(--writing-guide-ink,#557467)"),
        ],
    );
    let mut labels = Xml::new(
        "g",
        &[
            a("class", "writing-labels"),
            a("font-family", "sans-serif"),
            a("font-size", 13),
            a("text-anchor", "middle"),
            a("fill", "#557467"),
            a("style", "fill:var(--writing-guide-ink,#557467)"),
        ],
    );
    let mut defs = Xml::new("defs", &[]);
    let mut marker = Xml::new(
        "marker",
        &[
            a("id", format!("{key}-arrow")),
            a("markerUnits", "userSpaceOnUse"),
            a("viewBox", "0 0 10 10"),
            a("refX", 8),
            a("refY", 5),
            a("markerWidth", 10),
            a("markerHeight", 10),
            a("orient", "auto"),
        ],
    );
    marker.child(
        "path",
        &[
            a("d", "M1 1 L8 5 L1 9"),
            a("fill", "none"),
            a("stroke", "#557467"),
            a("stroke-width", "1.6"),
            a("style", "stroke:var(--writing-guide-ink,#557467)"),
        ],
        "",
    );
    defs.children.push(marker.clone());
    let mut number = 0;
    for (i, stroke) in arr(&shape["strokes"]).iter().enumerate() {
        let mut attrs = vec![
            a("d", s(&stroke["path"])),
            a("data-part", s(&stroke["name"])),
        ];
        let transform = stroke["transform"].as_str();
        if let Some(t) = transform {
            attrs.push(a("transform", t));
        }
        let has_guide = !s(&stroke["guide"]).is_empty();
        if has_guide {
            number += 1;
            attrs.push(a("data-movement", number));
        }
        ink.child("path", &attrs, "");
        if !has_guide {
            continue;
        }
        let mut arrow_id = format!("{key}-arrow");
        if !stroke["arrow_size"].is_null() {
            arrow_id = format!("{key}-arrow-{i}");
            let mut small = marker.clone();
            for (k, v) in &mut small.attrs {
                if k == "id" {
                    *v = arrow_id.clone();
                } else if k == "markerWidth" || k == "markerHeight" {
                    *v = stroke["arrow_size"].to_string();
                }
            }
            defs.children.push(small);
        }
        let mut attrs = vec![];
        if let Some(t) = transform {
            attrs.push(a("transform", t));
        }
        attrs.push(a("data-movement", number));
        let mut guide = Xml::new("g", &attrs);
        guide.child(
            "path",
            &[
                a("d", s(&stroke["guide"])),
                a("marker-end", format!("url(#{arrow_id})")),
            ],
            "",
        );
        guides.children.push(guide);
        let mut label = Xml::new("g", &attrs);
        let y = stroke["label"][1].as_f64().unwrap() + 4.;
        label.child(
            "text",
            &[
                a("x", &stroke["label"][0]),
                a("y", y),
                a("paint-order", "stroke fill"),
                a("stroke", "#fff"),
                a("stroke-width", 3),
                a("stroke-linejoin", "round"),
                a("style", "stroke:var(--writing-background,#fff)"),
            ],
            &number.to_string(),
        );
        labels.children.push(label);
    }
    guides.children.insert(0, defs);
    group.children.extend([ink, guides, labels]);
    group
}
fn svg(key: &str, shape: &Value) -> String {
    let top = shape["viewTop"].as_i64().unwrap_or(-55);
    let width = shape["width"].as_i64().unwrap();
    let height = shape["height"].as_i64().unwrap();
    let mut root = Xml::new(
        "svg",
        &[
            a("xmlns", "http://www.w3.org/2000/svg"),
            a(
                "viewBox",
                format!("-55 {top} {} {}", width + 110, height + 55 - top),
            ),
            a("role", "img"),
            a("aria-labelledby", format!("{key}-title {key}-description")),
            a("data-source-page", &shape["page"]),
        ],
    );
    root.child(
        "title",
        &[a("id", format!("{key}-title"))],
        &format!("{} — writing diagram", s(&shape["symbol"])),
    );
    let reference = if shape["form"] == "modern" {
        format!(
            "Modern form of {}, with editorial drawing movements. Moag PDF page {} contains an older form.",
            s(&shape["symbol"]),
            shape["page"]
        )
    } else {
        format!("Redrawn from Moag, PDF page {}.", shape["page"])
    };
    if let Some(form) = shape["form"].as_str() {
        root.attrs.push(("data-form".into(), form.into()));
    }
    root.child("desc",&[a("id",format!("{key}-description"))],&(reference+" Separate centerline paths represent the letter; thin arrows and numbers show writing movements."));
    root.children.push(draw(key, shape));
    root.render(0)
}
fn g6(v: f64) -> String {
    let decimals = (5. - v.abs().log10().floor()).max(0.) as usize;
    format!("{v:.decimals$}")
        .trim_end_matches('0')
        .trim_end_matches('.')
        .to_string()
}
fn table(page: &str, keys: &Value, shapes: &Value) -> String {
    let n = arr(keys).len();
    let mut root = Xml::new(
        "svg",
        &[
            a("xmlns", "http://www.w3.org/2000/svg"),
            a("viewBox", format!("0 0 860 {}", n.div_ceil(2) * 355)),
            a("role", "img"),
            a(
                "aria-label",
                format!("Malayalam writing symbols, Moag PDF page {page}"),
            ),
        ],
    );
    for (i, k) in arr(keys).iter().enumerate() {
        let key = s(k);
        let shape = &shapes[key];
        let x = (i % 2) as f64 * 430.;
        let y = (i / 2) as f64 * 355.;
        let width = shape["width"].as_f64().unwrap();
        let height = shape["height"].as_f64().unwrap();
        let scale = 1f64.min(380. / (width + 110.)).min(295. / (height + 110.));
        let ox = x + (430. - width * scale) / 2.;
        let oy = y + 55. + (-55. - shape["viewTop"].as_f64().unwrap_or(-55.)).max(0.) * scale;
        let mut group = Xml::new(
            "g",
            &[a(
                "transform",
                format!("translate({} {}) scale({})", g6(ox), g6(oy), g6(scale)),
            )],
        );
        group.children.push(draw(key, shape));
        root.children.push(group);
        root.child(
            "text",
            &[
                a("x", format!("{:.1}", x + 215.)),
                a("y", y + 343.),
                a("font-size", 22),
                a("text-anchor", "middle"),
            ],
            s(&shape["caption"]),
        );
    }
    root.render(0)
}
pub fn build(root: &Path, check: bool) -> Result<()> {
    let data = read_json(root.join("data/writing/models.json"))?;
    let shapes = &data["shapes"];
    let mut chapter = fs::read_to_string(root.join("docs/symbols.md"))?;
    let mut manifest = vec![];
    for (page, keys) in data["tables"].as_object().unwrap() {
        let mut grid = format!("<!-- writing-grid:{page} -->\n<div class=\"writing-grid\">");
        for key in arr(keys) {
            let key = s(key);
            let shape = &shapes[key];
            let caption = format!(
                "{}{}",
                if key.starts_with("sign-") { "◌" } else { "" },
                s(&shape["caption"])
            );
            grid += &format!(
                "\n  <figure class=\"writing-card\" data-writing-symbol=\"{key}\">\n    <img src=\"assets/writing/symbols/{key}.svg\" alt=\"Writing movements for {}\" loading=\"lazy\">\n    <figcaption lang=\"ml\">{}</figcaption>\n  </figure>",
                esc(s(&shape["symbol"])),
                esc(&caption)
            );
            write(
                root.join(format!("docs/assets/writing/symbols/{key}.svg")),
                &svg(key, shape),
                check,
            )?;
            manifest.push(json!({"id":key,"symbol":shape["symbol"],"sourcePage":shape["page"],"movements":arr(&shape["strokes"]).iter().filter(|x|!s(&x["guide"]).is_empty()).count()}));
        }
        grid += "\n</div>\n<!-- /writing-grid -->";
        let block = re(&format!(
            "(?s)<!-- writing-grid:{page} -->.*?<!-- /writing-grid -->"
        ));
        ensure!(block.is_match(&chapter), "missing grid {page}");
        chapter = block.replace(&chapter, regex::NoExpand(&grid)).into_owned();
        write(
            root.join(format!("docs/assets/writing/front-writing-{page:0>3}.svg")),
            &table(page, keys, shapes),
            check,
        )?;
    }
    write(root.join("docs/symbols.md"), &chapter, check)?;
    write_json(
        root.join("docs/assets/writing/manifest.json"),
        &json!(manifest),
        check,
    )?;
    validate(root)?;
    println!("93 writing models and 20 tables checked");
    Ok(())
}
pub fn validate(root: &Path) -> Result<()> {
    let data = read_json(root.join("data/writing/models.json"))?;
    let chapter = fs::read_to_string(root.join("docs/symbols.md"))?;
    let expected: BTreeSet<_> = data["shapes"]
        .as_object()
        .unwrap()
        .keys()
        .cloned()
        .collect();
    let actual: BTreeSet<_> = re(r#"data-writing-symbol="([^"]+)""#)
        .captures_iter(&chapter)
        .map(|c| c[1].to_string())
        .collect();
    ensure!(expected == actual, "writing chapter coverage mismatch");
    for key in expected {
        let text = fs::read_to_string(root.join(format!("docs/assets/writing/symbols/{key}.svg")))?;
        let xml = roxmltree::Document::parse(&text)?;
        let top = xml.root_element();
        let shape = &data["shapes"][&key];
        ensure!(
            top.attribute("data-source-page") == Some(shape["page"].to_string().as_str()),
            "wrong writing source page"
        );
        ensure!(
            !xml.descendants()
                .any(|n| ["script", "image"].contains(&n.tag_name().name())),
            "raster/script in diagram"
        );
        for class in ["writing-ink", "writing-guides", "writing-labels"] {
            ensure!(
                xml.descendants()
                    .filter(|n| n.attribute("class") == Some(class))
                    .count()
                    == 1,
                "missing independent layer"
            );
        }
        let numbers: Vec<_> = xml
            .descendants()
            .filter(|n| n.tag_name().name() == "path" && n.attribute("data-movement").is_some())
            .map(|n| n.attribute("data-movement").unwrap().parse::<usize>())
            .collect::<std::result::Result<_, _>>()?;
        let count = arr(&shape["strokes"])
            .iter()
            .filter(|s1| !s(&s1["guide"]).is_empty())
            .count();
        ensure!(
            numbers == (1..=count).collect::<Vec<_>>(),
            "wrong movement sequence: {key}"
        );
        ensure!(
            xml.descendants()
                .filter(|n| n.tag_name().name() == "text")
                .count()
                == count,
            "wrong movement labels: {key}"
        );
    }
    Ok(())
}
