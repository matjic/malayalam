#!/usr/bin/env python3
"""Build a focused listening page for the two resolved transcript questions."""

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/audio/moag"


def main():
    clips = {
        Path(c["path"]).stem: c
        for c in json.loads(
            (ROOT / "docs/assets/audio/moag/words/manifest.json").read_text()
        )["clips"]
    }
    for item in json.loads((DATA / "vocabulary-word-exclusions.json").read_text()):
        clips.setdefault(item["id"], item)
    cases = [
        dict(
            id="lesson_05_word_005",
            start=28.8,
            end=41.7,
            question="Confirmed: പഠിക്കുന്നു (“is studying”).",
            note="Confirmed by your listening review; now attached to the printed പഠിക്കുന്നു row.",
        ),
        dict(
            id="lesson_20_word_041",
            start=250.8,
            end=267.5,
            question="Confirmed: English announcement “Part Two.”",
            note="Confirmed by your listening review; removed from vocabulary players and retained in the full recording.",
        ),
    ]
    folder = ROOT / "docs/assets/audio/moag/audit-context"
    folder.mkdir(exist_ok=True)
    cards = []
    for case in cases:
        clip = clips[case["id"]]
        dest = folder / f"{case['id']}-context.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-i",
                str(ROOT / clip["source"]),
                "-ss",
                str(case["start"]),
                "-t",
                str(case["end"] - case["start"]),
                "-map_metadata",
                "-1",
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "3",
                str(dest),
            ],
            check=True,
        )
        cards.append(
            f'''<article><h2>Lesson {clip["lesson"]} · clip {case["id"][-3:]}</h2><p class="question">{case["question"]}</p><p>{case["note"]}</p><label>Individual clip</label><audio controls preload="none" aria-label="Individual {case["id"]}" src="{clip["path"][5:]}"></audio><label>Surrounding recording</label><audio controls preload="none" aria-label="Context {case["id"]}" src="{dest.relative_to(ROOT / "docs")}"></audio><p><code>{case["id"]}</code> · <a href="/#/lesson{clip["lesson"]}">Open lesson</a></p></article>'''
        )
    page = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Audio review — resolved</title><link rel="stylesheet" href="assets/fonts.css"><style>*{box-sizing:border-box}body{font:16px system-ui,sans-serif;line-height:1.6;color:#172332;background:#f4f6f8;max-width:780px;margin:auto;padding:24px}h1{font-size:27px}h2{font-size:21px}article{background:white;border:1px solid #d7dfe6;border-radius:12px;padding:24px;margin:24px 0}p{color:#526073}.question{font-family:'Noto Sans Malayalam',system-ui;color:#172332}label{display:block;margin-top:18px;font-weight:600}audio{width:100%;margin-top:8px}a{color:#17619b}code{font-size:13px}</style><h1>Audio review — resolved</h1><p>Both transcription questions are resolved. The clips and surrounding excerpts remain here for reference. Other recorded forms still have placement flags.</p>"""
    page += "\n".join(cards)
    page += """<script>document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(a!==b)b.pause()})));</script></html>"""
    (ROOT / "docs/audio-audit-remaining.html").write_text(page)
    print("Built resolved two-clip review page with original-track context.")


if __name__ == "__main__":
    main()
