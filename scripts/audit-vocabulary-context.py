#!/usr/bin/env python3
"""Record contextual review evidence without changing production audio or labels."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from audio_tables import key, strip_audio_columns

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/audio/moag"


def read_json(path):
    return json.loads(path.read_text())


def main():
    export_path = DATA / "vocabulary-review-export.json"
    export = read_json(export_path)
    reviews = {r["id"]: r for r in export["reviews"]}
    assert len(reviews) == len(export["reviews"]) == 142
    findings = read_json(DATA / "vocabulary-context-findings.json")
    prior_reviews = read_json(DATA / "vocabulary-reviews.json")
    with (DATA / "vocabulary-transcripts.csv").open() as handle:
        published = [r for r in csv.DictReader(handle) if r["clip"]]
    assert len(published) == 1005
    expected = {
        Path(r["clip"]).stem
        for r in published
        if r["status"] in ("review", "untranscribed")
    }
    assert set(reviews) == expected
    ledger = []
    for lesson in range(1, 26):
        alignment = read_json(DATA / f"vocabulary-alignment/lesson_{lesson:02}.json")
        recognition = read_json(
            DATA / f"vocabulary-recognition/lesson_{lesson:02}.json"
        )
        recheck_path = DATA / f"vocabulary-rechecks/lesson_{lesson:02}.json"
        rechecks = read_json(recheck_path) if recheck_path.exists() else {}
        words = {w["id"]: w for w in alignment["words"]}
        lesson_rows = [r for r in published if int(r["lesson"]) == lesson]
        lesson_path = ROOT / f"docs/lesson{lesson}.md"
        original_text = strip_audio_columns(lesson_path.read_text())
        original_key = key(original_text)
        vocabulary = recognition["textbook_vocabulary"]
        for i, row in enumerate(lesson_rows):
            clip_id = Path(row["clip"]).stem
            word = words[clip_id]
            review = reviews.get(clip_id)
            effective = (
                (review.get("correction") or review["proposed_transcript"])
                if review
                else row["transcript"]
            )
            if review:
                assert all(
                    abs(float(row[k]) - review[k]) < 0.0001
                    for k in ("start_seconds", "end_seconds")
                )
                draft = export["drafts"].get(clip_id, {})
                assert all(
                    draft.get(k, "").strip() == review.get(k, "").strip()
                    for k in ("correction", "notes")
                )
            finding = findings.get(clip_id, {})
            outcome = finding.get(
                "context_result",
                "context_consistent_with_user_review"
                if review
                else (
                    "prior_user_review"
                    if clip_id in prior_reviews
                    else "automatic_unverified"
                ),
            )
            neighbors = []
            for j in range(max(0, i - 1), min(len(lesson_rows), i + 2)):
                if j == i:
                    continue
                nr = lesson_rows[j]
                nid = Path(nr["clip"]).stem
                human = reviews.get(nid)
                neighbors.append(
                    {
                        "id": nid,
                        "published_transcript": nr["transcript"],
                        "review_transcript": (
                            human.get("correction") or human["proposed_transcript"]
                        )
                        if human
                        else None,
                        "source_start": float(nr["start_seconds"]),
                        "source_end": float(nr["end_seconds"]),
                    }
                )
            target_key = key(effective)
            related_vocab = [
                v
                for v in vocabulary
                if target_key
                and (
                    target_key in key(v["malayalam"])
                    or key(v["malayalam"]) in target_key
                )
            ]
            occurrences = []
            if target_key:
                # Original source only: never use generated audio labels as textbook evidence.
                for lineno, line in enumerate(original_text.splitlines(), 1):
                    if target_key in key(line):
                        occurrences.append(
                            {"stripped_source_line": lineno, "text": line[:700]}
                        )
                        if len(occurrences) == 3:
                            break
            start, end = float(row["start_seconds"]), float(row["end_seconds"])
            english = []
            for segment in word.get("english_segments", []):
                overlap = max(
                    0, min(end, segment["end"]) - max(start, segment["start"])
                )
                english.append(
                    {
                        **segment,
                        "overlap_seconds": round(overlap, 4),
                        "segment_seconds": round(segment["end"] - segment["start"], 4),
                    }
                )
            ledger.append(
                {
                    "id": clip_id,
                    "lesson": lesson,
                    "clip": row["clip"],
                    "source_start": start,
                    "source_end": end,
                    "published_transcript": row["transcript"],
                    "published_status": row["status"],
                    "human_review": review,
                    "prior_user_review": prior_reviews.get(clip_id),
                    "effective_review_transcript": effective if review else None,
                    "context_result": outcome,
                    "suggested_transcript": finding.get("suggested_transcript", ""),
                    "context_reason": finding.get(
                        "context_reason",
                        "User identification is consistent with the vocabulary/recognition and neighboring sequence inspected. This is contextual support, not independent auditory verification."
                        if review
                        else "Included in the all-lesson sequence/evidence screen. No specific issue recorded; still an unverified automatic match.",
                    ),
                    "neighbors": neighbors,
                    "text_in_original_lesson": bool(
                        target_key and target_key in original_key
                    ),
                    "related_printed_vocabulary": related_vocab,
                    "original_lesson_occurrences": occurrences,
                    "raw_malayalam": word.get("raw_texts", []),
                    "isolated_recheck": rechecks.get(clip_id, {}).get("text", ""),
                    "english_recognition_segments": english,
                    "utterances": word["utterances"],
                    "auditor_heard_audio": False,
                }
            )
    assert {r["id"] for r in ledger} >= set(findings)
    reviewed = [r for r in ledger if r["human_review"]]
    additional = [r for r in ledger if not r["human_review"] and r["id"] in findings]
    summary = {
        "total_clips_screened": len(ledger),
        "exported_reviews_contextually_examined": len(reviewed),
        "human_review_decisions": dict(
            Counter(r["human_review"]["decision"] for r in reviewed)
        ),
        "review_context_results": dict(Counter(r["context_result"] for r in reviewed)),
        "additional_automatic_matches_needing_followup": len(additional),
        "automatic_matches_without_specific_finding": sum(
            r["context_result"] == "automatic_unverified" for r in ledger
        ),
        "prior_user_reviews_preserved": sum(
            r["context_result"] == "prior_user_review" for r in ledger
        ),
        "independently_listened_by_auditor": 0,
        "production_labels_changed": False,
        "production_cuts_changed": False,
    }
    report = {
        "scope": "All 142 exported reviews were examined against printed lesson vocabulary, original lesson text, their preceding/following clip assignments, available raw Malayalam, isolated rechecks, and English recognition. All 1005 published assignments were screened as ordered sequences; additional specific conflicts were investigated. Automatic matches without findings have not been certified correct.",
        "limitations": [
            "No auditory perception tool is available. Context and model recognition cannot establish exact phonetics or word boundaries.",
            "Broad recognition segments can cover several words and are evidence to inspect, not permission to copy a neighboring label.",
            "Some raw word timestamps/groupings are themselves misaligned; disagreements must remain visible.",
            "Proposed resolutions of user flags are candidates, not new user confirmations.",
            "The original export is preserved. A nonempty correction field is considered even if the decision was confirmed.",
        ],
        "input_sha256": hashlib.sha256(export_path.read_bytes()).hexdigest(),
        "summary": summary,
        "clips": ledger,
    }
    (DATA / "vocabulary-context-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    fields = [
        "id",
        "lesson",
        "published_transcript",
        "published_status",
        "decision",
        "review_transcript",
        "notes",
        "context_result",
        "suggested_transcript",
        "context_reason",
        "previous_clip",
        "next_clip",
        "raw_malayalam",
        "isolated_recheck",
        "english_recognition",
        "source_start",
        "source_end",
        "clip",
    ]
    for filename, entries in [
        ("vocabulary-context-audit.csv", ledger),
        ("vocabulary-review-context.csv", reviewed),
    ]:
        with (DATA / filename).open("w") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for entry in entries:
                human = entry["human_review"] or {}
                neighbors = entry["neighbors"]
                writer.writerow(
                    {
                        **entry,
                        "decision": human.get("decision", ""),
                        "review_transcript": entry["effective_review_transcript"],
                        "notes": human.get("notes", ""),
                        "previous_clip": next(
                            (
                                n["id"]
                                + ": "
                                + (n["review_transcript"] or n["published_transcript"])
                                for n in neighbors
                                if n["source_start"] < entry["source_start"]
                            ),
                            "",
                        ),
                        "next_clip": next(
                            (
                                n["id"]
                                + ": "
                                + (n["review_transcript"] or n["published_transcript"])
                                for n in neighbors
                                if n["source_start"] > entry["source_start"]
                            ),
                            "",
                        ),
                        "raw_malayalam": " / ".join(entry["raw_malayalam"]),
                        "english_recognition": " / ".join(
                            s["text"] for s in entry["english_recognition_segments"]
                        ),
                    }
                )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
