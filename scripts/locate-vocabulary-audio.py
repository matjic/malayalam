"""Locate English vocabulary announcements with full Whisper large-v3."""

import argparse, json, re, sys, subprocess
from pathlib import Path
import numpy as np, mlx_whisper

sys.path.insert(0, str(Path(__file__).resolve().parent))

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--model", required=True)
args = parser.parse_args()
config = json.loads((Path(args.model) / "config.json").read_text())
assert (
    config["n_audio_layer"] == 32
    and config["n_text_layer"] == 32
    and config["n_mels"] == 128
)
root = Path(__file__).resolve().parents[1]
out = root / "data/audio/moag/vocabulary-recognition"
out.mkdir(exist_ok=True)
sections = json.loads((root / "docs/assets/audio/moag/sections.json").read_text())[
    "clips"
]
tracks = json.loads((root / "data/audio/moag/section-boundaries.json").read_text())[
    "tracks"
]
for n in range(1, 26):
    path = out / f"lesson_{n:02d}-boundaries.json"
    if path.exists():
        continue
    clip = next(
        (c for c in sections if c["lesson"] == n and c["kind"] == "vocabulary"), None
    )
    start = clip["start"] if clip else 0
    track = next(t for t in tracks if t["lesson"] == n)
    end = (
        clip["end"]
        if clip
        else min(
            [
                c["start_seconds"]
                for c in track["section_candidates"]
                if c["kind"] in {"reading_practice", "conversation", "exercise", "text"}
            ]
            + [660]
        )
    )
    source = root / f"data/audio/moag/lesson_{n:02d}.mp3"
    audio = np.frombuffer(
        subprocess.check_output(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(start),
                "-i",
                str(source),
                "-t",
                str(end - start),
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
    r = mlx_whisper.transcribe(
        audio,
        path_or_hf_repo=args.model,
        language="en",
        condition_on_previous_text=False,
        temperature=0,
    )
    segments = [
        dict(
            start=round(s["start"] + start, 3),
            end=round(s["end"] + start, 3),
            text=s["text"],
        )
        for s in r["segments"]
    ]
    path.write_text(
        json.dumps(
            dict(
                lesson=n,
                model="Whisper large-v3",
                purpose="English announcements only; Malayalam transliterations are not teaching transcriptions.",
                range_start=start,
                range_end=end,
                segments=segments,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(
        n,
        [
            (s["start"], s["text"])
            for s in segments
            if re.search(
                "vocab|practice|exercise|ready|repeat|reading|conversation|lesson",
                s["text"],
                re.I,
            )
        ],
        flush=True,
    )
