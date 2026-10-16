"""Recheck uncertain word clips with full Whisper large-v3, retaining evidence."""

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import numpy as np
import mlx_whisper

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "vocab_alignment", ROOT / "scripts/align-vocabulary-audio.py"
)
alignment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alignment)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--lessons", type=int, nargs="+", default=list(range(1, 26)))
    args = parser.parse_args()
    config = json.loads((Path(args.model) / "config.json").read_text())
    assert config["n_text_layer"] == 32
    out = ROOT / "data/audio/moag/vocabulary-rechecks"
    out.mkdir(exist_ok=True)
    for number in args.lessons:
        source = ROOT / f"data/audio/moag/vocabulary-alignment/lesson_{number:02d}.json"
        if not source.exists():
            continue
        record = json.loads(source.read_text())
        dest = out / f"lesson_{number:02d}.json"
        previous = json.loads(dest.read_text()) if dest.exists() else {}
        candidates = alignment.candidates(record["textbook_vocabulary"])
        for word in record["words"]:
            if word["status"] != "review" and len(word["utterances"]) == 2:
                continue
            start = word["utterances"][0]["start"]
            end = word["utterances"][-1]["end"]
            if (
                word["id"] in previous
                and previous[word["id"]]["start"] == start
                and previous[word["id"]]["end"] == end
            ):
                continue
            audio = np.frombuffer(
                subprocess.check_output(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-ss",
                        str(start),
                        "-i",
                        str(ROOT / record["source"]),
                        "-t",
                        str(end - start),
                        "-ar",
                        "16000",
                        "-ac",
                        "1",
                        "-f",
                        "f32le",
                        "-",
                    ]
                ),
                np.float32,
            )
            result = mlx_whisper.transcribe(
                audio,
                path_or_hf_repo=args.model,
                language="ml",
                task="transcribe",
                initial_prompt=" ".join(c["text"] for c in candidates),
                temperature=0,
                condition_on_previous_text=False,
                sample_len=64,
            )
            previous[word["id"]] = dict(
                start=start,
                end=end,
                text=result["text"].strip(),
                segments=result["segments"],
                model="Whisper large-v3",
            )
            dest.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n")
            print(
                number, word["id"], word["transcript"], "=>", result["text"], flush=True
            )


if __name__ == "__main__":
    main()
