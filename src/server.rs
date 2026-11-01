//! Local preview only. Production is static files on GitHub Pages.
use anyhow::{Context, Result};
use std::{
    fs,
    io::{Read, Seek, SeekFrom},
    path::Path,
};
use tiny_http::{Header, Method, Response, Server, StatusCode};

fn mime(path: &Path) -> &'static str {
    match path.extension().and_then(|s| s.to_str()).unwrap_or("") {
        "html" => "text/html; charset=utf-8",
        "css" => "text/css; charset=utf-8",
        "js" => "application/javascript; charset=utf-8",
        "json" => "application/json; charset=utf-8",
        "svg" => "image/svg+xml",
        "woff2" => "font/woff2",
        "woff" => "font/woff",
        "ttf" => "font/ttf",
        "png" => "image/png",
        "jpg" | "jpeg" => "image/jpeg",
        "mp3" => "audio/mpeg",
        "ogg" => "audio/ogg",
        "wav" => "audio/wav",
        "mp4" => "video/mp4",
        "pdf" => "application/pdf",
        "epub" => "application/epub+zip",
        _ => "application/octet-stream",
    }
}

fn range(header: &str, length: u64) -> Option<(u64, u64)> {
    let (start, end) = header.strip_prefix("bytes=")?.split_once('-')?;
    if length == 0 {
        return None;
    }
    let (start, end) = if start.is_empty() {
        let suffix = end.parse::<u64>().ok()?;
        if suffix == 0 {
            return None;
        }
        (length.saturating_sub(suffix), length - 1)
    } else {
        (
            start.parse().ok()?,
            if end.is_empty() {
                length - 1
            } else {
                end.parse::<u64>().ok()?.min(length - 1)
            },
        )
    };
    (start <= end && start < length).then_some((start, end))
}

pub fn serve(output: &Path, base: &str, addr: &str) -> Result<()> {
    let root = output
        .canonicalize()
        .context("build the site before serving")?;
    let server = Server::http(addr).map_err(|e| anyhow::anyhow!(e.to_string()))?;
    println!("Preview: http://{addr}{base}");
    for request in server.incoming_requests() {
        if !matches!(request.method(), Method::Get | Method::Head) {
            let _ = request.respond(Response::empty(StatusCode(405)));
            continue;
        }
        let parsed = url::Url::parse("http://preview.invalid/")?.join(request.url())?;
        let path = percent_encoding::percent_decode_str(parsed.path()).decode_utf8_lossy();
        let Some(relative) = path.strip_prefix(base) else {
            let _ = request.respond(Response::empty(StatusCode(404)));
            continue;
        };
        let mut target = root.join(relative);
        if target.is_dir() {
            target = target.join("index.html");
        }
        let target = target
            .canonicalize()
            .ok()
            .filter(|p| p.starts_with(&root) && p.is_file());
        let Some(target) = target else {
            let body = fs::read(root.join("404.html")).unwrap_or_else(|_| b"Not found".to_vec());
            let _ = request.respond(Response::from_data(body).with_status_code(404).with_header(
                Header::from_bytes("Content-Type", "text/html; charset=utf-8").unwrap(),
            ));
            continue;
        };
        let mut file = fs::File::open(&target)?;
        let length = file.metadata()?.len();
        let mut headers = vec![
            Header::from_bytes("Content-Type", mime(&target)).unwrap(),
            Header::from_bytes("Accept-Ranges", "bytes").unwrap(),
        ];
        let requested = request.headers().iter().find(|h| h.field.equiv("Range"));
        let (start, size, status) = if let Some(header) = requested {
            if let Some((start, end)) = range(header.value.as_str(), length) {
                headers.push(
                    Header::from_bytes("Content-Range", format!("bytes {start}-{end}/{length}"))
                        .unwrap(),
                );
                (start, end - start + 1, StatusCode(206))
            } else {
                let _ = request.respond(Response::empty(StatusCode(416)).with_header(
                    Header::from_bytes("Content-Range", format!("bytes */{length}")).unwrap(),
                ));
                continue;
            }
        } else {
            (0, length, StatusCode(200))
        };
        file.seek(SeekFrom::Start(start))?;
        let response = Response::new(status, headers, file.take(size), Some(size as usize), None);
        if let Err(error) = request.respond(response) {
            eprintln!("preview connection: {error}");
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn audio_ranges_are_bounded() {
        assert_eq!(range("bytes=10-19", 100), Some((10, 19)));
        assert_eq!(range("bytes=90-", 100), Some((90, 99)));
        assert_eq!(range("bytes=-10", 100), Some((90, 99)));
        assert_eq!(range("bytes=0-999", 100), Some((0, 99)));
        assert_eq!(range("bytes=100-", 100), None);
        assert_eq!(range("bytes=0-1,5-6", 100), None);
    }
}
