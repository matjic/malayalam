"""Try Koyal on a small sample of existing vocabulary clips, preserving raw output."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    samples = []
    with tempfile.TemporaryDirectory(prefix="koyal-clips-") as temp:
        for lesson in (1, 5, 10, 15, 20, 25):
            record = json.loads((root / f"data/audio/moag/vocabulary-alignment/lesson_{lesson:02d}.json").read_text())
            # Include the first two entries and one entry flagged for review, when present.
            words = record["words"][:2]
            extra = next((w for w in record["words"][2:] if w["status"] == "review"), record["words"][-1])
            for word in [*words, extra]:
                start = max(0, word["utterances"][0]["start"] - 0.15)
                end = word["utterances"][-1]["end"] + 0.15
                wav = Path(temp) / f'{word["id"]}.wav'
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", str(root / record["source"]), "-t", str(end-start), "-ar", "16000", "-ac", "1", str(wav)], check=True)
                samples.append(dict(id=word["id"], source=record["source"], start=start, end=end, expected=word["transcript"], whisper_raw=word["raw_texts"], alignment_status=word["status"], wav=str(wav)))
        import torch
        import nemo.collections.asr as asr

        torch.set_num_threads(4)
        model = asr.models.ASRModel.restore_from(args.model, map_location="cpu")
        model.eval()
        started = time.monotonic()
        with torch.inference_mode():
            results = model.transcribe([s["wav"] for s in samples], batch_size=1)
        elapsed = time.monotonic() - started
        for sample, result in zip(samples, results, strict=True):
            sample.pop("wav")
            sample["koyal"] = result if isinstance(result, str) else result.text
            print(sample["id"], sample["expected"], "=>", sample["koyal"], flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(dict(model="adalat-ai/koyal-ml-120m-1.0", device="cpu", decoding="default greedy", inference_seconds=elapsed, audio_seconds=sum(s["end"]-s["start"] for s in samples), samples=samples), ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
