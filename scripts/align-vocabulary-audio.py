"""Match large-v3 utterances to printed vocabulary without hiding ASR evidence."""

import argparse
import hashlib
from difflib import SequenceMatcher
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/audio/moag/vocabulary-recognition"


def normal(text):
    text = unicodedata.normalize("NFC", text)
    text = text.replace("റ്റ", "ട")
    for a, b in {
        "ആ": "അ",
        "ഈ": "ഇ",
        "ഊ": "ഉ",
        "ഏ": "എ",
        "ഓ": "ഒ",
        "ഖ": "ക",
        "ഥ": "ത",
        "ഛ": "ച",
        "ശ": "സ",
        "ഷ": "സ",
        "ം": "മ",
    }.items():
        text = text.replace(a, b)
    for a, b in {
        "ൺ": "ണ",
        "ൻ": "ന",
        "ർ": "ര",
        "ൽ": "ല",
        "ൾ": "ള",
        "ൿ": "ക",
        "ീ": "ി",
        "ൂ": "ു",
        "േ": "െ",
        "ോ": "ൊ",
        "ള": "ല",
        "ണ": "ന",
        "ഗ": "ക",
        "ദ": "ത",
        "ഡ": "ട",
        "ബ": "പ",
        "ഝ": "ജ",
        "ഭ": "പ",
        "ധ": "ത",
        "ഘ": "ക",
        "ഠ": "ട",
        "ഢ": "ട",
        "റ": "ര",
        "ഴ": "ല",
    }.items():
        text = text.replace(a, b)
    text = "".join(c for c in text if "\u0d00" <= c <= "\u0d7f" and c not in "്ംഃ")
    return re.sub(r"(.)\1+", r"\1", text)


def similarity(a, b):
    a = normal(a)
    b = normal(b)
    return SequenceMatcher(None, a, b, autojunk=False).ratio() if a and b else 0


def candidates(rows):
    result = []
    for index, row in enumerate(rows):
        text = re.sub(r"<!--.*?-->", "", row["malayalam"])
        primary = re.split(r"<br>|\(", text)[0]
        forms = re.split(r",| or | / ", primary)
        rest = text[len(primary) :]
        forms += re.findall(r"[\u0d00-\u0d7f]+(?:[ \t]+[\u0d00-\u0d7f]+)*", rest)
        for form in forms:
            form = re.sub(r"^[\s\-*]+|[\s\-*]+$", "", form)
            if normal(form) and (not result or result[-1]["text"] != form):
                result.append(
                    dict(
                        text=form,
                        meaning=row["meaning"],
                        row=index,
                        variant=form != primary,
                    )
                )
    return result


def utterances_for(recognition):
    utterances = []
    for group in recognition["groups"]:
        us = [dict(u, words=[]) for u in group["utterances"]]
        for segment in group["segments"]:
            for word in segment.get("words", []):
                if not re.search("[\u0d00-\u0d7f]", word["word"]):
                    continue
                index = min(
                    range(len(us)),
                    key=lambda i: abs(word["end"] - (us[i]["compact_end"] - 0.18)),
                )
                us[index]["words"].append(word["word"].strip())
        utterances.extend(us)
    # Recover an initial short pronunciation swallowed by an approximate English
    # announcement timestamp. Keep its raw transcript empty for explicit review.
    from audio_segments import speech_spans

    start = recognition["range_start"]
    nearby = [
        (s, e)
        for s, e in speech_spans(
            ROOT / recognition["source"],
            noise=recognition["pause_threshold_db"],
            pause=0.5,
        )
        if start - 1.2 <= s < start - 0.05 and e - s < 0.6
    ]
    if nearby:
        s, e = nearby[-1]
        utterances.insert(
            0, dict(start=round(s - 0.14, 4), end=round(e + 0.18, 4), words=[])
        )
    return utterances


def score(pair, candidate):
    from audio_lexicon import english_score

    texts = pair["raw_texts"]
    # The recognizer sometimes joins repetitions or separates a compound.
    samples = texts + [" ".join(texts)]
    for text in texts:
        samples += text.split()
    return max(
        max((similarity(text, candidate["text"]) for text in samples), default=0),
        english_score(pair, candidate),
    )


def align(recognition):
    from audio_repetitions import pair_utterances

    utterances = utterances_for(recognition)
    expected = candidates(recognition["textbook_vocabulary"])
    grouped, _ = pair_utterances(ROOT / recognition["source"], utterances)
    pairs = [
        dict(
            utterances=[dict(start=u["start"], end=u["end"]) for u in us],
            raw_texts=[" ".join(u["words"]) for u in us],
        )
        for us in grouped
    ]
    english = json.loads(
        (DATA / f"lesson_{recognition['lesson']:02d}-boundaries.json").read_text()
    )["segments"]
    for pair in pairs:
        start = pair["utterances"][0]["start"]
        end = pair["utterances"][-1]["end"]
        pair["english_segments"] = [
            segment
            for segment in english
            if min(end, segment["end"]) - max(start, segment["start"]) > 0.25
        ]
    # Vocabulary recordings interleave the main and supplementary word lists.
    # Assign spellings globally; order is only a weak tie-breaker for ambiguous
    # recognitions, never a constraint that can relabel a clearly spoken word.
    import numpy as np
    from scipy.optimize import linear_sum_assignment

    n = len(pairs)
    m = len(expected)
    costs = np.zeros((n + m, n + m))
    for i, pair in enumerate(pairs):
        for j, candidate in enumerate(expected):
            match = score(pair, candidate)
            costs[i, j] = (
                1 - match
                if any(pair["raw_texts"]) or pair.get("english_segments")
                else 0.55
            ) + 0.25 * abs(i / max(n, 1) - j / max(m, 1))
        costs[i, m:] = 0.7
    for j, candidate in enumerate(expected):
        costs[n:, j] = 0.35 if candidate["variant"] else 0.65
    assigned_rows, assigned_columns = linear_sum_assignment(costs)
    mapped = {
        int(i): int(j)
        for i, j in zip(assigned_rows, assigned_columns)
        if i < n and j < m
    }
    covered = set()
    for index, pair in enumerate(pairs):
        if index in mapped:
            item = expected[mapped[index]]
            match = score(pair, item)
            pair.update(
                transcript=item["text"],
                meaning=item["meaning"],
                textbook_row=item["row"],
                similarity=round(match, 3),
                status="matched" if match >= 0.7 else "review",
            )
            covered.add(item["row"])
        else:
            raw = max(pair["raw_texts"], key=len)
            pair.update(
                transcript=raw.strip() or "",
                meaning="",
                textbook_row=None,
                similarity=0,
                status="review",
            )
        pair["id"] = f"lesson_{recognition['lesson']:02d}_word_{index + 1:03d}"
    return dict(
        pipeline_version=6,
        lesson=recognition["lesson"],
        source=recognition["source"],
        model=recognition["model"],
        range_start=recognition["range_start"],
        range_end=recognition["range_end"],
        method="Acoustic cepstrum comparison pairs repeated utterances independently of textbook order; large-v3 word end timestamps matched to pauses, then global spelling assignment against printed vocabulary (order is only a weak tie-breaker). Low-confidence labels require review. Raw recognizer text retained.",
        words=pairs,
        textbook_vocabulary=recognition["textbook_vocabulary"],
        unmatched_textbook_rows=[
            dict(index=i, **r)
            for i, r in enumerate(recognition["textbook_vocabulary"])
            if i not in covered
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons", type=int, nargs="+", default=range(1, 26))
    args = parser.parse_args()
    out = ROOT / "data/audio/moag/vocabulary-alignment"
    out.mkdir(exist_ok=True)
    for number in args.lessons:
        source = DATA / f"lesson_{number:02d}.json"
        if not source.exists():
            continue
        recognition = json.loads(source.read_text())
        if not recognition.get("complete") or recognition.get("pipeline_version") != 2:
            continue
        destination = out / f"lesson_{number:02d}.json"
        checksum = hashlib.sha256(source.read_bytes()).hexdigest()
        boundary_checksum = hashlib.sha256(
            (DATA / f"lesson_{number:02d}-boundaries.json").read_bytes()
        ).hexdigest()
        if destination.exists():
            prior = json.loads(destination.read_text())
            if (
                prior.get("pipeline_version") == 6
                and prior.get("recognition_sha256") == checksum
                and prior.get("boundary_sha256", boundary_checksum) == boundary_checksum
            ):
                if "boundary_sha256" not in prior:
                    prior["boundary_sha256"] = boundary_checksum
                    destination.write_text(
                        json.dumps(prior, ensure_ascii=False, indent=2) + "\n"
                    )
                print(number, "cached", flush=True)
                continue
        result = align(recognition)
        result["recognition_sha256"] = checksum
        result["boundary_sha256"] = boundary_checksum
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(
            number,
            len(result["words"]),
            "words;",
            sum(w["status"] == "review" for w in result["words"]),
            "need review;",
            len(result["unmatched_textbook_rows"]),
            "unmatched printed entries",
        )


if __name__ == "__main__":
    main()
