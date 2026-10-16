"""Apply explicit, source-anchored vocabulary repairs without rewriting lesson text."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path
import re

from audio_tables import TABLE, add_audio_columns, cells, key

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def repairs():
    path = ROOT / "data/audio/moag/vocabulary-cut-repairs.json"
    return json.loads(path.read_text()) if path.exists() else []


@lru_cache(maxsize=None)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_repairs(record, words):
    words = [dict(w) for w in words]
    by_id = {w["id"]: w for w in words}
    for repair in repairs():
        if repair["lesson"] != record["lesson"]:
            continue
        assert record["source"] == repair["source"]
        assert digest(ROOT / repair["source"]) == repair["source_sha256"]
        word = by_id[repair["id"]]
        before = repair["previous"]
        assert word["utterances"][0]["start"] == before["start"]
        assert word["utterances"][-1]["end"] == before["end"]
        if repair["placement"] == "vocabulary":
            matches = [
                i
                for i, r in enumerate(record["textbook_vocabulary"])
                if key(r["malayalam"]) == key(repair["printed_entry"]["malayalam"])
            ]
            assert len(matches) == 1, repair["id"]
            row = matches[0]
            assert (
                record["textbook_vocabulary"][row]["meaning"]
                == repair["printed_entry"]["meaning"]
            )
        else:
            row = None
        review = dict(
            transcript=repair["transcript"],
            start=repair["start"],
            end=repair["end"],
            status="matched",
            reviewer=repair["reviewer"],
            scope=repair["scope"],
        )
        word.update(
            transcript=repair["transcript"],
            meaning=repair["printed_entry"]["meaning"],
            utterances=repair["utterances"],
            textbook_row=row,
            status="matched",
            review=review,
            alignment_warning=None,
            repair=repair,
            reference_entry=repair["placement"] == "reference",
        )
    return words


def add_reference_controls(text, words):
    entries = [
        dict(
            w,
            path=f"docs/assets/audio/moag/words/{w['id']}.mp3",
            written_form=w["transcript"],
        )
        for w in words
        if w.get("reference_entry")
    ]
    if not entries:
        return text
    heading = re.search(r"^(#{2,3}) Reference List\n", text, re.M)
    assert heading
    start = heading.end()
    next_heading = re.search(
        r"^#{1," + str(len(heading[1])) + r"} ", text[start:], re.M
    )
    end = start + next_heading.start() if next_heading else len(text)
    body = text[start:end]
    forms = []
    for table in TABLE.finditer(body):
        for line in table[0].splitlines()[2:]:
            columns = cells(line)
            forms.append([columns[2].strip()] if len(columns) == 4 else [])
    for entry in entries:
        assert (
            sum(key(entry["transcript"]) in {key(f) for f in row} for row in forms) == 1
        )
    return text[:start] + add_audio_columns(body, entries, forms) + text[end:]


@lru_cache(maxsize=1)
def label_repairs():
    path = ROOT / "data/audio/moag/vocabulary-label-repairs.json"
    return json.loads(path.read_text()) if path.exists() else []


def apply_label_repairs(record, words):
    by_id = {w["id"]: w for w in words}
    for repair in label_repairs():
        if repair["lesson"] != record["lesson"]:
            continue
        assert record["source"] == repair["source"]
        assert digest(ROOT / repair["source"]) == repair["source_sha256"]
        word = by_id[repair["id"]]
        assert word["utterances"][0]["start"] == repair["start"]
        assert word["utterances"][-1]["end"] == repair["end"]
        assert digest(ROOT / repair["previous"]["path"]) == repair["clip_sha256"]
        row = None
        if repair["placement"] == "vocabulary":
            matches = [
                i
                for i, r in enumerate(record["textbook_vocabulary"])
                if r == repair["printed_entry"]
            ]
            assert len(matches) == 1, repair["id"]
            row = matches[0]
        word.update(
            transcript=repair["transcript"],
            textbook_row=row,
            status=repair["status"],
            label_review=repair,
            review=dict(
                transcript=repair["transcript"],
                start=repair["start"],
                end=repair["end"],
                status=repair["status"],
                reviewer=repair["reviewer"],
                scope=repair["scope"],
            ),
            alignment_warning=None
            if repair["status"] == "matched"
            else repair["scope"],
        )
        if row is not None:
            word["meaning"] = record["textbook_vocabulary"][row]["meaning"]
        else:
            word["meaning"] = repair.get("meaning", "")
    return words
