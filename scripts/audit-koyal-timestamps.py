#!/usr/bin/env python3
"""Compare source word times with existing cuts; propose spans for printed rows.

This is a dry run: neither lesson text nor production audio is modified.
"""

import csv
import html
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/audio/moag"
spec = importlib.util.spec_from_file_location(
    "koyal_compare", ROOT / "scripts/compare-koyal-vocabulary.py"
)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def original_forms(row):
    """Allow source-listed alternatives and optional full phrases, not fuzzy labels."""
    text = re.sub(r"<!--.*?-->", "", row["malayalam"])
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\[[A-Za-z]+\]", "", text)
    alternatives = []
    # Parenthetical Malayalam pronouns/endings are optional within the full phrase.
    # Inflection annotations contribute their explicitly printed forms separately.
    variants = [text]
    for group in re.findall(r"\([^()]*\)", text):
        content = group[1:-1]
        optional = bool(re.fullmatch(r"[\u0d00-\u0d7f\s]+", content))
        variants = [
            v.replace(group, replacement, 1)
            for v in variants
            for replacement in (["", content] if optional else [""])
        ]
        if (
            re.search(r"past|plural|accusative|masculine|feminine", content, re.I)
            and ":" in content
        ):
            alternatives.append(content.split(":", 1)[1])
    # Some explicitly listed plurals are in the printed meaning column.
    for content in re.findall(r"\([^()]*\)", row["meaning"]):
        if (
            re.search(r"plural|past|masculine|feminine", content, re.I)
            and ":" in content
        ):
            alternatives.append(content.split(":", 1)[1])
    result = []
    for variant in variants + alternatives:
        for form in re.split(r",|\bor\b| / ", variant):
            # English grammar markers and dashes are notation, not spoken labels.
            form = re.sub(r"[^\u0d00-\u0d7f\d\s]", " ", form)
            form = " ".join(form.split())
            if form and form not in result:
                result.append(form)
    return result


def validate_timestamps(record):
    chunks = record["chunks"]
    bounds = record["transcription_range"]
    assert chunks and abs(chunks[0]["start"] - bounds["start"]) < 0.0001
    assert abs(chunks[-1]["end"] - bounds["end"]) < 0.0001
    assert all(abs(a["end"] - b["start"]) < 0.0001 for a, b in zip(chunks, chunks[1:]))
    for word in record["words"]:
        chunk = chunks[word["chunk"]]
        assert (
            chunk["start"] - 0.0001
            <= word["start"]
            <= word["end"]
            <= chunk["end"] + 0.1001
        )
        assert abs(word["start"] - word["section_start"] - bounds["start"]) < 0.0002
        assert abs(word["end"] - word["section_end"] - bounds["start"]) < 0.0002
    assert len(record["words"]) == sum(len(c["raw_word_timestamps"]) for c in chunks)


def main():
    published = list(csv.DictReader((DATA / "vocabulary-transcripts.csv").open()))
    published = [r for r in published if r["clip"]]
    comparison = json.loads((DATA / "koyal-comparison.json").read_text())
    compared = {r["id"]: r for r in comparison["clips"]}
    audit_rows, proposed_rows = [], []
    word_total, edge_total = 0, 0
    for lesson in range(1, 26):
        record = json.loads(
            (DATA / f"koyal-timestamps/lesson_{lesson:02}.json").read_text()
        )
        validate_timestamps(record)
        words = record["words"]
        word_total += len(words)
        edge_total += sum(w["near_chunk_edge"] for w in words)
        local = [r for r in published if int(r["lesson"]) == lesson]
        for row in local:
            start, end = float(row["start_seconds"]), float(row["end_seconds"])
            inside = [w for w in words if start <= (w["start"] + w["end"]) / 2 <= end]
            crossing = [
                w
                for w in words
                if w["end"] > start
                and w["start"] < end
                and (w["start"] < start - 0.15 or w["end"] > end + 0.15)
            ]
            text = " ".join(w["word"] for w in inside)
            clip_id = Path(row["clip"]).stem
            c = compared[clip_id]
            audit_rows.append(
                dict(
                    id=clip_id,
                    lesson=lesson,
                    published_transcript=row["transcript"],
                    human_reference=c["human_reference"],
                    koyal_isolated=c["koyal"],
                    source_timed_text=text,
                    timed_agrees_published=compare.equal(text, row["transcript"]),
                    timed_agrees_human=compare.equal(text, c["human_reference"])
                    if c["human_reference"]
                    else None,
                    timed_agrees_isolated=compare.equal(text, c["koyal"]),
                    words=inside,
                    crosses_existing_cut=crossing,
                    near_chunk_edge=any(w["near_chunk_edge"] for w in inside),
                    source_start=start,
                    source_end=end,
                    clip=row["clip"],
                )
            )
        vocab = json.loads(
            (DATA / f"vocabulary-recognition/lesson_{lesson:02}.json").read_text()
        )["textbook_vocabulary"]
        active_start = min(float(r["start_seconds"]) for r in local) - 0.1
        active_end = max(float(r["end_seconds"]) for r in local) + 0.1
        keys = [compare.canonical(w["word"]) for w in words]
        for index, row in enumerate(vocab):
            forms = original_forms(row)
            candidates = []
            for form in forms:
                target = compare.canonical(form)
                hits = []
                for a, first in enumerate(words):
                    if first["start"] < active_start or first["end"] > active_end:
                        continue
                    combined = ""
                    for b in range(a, min(a + 16, len(words))):
                        if (
                            words[b]["end"] > active_end
                            or words[b]["end"] - first["start"] > 12
                        ):
                            break
                        combined += keys[b]
                        if not target.startswith(combined):
                            break
                        if combined == target:
                            hits.append(
                                dict(
                                    first_word=a,
                                    last_word=b,
                                    start=first["start"],
                                    end=words[b]["end"],
                                    near_chunk_edge=any(
                                        w["near_chunk_edge"] for w in words[a : b + 1]
                                    ),
                                )
                            )
                            break
                groups = []
                for hit in hits:
                    if (
                        groups
                        and hit["first_word"] == groups[-1][-1]["last_word"] + 1
                        and hit["start"] - groups[-1][-1]["end"] <= 4
                    ):
                        groups[-1].append(hit)
                    else:
                        groups.append([hit])
                for group in groups:
                    a, b = group[0]["first_word"], group[-1]["last_word"]
                    previous_end = words[a - 1]["end"] if a else active_start
                    next_start = (
                        words[b + 1]["start"] if b + 1 < len(words) else active_end
                    )
                    speech_start, speech_end = group[0]["start"], group[-1]["end"]
                    left_gap, right_gap = (
                        max(0, speech_start - previous_end),
                        max(0, next_start - speech_end),
                    )
                    cut_start = max(
                        active_start, speech_start - min(0.15, left_gap / 2)
                    )
                    cut_end = min(active_end, speech_end + min(0.2, right_gap / 2))
                    if cut_end <= cut_start:
                        continue
                    overlaps = [
                        Path(r["clip"]).stem
                        for r in local
                        if float(r["end_seconds"]) > speech_start
                        and float(r["start_seconds"]) < speech_end
                    ]
                    candidates.append(
                        dict(
                            form=form,
                            repetitions=len(group),
                            speech_start=speech_start,
                            speech_end=speech_end,
                            proposed_start=round(cut_start, 4),
                            proposed_end=round(cut_end, 4),
                            near_chunk_edge=any(h["near_chunk_edge"] for h in group),
                            word_indices=[a, b],
                            overlapping_existing_clips=overlaps,
                            raw_source_words=[w["word"] for w in words[a : b + 1]],
                            selection="ambiguous_multiple_occurrences"
                            if len(groups) > 1
                            else (
                                "exact_repeated_form"
                                if len(group) > 1
                                else "single_recognized_occurrence"
                            ),
                            requires_waveform_and_listening_review=True,
                        )
                    )
            proposed_rows.append(
                dict(
                    lesson=lesson,
                    printed_row=index,
                    original_malayalam=row["malayalam"],
                    original_meaning=row["meaning"],
                    source_listed_forms=forms,
                    result="candidate_spans_found"
                    if candidates
                    else "no_exact_source_span",
                    candidates=candidates,
                )
            )
    assert len(audit_rows) == 1005 and len(proposed_rows) == 941
    summary = dict(
        timestamp_lessons=25,
        timestamped_words=word_total,
        words_near_recognition_chunk_edges=edge_total,
        published_clips_examined=1005,
        clips_with_timestamp_crossings=sum(
            bool(r["crosses_existing_cut"]) for r in audit_rows
        ),
        printed_vocabulary_rows=941,
        printed_rows_with_candidate_spans=sum(
            bool(r["candidates"]) for r in proposed_rows
        ),
        printed_rows_without_exact_span=sum(not r["candidates"] for r in proposed_rows),
        production_changes=False,
    )
    (DATA / "koyal-cut-proposals.json").write_text(
        json.dumps(
            dict(
                policy="Original printed vocabulary and meanings are immutable targets. Recognition only locates candidate source spans; no fuzzy assignment, word substitution, or production edits. Missing exact matches remain unresolved, not proof of a textbook error or absent recording.",
                limitations=[
                    "All timestamps are approximate ASR output.",
                    "Candidate padding is constrained by neighboring recognized words, not yet refined against the waveform.",
                    "Single occurrences, chunk-edge words and multiple occurrences need review.",
                    "Exact matching intentionally misses number formatting, spelling variants and recognition errors; these need contextual review.",
                    "Potential textbook mistakes must be checked separately against the source edition and language evidence.",
                ],
                summary=summary,
                printed_rows=proposed_rows,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    (DATA / "koyal-cutoff-audit.json").write_text(
        json.dumps(
            dict(
                summary=summary,
                method="Recognized words assigned by source-time midpoint only; crossing words extend more than 150 ms beyond an existing cut. These are diagnostic flags, not verified clipping errors.",
                clips=audit_rows,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    fields = [
        "id",
        "lesson",
        "published_transcript",
        "human_reference",
        "koyal_isolated",
        "source_timed_text",
        "timed_agrees_published",
        "timed_agrees_human",
        "timed_agrees_isolated",
        "near_chunk_edge",
        "source_start",
        "source_end",
        "clip",
    ]
    with (DATA / "koyal-cutoff-audit.csv").open("w") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields + ["crossing_words"], extrasaction="ignore"
        )
        writer.writeheader()
        for r in audit_rows:
            writer.writerow(
                {
                    **r,
                    "crossing_words": " / ".join(
                        w["word"] for w in r["crosses_existing_cut"]
                    ),
                }
            )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
