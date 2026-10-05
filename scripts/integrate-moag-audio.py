"""Build bounded Moag section clips and embed their players in the lessons."""

import argparse
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r'\n<!-- moag-audio -->\n.*?<!-- /moag-audio -->\n', re.S)
CLIPS = []


def clock(seconds):
    return f'{int(seconds) // 60:02d}:{int(seconds) % 60:02d}'


def render(number, kind, label, cues, end, note, boundaries=()):
    clips = []
    for index, (title, start) in enumerate(cues):
        # Every option stops at the next distinct announcement within the section.
        stop = min([point for _, point in cues if point > start]
                   + [point for point in boundaries if point > start + 15] + [end])
        source = f'assets/audio/moag/sections/lesson_{number:02d}_{kind}_{index}.mp3'
        clip = dict(lesson=number, kind=kind, label=title, start=start, end=stop,
                    path='docs/' + source)
        assert 0 <= start < stop, clip
        clips.append(clip)
        CLIPS.append(clip)
    options = ''.join(
        f'<button type="button" data-audio-src="{clip["path"][5:]}" '
        f'aria-pressed="{str(index == 0).lower()}">{html.escape(clip["label"])} · '
        f'{clock(clip["end"] - clip["start"])}</button>'
        for index, clip in enumerate(clips)
    )
    return (
        '\n<!-- moag-audio -->\n'
        '<div class="lesson-audio">\n'
        f'<p><strong>{html.escape(label)}</strong></p>\n'
        f'<audio controls preload="none" aria-label="Lesson {number}: {html.escape(label)}" '
        f'src="{clips[0]["path"][5:]}"></audio>\n'
        f'<div class="lesson-audio-cues">{options}</div>\n'
        f'<p class="lesson-audio-note">{html.escape(note)}</p>\n'
        '</div>\n<!-- /moag-audio -->\n'
    )


def sections(track):
    candidates = track['section_candidates']
    result = []
    mapping = [('Vocabulary', 'vocabulary'), ('Reading Practice', 'reading_practice'),
               ('Conversation', 'conversation'), ('Text', 'text'),
               ('Sample Newspaper Advertisements', 'text'), ('Exercises', 'exercise')]
    chapter = ROOT / f'docs/lesson{track["lesson"]}.md'
    text = BLOCK.sub('', chapter.read_text())
    for heading, kind in mapping:
        match = re.search(r'^#{2,3} ' + re.escape(heading) + r'\n', text, re.M)
        if not match:
            continue
        found = [cue for cue in candidates if cue['kind'] == kind]
        if kind == 'conversation':
            found += [cue for cue in candidates if cue['kind'] == 'slower_reading'
                      and re.search(r'conversation|dialogue', cue['recognition_excerpt'], re.I)]
            found += [cue for cue in candidates if cue['kind'] == 'normal_speed'
                      and re.search(r'conversation|dialogue', cue['recognition_excerpt'], re.I)]
        if not found:
            continue
        first = min(found, key=lambda cue: cue['start_seconds'])
        def point(cue):
            return max(0, round(cue['start_seconds'], 2))
        cues = [('Listen', point(first))]
        # A section stops before the next different kind of major announcement.
        # Repeated headings for the same activity stay within the section.
        following = [point(cue) for cue in candidates
                     if cue['kind'] in {'vocabulary', 'reading_practice', 'conversation', 'text', 'exercise'}
                     and cue['kind'] != kind and point(cue) > point(first)]
        end = min(following + [round(track['duration_seconds'], 2)])
        if kind == 'conversation':
            slow = [cue for cue in candidates if cue['kind'] == 'slower_reading'
                    and cue['start_seconds'] >= first['start_seconds']
                    and re.search(r'conversation|dialogue', cue['recognition_excerpt'], re.I)]
            normal = [cue for cue in candidates if cue['kind'] == 'normal_speed'
                      and cue['start_seconds'] >= first['start_seconds']]
            roles = [cue for cue in candidates if cue['kind'] == 'role_play'
                     and cue['start_seconds'] >= first['start_seconds']]
            repeat = [cue for cue in candidates if cue['kind'] == 'repetition_practice'
                      and cue['start_seconds'] >= first['start_seconds']]
            for label, available in [('Slower conversation', slow), ('Normal-speed conversation', normal),
                                     ('Repeat with the speaker', repeat), ('Role practice', roles)]:
                available = [cue for cue in available if point(cue) < end]
                for index, cue in enumerate(available):
                    start = point(cue)
                    if start < end:
                        title = f'{label} {index + 1}' if len(available) > 1 else label
                        cues.append((title, start))
        # If the listening announcement is also the section start, use one option
        # rather than presenting identical clips under two labels.
        if len(cues) > 1:
            alternate = next((cue for cue in cues[1:] if abs(cue[1] - cues[0][1]) < 15), None)
            if alternate:
                cues = [alternate] + [cue for cue in cues[1:] if cue != alternate]
            else:
                # A heading without a recovered activity description is retained
                # as a general listening option rather than labeled repetition.
                cues[0] = ('Listen', cues[0][1])
        note = 'Approximate section boundaries; recorded wording may differ.'
        if kind == 'exercise':
            note = 'Recorded exercise numbers and order may differ. Some answers require teacher review. Section boundaries are approximate.'
        boundaries = [point(cue) for cue in candidates if cue['kind'] == 'conversation'] if kind == 'conversation' else []
        cues.sort(key=lambda cue: cue[1])
        result.append((match.end(), render(track['lesson'], kind, f'{heading} audio', cues, end, note, boundaries)))
    return text, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    audit = json.loads((ROOT / 'data/audio/moag/audit.json').read_text())
    refined = json.loads((ROOT / 'data/audio/moag/section-boundaries.json').read_text())
    fine_tracks = {track['lesson']: track for track in refined['tracks']}
    problems = []
    players = 0
    for track in audit['tracks']:
        track = {**track, 'section_candidates': fine_tracks[track['lesson']]['section_candidates']}
        number = track['lesson']
        path = ROOT / f'docs/lesson{number}.md'
        original = path.read_text()
        text, insertions = sections(track)
        for position, block in sorted(insertions, reverse=True):
            text = text[:position] + block + text[position:]
        # Replacing generated blocks must never change the underlying lesson text.
        assert BLOCK.sub('', text) == BLOCK.sub('', original), path
        players += len(insertions)
        if text != original:
            if args.check:
                problems.append(f'{path.relative_to(ROOT)} needs audio integration')
            else:
                path.write_text(text)
        source = ROOT / track['path']
        if hashlib.sha256(source.read_bytes()).hexdigest() != track['sha256']:
            problems.append(f'{source.relative_to(ROOT)} does not match the original recording')
    manifest_path = ROOT / 'docs/assets/audio/moag/sections.json'
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    old = {clip['path']: clip for clip in previous.get('clips', [])}
    for clip in CLIPS:
        destination = ROOT / clip['path']
        prior = old.get(clip['path'], {})
        unchanged = all(prior.get(key) == clip[key] for key in ('start', 'end', 'lesson'))
        if not args.check and (not unchanged or not destination.exists()):
            destination.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                            '-ss', str(clip['start']), '-i', str(ROOT / f'data/audio/moag/lesson_{clip["lesson"]:02d}.mp3'),
                            '-t', str(clip['end'] - clip['start']), '-map_metadata', '-1',
                            '-c:a', 'copy', str(destination)], check=True)
        if not destination.exists():
            problems.append(f'Missing section clip: {clip["path"]}')
            continue
        clip['sha256'] = hashlib.sha256(destination.read_bytes()).hexdigest()
        if args.check and (not unchanged or clip['sha256'] != prior.get('sha256')):
            problems.append(f'Section clip changed: {clip["path"]}')
    if not args.check:
        manifest_path.write_text(json.dumps(dict(method='Section announcements rechecked with Whisper large-v3-turbo word timestamps and independent Whisper small comparisons, with preceding pauses used where available. MP3 frames copied without re-encoding; sentence-level Malayalam alignment remains unverified.', clips=CLIPS), indent=2) + '\n')
        active_paths = {clip['path'] for clip in CLIPS}
        for path, prior in old.items():
            if path not in active_paths:
                stale = ROOT / path
                if stale.exists() and hashlib.sha256(stale.read_bytes()).hexdigest() == prior.get('sha256'):
                    stale.unlink()
        # The original tracks live in data/. Remove only unchanged copies created
        # by the earlier full-track integration, now replaced by section clips.
        for track in audit['tracks']:
            copied = ROOT / f'docs/assets/audio/moag/lesson_{track["lesson"]:02d}.mp3'
            if copied.exists() and hashlib.sha256(copied.read_bytes()).hexdigest() == track['sha256']:
                copied.unlink()
    for problem in problems:
        print(problem)
    if problems:
        raise SystemExit(1)
    print(f'Checked 25 original recordings and {players} lesson/section players.' if args.check
          else f'Integrated 25 recordings with {players} lesson/section players.')


if __name__ == '__main__':
    main()
