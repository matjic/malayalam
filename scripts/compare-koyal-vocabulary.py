#!/usr/bin/env python3
"""Compare independent recognizers with user reviews without certifying labels."""

from collections import Counter
import csv
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/audio/moag"


def canonical(text):
    """Ignore spacing/punctuation; retain vowel distinctions, endings and extra text."""
    text = unicodedata.normalize("NFC", text)
    for legacy, modern in [
        ("ണ്\u200d", "ൺ"),
        ("ന്\u200d", "ൻ"),
        ("ര്\u200d", "ർ"),
        ("ല്\u200d", "ൽ"),
        ("ള്\u200d", "ൾ"),
        ("ക്\u200d", "ൿ"),
    ]:
        text = text.replace(legacy, modern)
    return "".join(c.lower() for c in text if unicodedata.category(c)[0] in "LMN")


def comparison_key(text):
    """Collapse only exact whole-output repetitions, never fuzzy token windows."""
    value = canonical(text)
    for repetitions in range(4, 1, -1):
        if len(value) >= repetitions and len(value) % repetitions == 0:
            unit = value[: len(value) // repetitions]
            if unit * repetitions == value:
                return unit
    return value


def equal(a, b):
    return bool(comparison_key(a)) and comparison_key(a) == comparison_key(b)


def main():
    recognized = json.loads((DATA / "koyal-vocabulary.json").read_text())
    contextual = json.loads((DATA / "koyal-vocabulary-context.json").read_text())
    assert recognized["complete"] and contextual["complete"]
    assert len(recognized["samples"]) == 1005
    context_map = {s["id"]: s for s in contextual["samples"]}
    audit = json.loads((DATA / "vocabulary-context-audit.json").read_text())
    audit_map = {s["id"]: s for s in audit["clips"]}
    buzz_path = DATA / "buzzasr-sample-results.json"
    buzz = json.loads(buzz_path.read_text()) if buzz_path.exists() else {"rows": []}
    buzz_map = {s["id"]: s for s in buzz["rows"]}
    rows = []
    for sample in recognized["samples"]:
        clip_id = sample["id"]
        a = audit_map[clip_id]
        human = a["human_review"] or {}
        reference = (
            a["effective_review_transcript"]
            if human and human["decision"] != "flagged"
            else ""
        )
        koyal = sample["koyal"]
        agrees_human = equal(koyal, reference) if reference else None
        agrees_published = equal(koyal, a["published_transcript"])
        category = (
            ("human_agreement" if agrees_human else "human_disagreement")
            if reference
            else (
                "user_flagged"
                if human
                else (
                    "automatic_agreement"
                    if agrees_published
                    else "automatic_disagreement"
                )
            )
        )
        if not human and a.get("prior_user_review"):
            category = (
                "prior_label_agreement"
                if agrees_published
                else "prior_label_disagreement"
            )
        whisper_texts = [*a["raw_malayalam"], a["isolated_recheck"]]
        previous = next(
            (n for n in a["neighbors"] if n["source_start"] < a["source_start"]), {}
        )
        following = next(
            (n for n in a["neighbors"] if n["source_start"] > a["source_start"]), {}
        )
        row = dict(
            id=clip_id,
            lesson=a["lesson"],
            published_transcript=a["published_transcript"],
            published_status=a["published_status"],
            human_decision=human.get("decision", ""),
            human_reference=reference,
            human_notes=human.get("notes", ""),
            koyal=koyal,
            comparison=category,
            koyal_agrees_human=agrees_human,
            koyal_agrees_published=agrees_published,
            exact_whole_output_repetition_normalized=canonical(koyal)
            != comparison_key(koyal),
            empty_koyal=not bool(koyal.strip()),
            any_whisper_agreement=any(equal(koyal, s) for s in whisper_texts),
            isolated_whisper=a["isolated_recheck"],
            raw_whisper=" / ".join(a["raw_malayalam"]),
            previous_id=previous.get("id", ""),
            previous_label=previous.get("review_transcript")
            or previous.get("published_transcript", ""),
            next_id=following.get("id", ""),
            next_label=following.get("review_transcript")
            or following.get("published_transcript", ""),
            context_result=a["context_result"],
            suggested_transcript=a["suggested_transcript"],
            context_reason=a["context_reason"],
            context_koyal=context_map.get(clip_id, {}).get("koyal", ""),
            context_start=context_map.get(clip_id, {}).get("start"),
            context_end=context_map.get(clip_id, {}).get("end"),
            buzzasr=buzz_map.get(clip_id, {}).get("buzzasr", ""),
            source_start=a["source_start"],
            source_end=a["source_end"],
            clip=a["clip"],
        )
        row["followup"] = category in (
            "human_disagreement",
            "user_flagged",
            "automatic_disagreement",
            "prior_label_disagreement",
        ) or a["context_result"] not in (
            "automatic_unverified",
            "prior_user_review",
            "context_consistent_with_user_review",
            "use_entered_correction",
        )
        rows.append(row)
    assert len({r["id"] for r in rows}) == 1005
    comparison = []
    by_id = {r["id"]: r for r in rows}
    for b in buzz["rows"]:
        r = by_id[b["id"]]
        comparison.append(
            dict(
                id=b["id"],
                reference=b["reference"],
                koyal=r["koyal"],
                buzzasr=b["buzzasr"],
                koyal_agrees=equal(r["koyal"], b["reference"]),
                buzzasr_agrees=equal(b["buzzasr"], b["reference"]),
                previous_agrees=equal(b["previous"], b["reference"]),
            )
        )
    summary = dict(
        total=1005,
        context_excerpts=len(context_map),
        categories=dict(Counter(r["comparison"] for r in rows)),
        empty_koyal=sum(r["empty_koyal"] for r in rows),
        followup=sum(r["followup"] for r in rows),
        clip_inference_seconds=recognized["inference_seconds"],
        context_inference_seconds=contextual["inference_seconds"],
        shared_buzzasr_sample=dict(
            clips=len(comparison),
            koyal_agreements=sum(r["koyal_agrees"] for r in comparison),
            buzzasr_agreements=sum(r["buzzasr_agrees"] for r in comparison),
            previous_label_agreements=sum(r["previous_agrees"] for r in comparison),
        ),
    )
    report = dict(
        summary=summary,
        normalization="NFC, equivalent legacy chillu forms, ignore spacing/punctuation, collapse exact whole-output repetitions of 2–4 copies. Keep different vowels, endings, numerals and extra speech.",
        caveats=[
            "Agreement counts are not accuracy estimates: references are user reviews, some explicitly uncertain or contextually contradicted.",
            "The 16-clip BuzzASR sample was deliberately selected and is not a representative benchmark; comparison uses the saved outputs only.",
            "Whisper raw/group timestamps can be misaligned. Agreement between models is supporting evidence, not verification.",
            "Context recognition is untimed text covering multiple clips; do not assign its words to individual clips by fuzzy matching.",
            "Empty output does not establish silence. No teaching labels or audio cuts have been changed.",
        ],
        shared_buzzasr_comparison=comparison,
        clips=rows,
    )
    (DATA / "koyal-comparison.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    for name, entries in [
        ("koyal-comparison.csv", rows),
        ("koyal-followup.csv", [r for r in rows if r["followup"]]),
    ]:
        with (DATA / name).open("w") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(entries)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
