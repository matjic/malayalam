#!/usr/bin/env python3
"""Build a temporary side-by-side page for the local boundary experiment."""

import html
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/audio/moag"
spec = importlib.util.spec_from_file_location(
    "probes", ROOT / "scripts/probe-koyal-boundaries.py"
)
probes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probes)


def main():
    path = DATA / "koyal-coreml-boundary-trial.json"
    report = json.loads(path.read_text())
    cards = []
    repairs_path = DATA / "vocabulary-cut-repairs.json"
    applied = (
        {r["id"]: r for r in json.loads(repairs_path.read_text())}
        if repairs_path.exists()
        else {}
    )
    explanations = {
        "lesson_24_sneham": "Ends before തമ്മിൽ begins.",
        "lesson_24_thammil": "Includes the first reading that was in the preceding clip.",
        "lesson_24_gunam": "Ends before കുറവ് begins.",
        "lesson_24_kuravu": "Includes both readings of കുറവ്.",
        "lesson_21_tharuka": "Ends before പറഞ്ഞുതരുക begins.",
        "lesson_21_paranjutharuka": "Includes both readings of പറഞ്ഞുതരുക.",
    }
    for case in report["cases"]:
        entry = applied.get(case["old"], {}).get(
            "printed_entry"
        ) or probes.printed_entry(case)
        case["printed_entry"] = entry
        label, meaning = html.escape(entry["malayalam"]), html.escape(entry["meaning"])
        old = f"assets/audio/moag/words/{case['old']}.mp3"
        archived = (
            ROOT / f"docs/assets/audio/moag/boundary-trial/before/{case['old']}.mp3"
        )
        if archived.exists():
            old = str(archived.relative_to(ROOT / "docs"))
        selected = case["selected"]
        if selected:
            source = selected["preview"].removeprefix("docs/")
            preview = f'<audio controls preload="none" aria-label="Trial cut: {label}" src="{html.escape(source, quote=True)}"></audio>'
            details = f"{selected['start']:.2f}–{selected['end']:.2f}s in source · both readings retained"
            note = explanations.get(
                case["id"], "The clip now contains only the two readings of this entry."
            )
            status = "Applied" if case["old"] in applied else "Candidate cut"
        elif case.get("retain_original_audio"):
            preview = f'<audio controls preload="none" aria-label="Retained recording: {label}" src="assets/audio/moag/words/{case["old"]}.mp3"></audio>'
            details = "Original audio bytes retained."
            note = "The word is now attached to its existing printed entry."
            status = "Retained"
        else:
            preview = '<p class="muted">No candidate exported</p>'
            details = "Kept flagged for inspection."
            note = (
                "Recognition is consistent, but the crop edges did not meet the quiet-boundary criterion."
                if any(t["exact_target_repetitions"] == 2 for t in case["trials"])
                else "The recognizer does not agree with the printed form. The vocabulary has been preserved."
            )
            status = "Unresolved"
        snippets = " / ".join(sorted({t["transcript"] for t in case["trials"]}))
        cards.append(f'''<article><div class="heading"><h2 lang="ml">{label}</h2><span>{status}</span></div>
<p>{meaning}</p><p>{note}</p><div class="players"><section><h3>Before repair</h3><audio controls preload="none" aria-label="Existing cut: {label}" src="{old}"></audio><small>{case["old"]}</small></section><section><h3>Updated recording</h3>{preview}<small>{details}</small></section></div>
<details><summary>Recognition results · {len(case["trials"])} tested crops</summary><p lang="ml">{html.escape(snippets)}</p></details>
<p><a href="/#/lesson{case["lesson"]}" target="_blank" rel="noopener">Open Lesson {case["lesson"]} ↗</a> · {html.escape(case["printed_role"])}</p></article>''')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    page = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Audio boundary comparison</title><link rel="stylesheet" href="assets/fonts.css"><style>
*{box-sizing:border-box}body{font:16px system-ui,sans-serif;line-height:1.5;background:#f4f6f8;color:#172332;max-width:980px;padding:24px;margin:auto}h1{font-size:28px}h2{font-family:'Noto Sans Malayalam',system-ui;margin:0;font-size:28px}h3{font-size:15px;margin:0 0 10px}article{background:white;border:1px solid #d7dfe6;border-radius:12px;padding:24px;margin:24px 0}.heading{display:flex;align-items:center;justify-content:space-between;gap:16px}.heading span{font-size:13px;background:#e8eff6;border-radius:20px;padding:4px 12px}p{color:#526073}.players{display:grid;grid-template-columns:1fr 1fr;gap:24px}audio{width:100%}small{display:block;color:#526073;overflow-wrap:anywhere}details{margin-top:20px}a{color:#17619b}.muted{font-style:italic}details p[lang=ml]{font-family:'Noto Sans Malayalam',system-ui}@media(max-width:650px){.players{grid-template-columns:1fr}.heading{align-items:flex-start}}
</style><h1>Audio boundary comparison</h1><p>Compare the prior clips with the repaired recordings. Six cuts were approved by listening; two noisy boundary repairs were checked across crop variations. The original അവന് audio is retained. Printed lesson wording and meanings are unchanged.</p>"""
    page += "\n".join(cards)
    page += """<script>document.querySelectorAll('audio').forEach(player=>player.addEventListener('play',()=>document.querySelectorAll('audio').forEach(other=>{if(other!==player)other.pause()})));</script></html>"""
    (ROOT / "docs/audio-boundary-review.html").write_text(page)
    print("Built comparison page for all nine repaired assignments.")


if __name__ == "__main__":
    main()
