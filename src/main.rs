use anyhow::{Result, bail};
use malayalam::{routes::base_path, server, site};
use std::{collections::BTreeMap, env, path::PathBuf};

fn main() -> Result<()> {
    let mut args = env::args().skip(1);
    let command = args.next().unwrap_or_else(|| "help".into());
    if matches!(command.as_str(), "help" | "--help" | "-h") {
        println!(
            "malayalam site|check-site|serve|sidebar [--root PATH] [--output dist/site-rust] [--base /] [--addr 127.0.0.1:3001] [--require-exports] [--check]"
        );
        return Ok(());
    }
    let mut options = BTreeMap::new();
    let mut complete = false;
    let mut check = false;
    while let Some(key) = args.next() {
        if key == "--require-exports" {
            complete = true;
            continue;
        }
        if key == "--check" {
            check = true;
            continue;
        }
        if !matches!(key.as_str(), "--root" | "--output" | "--base" | "--addr") {
            bail!("unknown option: {key}");
        }
        let value = args
            .next()
            .ok_or_else(|| anyhow::anyhow!("{key} needs a value"))?;
        options.insert(key, value);
    }
    let root = options
        .get("--root")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(env!("CARGO_MANIFEST_DIR")));
    let output = root.join(
        options
            .get("--output")
            .map(String::as_str)
            .unwrap_or("dist/site-rust"),
    );
    let base = base_path(options.get("--base").map(String::as_str).unwrap_or("/"))?;
    match command.as_str() {
        "sidebar" => {
            let book = malayalam::content::Book::load(&root, &base)?;
            let path = root.join("docs/_sidebar.md");
            if check {
                if std::fs::read_to_string(path)? != book.sidebar {
                    bail!("sidebar is stale; run cargo run -- sidebar");
                }
                println!("Sidebar is up to date.");
            } else {
                std::fs::write(path, book.sidebar)?;
                println!("Updated docs/_sidebar.md");
            }
            Ok(())
        }
        "site" => site::build(&root, &output, &base),
        "check-site" => site::check(&output, &base, complete),
        "serve" => server::serve(
            &output,
            &base,
            options
                .get("--addr")
                .map(String::as_str)
                .unwrap_or("127.0.0.1:3001"),
        ),
        _ => bail!("unknown command: {command}; use --help"),
    }
}
