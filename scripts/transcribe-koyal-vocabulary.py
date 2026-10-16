#!/usr/bin/env python3
"""Run independent Koyal recognition on published clips and contextual excerpts.

Preserves raw transcripts and content hashes; never updates teaching labels or cuts.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/audio/moag"
MODEL_ID = "adalat-ai/koyal-ml-120m-1.0"


def sha256(path):
    with path.open("rb") as handle:
        return (
            hashlib.file_digest(handle, "sha256").hexdigest()
            if hasattr(hashlib, "file_digest")
            else hashlib.sha256(handle.read()).hexdigest()
        )


def save(path, record):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def build_samples():
    with (DATA / "vocabulary-transcripts.csv").open() as handle:
        rows = [r for r in csv.DictReader(handle) if r["clip"]]
    assert len(rows) == 1005
    clips, contexts = [], []
    findings = json.loads((DATA / "vocabulary-context-findings.json").read_text())
    for lesson in range(1, 26):
        local = [r for r in rows if int(r["lesson"]) == lesson]
        source = DATA / f"lesson_{lesson:02}.mp3"
        source_hash = sha256(source)
        for i, row in enumerate(local):
            path = ROOT / row["clip"]
            clip_id = path.stem
            sample = dict(
                id=clip_id,
                lesson=lesson,
                source=row["clip"],
                source_sha256=sha256(path),
                start=0,
                end=None,
                original_track=f"data/audio/moag/lesson_{lesson:02}.mp3",
                original_start=float(row["start_seconds"]),
                original_end=float(row["end_seconds"]),
                published_transcript=row["transcript"],
                published_status=row["status"],
            )
            clips.append(sample)
            if clip_id in findings:
                before, after = local[max(i - 1, 0)], local[min(i + 1, len(local) - 1)]
                contexts.append(
                    dict(
                        id=clip_id,
                        lesson=lesson,
                        source=str(source.relative_to(ROOT)),
                        source_sha256=source_hash,
                        start=max(0, float(before["start_seconds"]) - 0.4),
                        end=float(after["end_seconds"]) + 0.4,
                        target_start=float(row["start_seconds"]),
                        target_end=float(row["end_seconds"]),
                        previous_id=Path(before["clip"]).stem if i else None,
                        next_id=Path(after["clip"]).stem
                        if i + 1 < len(local)
                        else None,
                        published_transcript=row["transcript"],
                        context_finding=findings[clip_id],
                    )
                )
    assert {s["id"] for s in contexts} == set(findings)
    return clips, contexts


def run_set(model, samples, path, model_hash, batch_size):
    base = dict(
        model=MODEL_ID,
        model_sha256=model_hash,
        input_format="16000 Hz mono PCM WAV",
        decoding="default greedy",
        device="cpu",
        inputs="Published MP3 clips"
        if samples[0].get("original_track")
        else "Original track excerpts including previous and next clip; no labels supplied to recognizer",
        inference_seconds=0,
        samples=[],
        complete=False,
    )
    old = json.loads(path.read_text()) if path.exists() else base
    assert old["model_sha256"] == model_hash, "Model differs from cached results"
    results = {r["id"]: r for r in old["samples"]}
    pending = []
    for s in samples:
        cached = results.get(s["id"])
        if cached and all(
            cached.get(k) == s.get(k) for k in ("source_sha256", "start", "end")
        ):
            continue
        pending.append(s)
    print(
        f"{path.name}: {len(samples) - len(pending)} cached; {len(pending)} pending",
        flush=True,
    )
    with tempfile.TemporaryDirectory(prefix="koyal-vocabulary-") as temp:
        for offset in range(0, len(pending), batch_size):
            batch = pending[offset : offset + batch_size]

            def convert(s):
                wav = Path(temp) / f"{s['id']}.wav"
                command = ["ffmpeg", "-v", "error", "-y"]
                if s["start"]:
                    command += ["-ss", str(s["start"])]
                command += ["-i", str(ROOT / s["source"])]
                if s["end"] is not None:
                    command += ["-t", str(s["end"] - s["start"])]
                command += ["-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)]
                subprocess.run(command, check=True, capture_output=True)
                return wav

            with ThreadPoolExecutor(max_workers=4) as pool:
                wavs = list(pool.map(convert, batch))
            started = time.monotonic()
            outputs = model.transcribe(
                [str(p) for p in wavs], batch_size=1, verbose=False
            )
            old["inference_seconds"] += time.monotonic() - started
            for sample, result in zip(batch, outputs, strict=True):
                text = result if isinstance(result, str) else result.text
                assert isinstance(text, str)
                results[sample["id"]] = {**sample, "koyal": text}
            old["samples"] = [results[s["id"]] for s in samples if s["id"] in results]
            old["complete"] = len(old["samples"]) == len(samples)
            save(path, old)
            for wav in wavs:
                wav.unlink()
            print(
                f"{path.name}: {len(old['samples'])}/{len(samples)} saved ({old['inference_seconds']:.1f}s inference)",
                flush=True,
            )
    old["complete"] = True
    old["samples"] = [results[s["id"]] for s in samples]
    save(path, old)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Checkpoint interval; inference stays at batch size 1",
    )
    args = parser.parse_args()
    assert args.batch_size > 0
    os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/koyal-numba")
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/koyal-matplotlib")
    model_hash = sha256(args.model)
    clips, contexts = build_samples()
    import torch
    import nemo.collections.asr as asr

    torch.set_num_threads(4)
    model = asr.models.ASRModel.restore_from(str(args.model), map_location="cpu")
    model.eval()
    with torch.inference_mode():
        run_set(
            model, clips, DATA / "koyal-vocabulary.json", model_hash, args.batch_size
        )
        run_set(
            model,
            contexts,
            DATA / "koyal-vocabulary-context.json",
            model_hash,
            args.batch_size,
        )


if __name__ == "__main__":
    main()
