use anyhow::{Result, bail};
use clap::Parser;
use malayalam::{routes::base_path, server, site};
use std::path::PathBuf;
#[derive(Parser)]
#[command(about = "Malayalam book publishing and source maintenance")]
struct Args {
    /// site, check-site, serve, sidebar, navigation, check-reading, vocabulary,
    /// glossary, anki, audit-prompts, writing, audio, word-audio, letter-audio,
    /// epub, pdf, check-pdf, check-pdf-layout, check-lists, transcribe,
    /// review-audio, collect, archive, import-story, assemble-books
    command: String,
    #[arg(long)]
    input: Option<PathBuf>,
    #[arg(long)]
    model: Option<PathBuf>,
    #[arg(long)]
    manifest: Option<PathBuf>,
    #[arg(long)]
    scope: Option<String>,
    #[arg(long)]
    url: Vec<String>,
    #[arg(long, default_value_t = 60)]
    limit: usize,
    #[arg(long, default_value = "whisper-cli")]
    engine: String,
    #[arg(long, default_value = "ml")]
    language: String,
    #[arg(long,default_value=env!("CARGO_MANIFEST_DIR"))]
    root: PathBuf,
    #[arg(long)]
    output: Option<PathBuf>,
    #[arg(long, default_value = "/")]
    base: String,
    #[arg(long, default_value = "127.0.0.1:3001")]
    addr: String,
    #[arg(long)]
    check: bool,
    #[arg(long)]
    require_exports: bool,
    #[arg(long)]
    no_site_copy: bool,
}
fn main() -> Result<()> {
    let a = Args::parse();
    let root = &a.root;
    let base = base_path(&a.base)?;
    let output =
        |default: &str| root.join(a.output.as_deref().unwrap_or(std::path::Path::new(default)));
    match a.command.as_str() {
        "site" => site::build(root, &output("dist/site-rust"), &base),
        "check-site" => site::check(&output("dist/site-rust"), &base, a.require_exports),
        "serve" => server::serve(&output("dist/site-rust"), &base, &a.addr),
        "sidebar" => {
            let book = malayalam::content::Book::load(root, &base)?;
            malayalam::util::write(root.join("docs/_sidebar.md"), &book.sidebar, a.check)
        }
        "navigation" => malayalam::reading::navigation(root, a.check),
        "check-reading" => malayalam::reading::validate(root),
        "vocabulary" => malayalam::vocabulary::build(root, a.check),
        "glossary" => malayalam::vocabulary::glossary(root, a.check),
        "anki" => malayalam::anki::build(root, &output("dist/anki"), !a.no_site_copy).map(|_| ()),
        "epub" => malayalam::book::build(root, &output("dist/malayalam.epub"), false, None),
        "pdf" => malayalam::book::build(root, &output("dist/malayalam.pdf"), true, None),
        "check-pdf" => malayalam::book::validate_pdf(root, &output("dist/malayalam.pdf")),
        "check-pdf-layout" => malayalam::book::check_pdf_layout(root),
        "check-lists" => malayalam::book::check_lists(root),
        "audit-prompts" => {
            let data = malayalam::util::read_json(root.join("data/vocabulary/moag.json"))?;
            let study = malayalam::util::read_json(root.join("data/vocabulary/study.json"))?;
            malayalam::anki::validate(&data, &study)
        }
        "writing" => malayalam::writing::build(root, a.check),
        "audio" => malayalam::audio::build(root, "sections", a.check),
        "word-audio" => malayalam::audio::build(root, "words", a.check),
        "letter-audio" => malayalam::audio::build(root, "letters", a.check),
        "archive" => malayalam::resources::archive(
            root,
            a.manifest
                .as_deref()
                .ok_or_else(|| anyhow::anyhow!("--manifest is required"))?,
            a.check,
        ),
        "collect" => malayalam::resources::collect(
            &a.url,
            &output("dist/archive"),
            a.scope.as_deref(),
            a.limit,
        ),
        "import-story" => malayalam::resources::import_story(
            a.input
                .as_deref()
                .ok_or_else(|| anyhow::anyhow!("--input is required"))?,
            &output("dist/story"),
        ),
        "assemble-books" => malayalam::resources::assemble_books(root, a.check),
        "transcribe" => malayalam::recognition::transcribe(
            a.input
                .as_deref()
                .ok_or_else(|| anyhow::anyhow!("--input is required"))?,
            a.model
                .as_deref()
                .ok_or_else(|| anyhow::anyhow!("--model is required"))?,
            &output("dist/recognition.json"),
            &a.engine,
            &a.language,
        ),
        "review-audio" => malayalam::recognition::review(root, &output("dist/audio-review.html")),
        "help" => {
            println!("Use --help for commands and options");
            Ok(())
        }
        _ => {
            bail!("unknown command {}; use --help", a.command)
        }
    }
}
