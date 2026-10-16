"""Transcribe vocabulary with local Whisper large-v3 (optional MLX dependency).

Run with an MLX Python environment. Results retain all pause ranges and raw ASR
word timestamps so the review/build step never has to invent a transcription.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path
import numpy as np
import mlx_whisper
from audio_segments import speech_spans

ROOT = Path(__file__).resolve().parents[1]


def vocabulary(number):
    text = (ROOT / f"docs/lesson{number}.md").read_text()
    match = re.search(r"^(#{2,3}) Vocabulary\n", text, re.M)
    if not match:
        return []
    stop = re.search(r"^#{1," + str(len(match[1])) + r"} ", text[match.end() :], re.M)
    body = (
        text[match.end() : match.end() + stop.start()] if stop else text[match.end() :]
    )
    rows = []
    for line in body.splitlines():
        if line.startswith("| "):
            cells = line.split("|")[1:-1]
            if len(cells) < 2:
                continue
            word = re.sub(r"<!--.*?-->", "", cells[0]).strip()
            if not re.search("[\u0d00-\u0d7f]", word):
                continue
            rows.append(dict(malayalam=word, meaning=cells[1].strip()))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--lessons", nargs="+", type=int, default=list(range(1, 26)))
    args = parser.parse_args()
    # Refuse the turbo/small checkpoints, including silent accidental substitutions.
    config = json.loads((Path(args.model) / "config.json").read_text())
    assert (
        config["n_audio_layer"] == 32
        and config["n_text_layer"] == 32
        and config["n_mels"] == 128
    ), "Use full Whisper large-v3"
    out = ROOT / "data/audio/moag/vocabulary-recognition"
    out.mkdir(exist_ok=True)
    for number in args.lessons:
        dest = out / f"lesson_{number:02d}.json"
        previous = json.loads(dest.read_text()) if dest.exists() else {}
        if previous.get("pipeline_version") != 2:
            previous = {}
        if previous.get("complete"):
            print(f"Lesson {number}: cached", flush=True)
            continue
        source = ROOT / f"data/audio/moag/lesson_{number:02d}.mp3"
        announcements = json.loads(
            (out / f"lesson_{number:02d}-boundaries.json").read_text()
        )
        lines = announcements["segments"]
        header = next(
            (s for s in lines if re.search(r"vocabulary", s["text"], re.I)), None
        )
        assert header, f"Lesson {number}: vocabulary announcement needs review"
        intro = [
            s
            for s in lines
            if header["start"] <= s["start"] < header["start"] + 16
            and re.search(r"vocabulary|repeat|each item|ready|listen", s["text"], re.I)
        ]
        start = max(s["end"] for s in intro)
        following = [
            s["start"]
            for s in lines
            if s["start"] > start + 15
            and re.search(
                r"exercise|reading practice|repetition practice|conversation|form locative phrases",
                s["text"],
                re.I,
            )
        ]
        end = min(following + [announcements["range_end"]])
        # Prefer the least aggressive threshold that separates tape hiss from speech.
        options = []
        for db in [-34, -31, -28, -25, -22]:
            spans = [
                (s, e)
                for s, e in speech_spans(source, noise=db, pause=0.5)
                if s >= start - 0.05 and e <= end + 0.05
            ]
            score = sum(min(e - s, 3) for s, e in spans if e - s > 3)
            options.append((score, db, spans))
        maximum = max(len(x[2]) for x in options)
        options = [x for x in options if len(x[2]) >= maximum * 0.8]
        best = min(x[0] for x in options)
        _, db, spans = next(x for x in options if x[0] <= best + 3)
        assert spans, f"Lesson {number}: no speech spans found in vocabulary"
        audio = np.frombuffer(
            subprocess.check_output(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(source),
                    "-f",
                    "f32le",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-",
                ]
            ),
            np.float32,
        )
        rows = vocabulary(number)
        prompt = " ".join(re.sub(r"<br>.*|\s*\(.*", "", r["malayalam"]) for r in rows)
        groups = []
        group = []
        length = 0
        for s, e in spans:
            if group and (len(group) >= 12 or length + e - s + 0.6 > 22):
                groups.append(group)
                group = []
                length = 0
            group.append((s, e))
            length += e - s + 0.6
        if group:
            groups.append(group)
        records = previous.get("groups", [])
        for index, group in enumerate(groups):
            if index < len(records):
                continue
            parts = []
            mapping = []
            pos = 0
            for s, e in group:
                s = max(0, s - 0.14)
                e = min(len(audio) / 16000, e + 0.18)
                part = audio[round(s * 16000) : round(e * 16000)]
                mapping.append(
                    dict(
                        compact_start=pos,
                        compact_end=pos + len(part) / 16000,
                        start=round(s, 4),
                        end=round(e, 4),
                    )
                )
                parts.extend([part, np.zeros(6400, np.float32)])
                pos += len(part) / 16000 + 0.4
            result = mlx_whisper.transcribe(
                np.concatenate(parts),
                path_or_hf_repo=args.model,
                language="ml",
                task="transcribe",
                initial_prompt=prompt,
                word_timestamps=True,
                condition_on_previous_text=False,
                temperature=0,
                max_initial_timestamp=2,
                sample_len=128,
            )
            records.append(
                dict(
                    utterances=mapping, text=result["text"], segments=result["segments"]
                )
            )
            print(
                f"Lesson {number} {index + 1}/{len(groups)}: {result['text']}",
                flush=True,
            )
            result = dict(
                pipeline_version=2,
                lesson=number,
                source=str(source.relative_to(ROOT)),
                model="Whisper large-v3 (32 encoder and 32 decoder layers), MLX",
                language="ml",
                range_start=start,
                range_end=end,
                pause_threshold_db=db,
                pause_seconds=0.5,
                textbook_vocabulary=rows,
                groups=records,
                complete=len(records) == len(groups),
            )
            dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
