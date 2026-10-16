#!/usr/bin/env python3
"""Benchmark local Core ML Koyal and sweep targeted source-audio boundaries.

Never changes textbook wording or production clips. Writes experimental cuts
only when the exact printed form is recognized twice and both edges are quiet.
"""

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

from koyal_coreml import KoyalCoreML
from audio_tables import strip_audio_columns, cells

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/audio/moag"
spec = importlib.util.spec_from_file_location(
    "comparison", ROOT / "scripts/compare-koyal-vocabulary.py"
)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)
RATE = 16000


def decode(source, start=None, end=None):
    import numpy as np

    command = ["ffmpeg", "-v", "error", "-i", str(source)]
    if start is not None:
        command += ["-ss", str(start), "-t", str(end - start)]
    command += ["-ar", str(RATE), "-ac", "1", "-f", "f32le", "-"]
    return np.frombuffer(subprocess.check_output(command), dtype=np.float32).copy()


def cases():
    # Explicit targets come from existing printed tables, not model substitutions.
    return [
        dict(
            id="lesson_24_sneham",
            lesson=24,
            target="സ്നേഹം",
            printed_role="Existing verb/noun reference table",
            old="lesson_24_word_027",
            starts=[369.75, 369.85, 369.95],
            ends=[373.3, 373.5, 373.7, 373.9, 374.2, 374.5],
        ),
        dict(
            id="lesson_24_thammil",
            lesson=24,
            target="തമ്മിൽ",
            printed_role="Vocabulary",
            old="lesson_24_word_028",
            starts=[373.5, 373.65, 373.8, 373.95],
            ends=[376.55, 376.7, 376.85],
        ),
        dict(
            id="lesson_24_gunam",
            lesson=24,
            target="ഗുണം",
            printed_role="Vocabulary",
            old="lesson_24_word_051",
            starts=[480.9, 481.05, 481.2],
            ends=[484.5, 484.65, 484.8, 484.95, 485.2, 485.6],
        ),
        dict(
            id="lesson_24_kuravu",
            lesson=24,
            target="കുറവ്",
            printed_role="Vocabulary",
            old="lesson_24_word_052",
            starts=[484.65, 484.8, 484.95, 485.1],
            ends=[487.6, 487.75, 487.9],
        ),
        dict(
            id="lesson_21_tharuka",
            lesson=21,
            target="തരുക",
            printed_role="Vocabulary construction: past participle + തരുക",
            old="lesson_21_word_015",
            starts=[204.35, 204.45, 204.55],
            ends=[207.0, 207.3, 207.7, 208.1, 208.5, 209.0],
        ),
        dict(
            id="lesson_21_paranjutharuka",
            lesson=21,
            target="പറഞ്ഞുതരുക",
            printed_role="Vocabulary",
            old="lesson_21_word_016",
            starts=[208.4, 208.55, 208.7, 208.85],
            ends=[212.15, 212.3, 212.45],
        ),
        dict(
            id="lesson_04_panam",
            lesson=4,
            target="പണം",
            printed_role="Vocabulary",
            old="lesson_04_word_028",
            starts=[166.8, 166.95, 167.1],
            ends=[169.6, 169.8, 170.0, 170.3, 170.8],
        ),
        dict(
            id="lesson_04_onnu",
            lesson=4,
            target="ഒന്ന്",
            printed_role="Vocabulary",
            old="lesson_04_word_029",
            starts=[170.25, 170.4, 170.55],
            ends=[172.9, 173.1, 173.3],
        ),
        dict(
            id="lesson_04_avanu",
            lesson=4,
            target="അവന്",
            printed_role="Vocabulary",
            old="lesson_04_word_027",
            starts=[163.2, 163.35, 163.5],
            ends=[165.9, 166.1, 166.3],
        ),
    ]


def printed_entry(case):
    source = ROOT / f"docs/lesson{case['lesson']}.md"
    original = strip_audio_columns(source.read_text())
    target = (
        "past participle + തരുക" if case["id"] == "lesson_21_tharuka" else case["target"]
    )
    matches = []
    for line in original.splitlines():
        if not line.startswith("|"):
            continue
        columns = cells(line)
        for i in range(0, len(columns) - 1, 2):
            if compare.canonical(columns[i]) == compare.canonical(target):
                matches.append(
                    dict(malayalam=columns[i].strip(), meaning=columns[i + 1].strip())
                )
    assert matches, (case["id"], target)
    return matches[0]


def rms_db(audio):
    import numpy as np

    return float(20 * np.log10(max(float(np.sqrt(np.mean(audio**2))), 1e-10)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models", type=Path, default=Path("/private/tmp/koyal-coreml")
    )
    parser.add_argument(
        "--nemo",
        type=Path,
        default=Path("/private/tmp/koyal-ml-120m-1.0/koyal-ml-120m-1.0.nemo"),
    )
    parser.add_argument("--benchmark-only", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter()
    runtime = KoyalCoreML(args.models)
    load_seconds = time.perf_counter() - started
    import torch
    import nemo.collections.asr as asr

    reference = asr.models.ASRModel.restore_from(
        str(args.nemo), map_location="cpu"
    ).eval()
    reference.preprocessor.featurizer.dither = 0
    benchmark = []
    for clip_id in [
        "lesson_03_word_001",
        "lesson_16_word_040",
        "lesson_24_word_027",
        "lesson_24_word_051",
    ]:
        source = ROOT / f"docs/assets/audio/moag/words/{clip_id}.mp3"
        audio = decode(source)
        runtime.transcribe(audio)  # Warm both runtimes before the timed observation.
        with torch.inference_mode():
            reference.transcribe([audio], batch_size=1, verbose=False)
        coreml = runtime.transcribe(audio)
        began = time.perf_counter()
        with torch.inference_mode():
            nemo = reference.transcribe([audio], batch_size=1, verbose=False)[0].text
        nemo_seconds = time.perf_counter() - began
        row = dict(
            id=clip_id,
            audio_seconds=len(audio) / RATE,
            coreml=coreml["text"],
            nemo=nemo,
            identical=coreml["text"] == nemo,
            coreml_seconds=coreml["seconds"],
            nemo_seconds=nemo_seconds,
            timing_parts={k: v for k, v in coreml.items() if k.endswith("_seconds")},
            tokens=coreml["tokens"],
        )
        benchmark.append(row)
        print(
            f"Benchmark {clip_id}: Core ML {coreml['seconds']:.3f}s, NeMo {nemo_seconds:.3f}s, equal={row['identical']}",
            flush=True,
        )
    report = dict(
        compute_units="CPU_ONLY",
        padded_frames=runtime.manifest["frames"],
        predictor_blank_cache=True,
        model_load_seconds=load_seconds,
        benchmark=benchmark,
        benchmark_method="One timed observation per clip, after warming both runtimes; excludes model load and ffmpeg decode. Both include mel preprocessing; NeMo includes transcribe data-loader overhead.",
        cases=[],
        caveats=[
            "Crop transcription agreement is not listening verification.",
            "The same Malayalam recognizer across crops is correlated evidence; do not choose a cut just because it elicits the expected word.",
            "Quiet-edge checks cannot prove complete phonemes. Candidate cuts require listening.",
            "TDT token durations are frame skips, not phonetic lengths.",
            "CPU Core ML performance does not establish Neural Engine or iOS performance.",
            "All experimental cuts retain the source target twice; original published clips remain unchanged.",
        ],
    )
    path = DATA / "koyal-coreml-boundary-trial.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.benchmark_only:
        return
    export = ROOT / "docs/assets/audio/moag/boundary-trial"
    export.mkdir(parents=True, exist_ok=True)
    for case in cases():
        source = DATA / f"lesson_{case['lesson']:02}.mp3"
        lesson_text = (ROOT / f"docs/lesson{case['lesson']}.md").read_text()
        assert compare.canonical(case["target"]) in compare.canonical(
            strip_audio_columns(lesson_text)
        ), case["id"]
        left, right = min(case["starts"]) - 0.05, max(case["ends"]) + 0.05
        audio = decode(source, left, right)
        target = compare.canonical(case["target"])
        trials = []
        for start in case["starts"]:
            for end in case["ends"]:
                a, b = round((start - left) * RATE), round((end - left) * RATE)
                cut = audio[a:b].copy()
                if len(cut) / RATE > 5:
                    continue
                recognized = runtime.transcribe(cut)
                raw_key = compare.canonical(recognized["text"])
                count = (
                    len(raw_key) // len(target)
                    if target
                    and len(raw_key) % len(target) == 0
                    and target * (len(raw_key) // len(target)) == raw_key
                    else 0
                )
                edge_samples = round(0.06 * RATE)
                first_db, last_db = (
                    rms_db(cut[:edge_samples]),
                    rms_db(cut[-edge_samples:]),
                )
                trials.append(
                    dict(
                        start=start,
                        end=end,
                        transcript=recognized["text"],
                        exact_target_repetitions=count,
                        preprocessing_and_inference_seconds=recognized["seconds"],
                        first_60ms_rms_db=first_db,
                        last_60ms_rms_db=last_db,
                        quiet_edges=first_db < -35 and last_db < -35,
                        tokens=[
                            {**t, "source_start": round(start + t["start"], 4)}
                            for t in recognized["tokens"]
                        ],
                    )
                )
        # Keep both readings, require quiet edges, and require agreement at two
        # different starts and two different ends, rather than one lucky crop.
        matches = [
            t for t in trials if t["exact_target_repetitions"] == 2 and t["quiet_edges"]
        ]
        stable = (
            len({t["start"] for t in matches}) >= 2
            and len({t["end"] for t in matches}) >= 2
        )
        selected = None
        if stable:
            ms = sum(t["start"] for t in matches) / len(matches)
            me = sum(t["end"] for t in matches) / len(matches)
            selected = min(
                matches, key=lambda t: abs(t["start"] - ms) + abs(t["end"] - me)
            )
            destination = export / f"{case['id']}.mp3"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(source),
                    "-ss",
                    str(selected["start"]),
                    "-t",
                    str(selected["end"] - selected["start"]),
                    "-map_metadata",
                    "-1",
                    "-codec:a",
                    "libmp3lame",
                    "-q:a",
                    "3",
                    str(destination),
                ],
                check=True,
            )
            selected = {
                **selected,
                "preview": str(destination.relative_to(ROOT)),
                "preview_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            }
        result = {
            **case,
            "source": str(source.relative_to(ROOT)),
            "printed_entry": printed_entry(case),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "trials": trials,
            "stable_quiet_two_repetition_match": stable,
            "selected": selected,
            "production_applied": False,
        }
        report["cases"].append(result)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            f"{case['id']}: {len(trials)} crops, {len(matches)} matching quiet crops, preview={bool(selected)}",
            flush=True,
        )
    fields = [
        "case",
        "target",
        "start",
        "end",
        "transcript",
        "exact_target_repetitions",
        "quiet_edges",
        "first_60ms_rms_db",
        "last_60ms_rms_db",
        "preprocessing_and_inference_seconds",
    ]
    with (DATA / "koyal-coreml-boundary-trial.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for case in report["cases"]:
            writer.writerows(
                {**trial, "case": case["id"], "target": case["target"]}
                for trial in case["trials"]
            )


if __name__ == "__main__":
    main()
