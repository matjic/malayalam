#!/usr/bin/env python3
"""Build the temporary review page for recorded forms without exact table placement."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/audio/moag'
manifest = json.loads((ROOT / 'docs/assets/audio/moag/words/manifest.json').read_text())
clips = []
for c in manifest['clips']:
    if c.get('label_review', {}).get('placement') != 'unplaced_recorded_form':
        continue
    lesson_clips = [x for x in manifest['clips'] if x['lesson'] == c['lesson']]
    i = lesson_clips.index(c)
    neighbors = lesson_clips[max(0, i-1):i+2]
    record = json.loads((DATA / f"vocabulary-alignment/lesson_{c['lesson']:02}.json").read_text())
    rows = record['textbook_vocabulary']
    context = '\n'.join(f"{r['malayalam']} — {r['meaning']}" for r in rows)
    clips.append(dict(id=Path(c['path']).stem, lesson=c['lesson'], transcript=c['transcript'], status='review', meaning='', start_seconds=c['start'], end_seconds=c['end'], clip=c['path'][5:], neighbors=[dict(label=x['transcript'], clip=x['path'][5:]) for x in neighbors], printed_context=context, sha256=c['sha256']))
page = (ROOT / 'docs/audio-review.html').read_text()
page = re.sub(r'const clips=.*?;\n', lambda _: 'const clips='+json.dumps(clips, ensure_ascii=False)+';\n', page, count=1)
page = page.replace('malayalam-vocab-review-v1', 'malayalam-placement-review-v1').replace('vocabulary-reviews.json', 'vocabulary-placement-reviews.json')
page = page.replace('Review the 142 uncertain clips one at a time. Confirm the proposed word, type a correction, or flag a bad cut. Progress saves in this browser. Download your reviews when finished so they can be applied to the tables.', 'Review the 49 recorded forms one at a time. Confirm what you hear and suggest placement in the notes. The printed vocabulary and neighboring clips are below. Confirming the audio does not approve a table placement. Progress saves separately in this browser; download your reviews when finished.')
page = page.replace('Temporary vocabulary audio review', 'Temporary audio placement review').replace('<h1>Vocabulary audio review</h1>', '<h1>Audio placement review</h1>')
page = page.replace('<label for="correction">', '<details><summary>Neighboring recordings</summary><div id="neighbors"></div></details><details><summary>Original printed vocabulary</summary><pre id="printed" style="white-space:pre-wrap;font:16px Noto Sans Malayalam,system-ui;line-height:1.9"></pre></details><label for="correction">', 1)
page = page.replace('Notes / cut issues', 'Placement suggestion / notes / cut issues').replace('For example: cut off at the start, or includes the next word', 'For example: belongs beside a longer phrase, alternate form, or cut needs fixing')
page = page.replace('Needs match confirmation', 'Needs table placement').replace('Confirming means the word and clip boundaries are both correct.', 'Confirming means the word and boundaries sound correct; use notes for placement suggestions.')
page = page.replace("audio.pause();audio.src=c.clip;", "document.querySelectorAll('audio').forEach(a=>a.pause());audio.src=c.clip;$('printed').textContent=c.printed_context;$('neighbors').replaceChildren();c.neighbors.forEach(n=>{const p=document.createElement('p');p.textContent=n.label;const a=document.createElement('audio');a.controls=true;a.preload='none';a.src=n.clip;p.append(a);$('neighbors').append(p)});")
page = page.replace("audio.onerror=", "document.addEventListener('play',e=>{if(e.target.tagName==='AUDIO')document.querySelectorAll('audio').forEach(a=>{if(a!==e.target)a.pause()})},true);\naudio.onerror=")
(ROOT / 'docs/audio-placement-review.html').write_text(page)
print(f'Built placement review page: {len(clips)} clips.')
