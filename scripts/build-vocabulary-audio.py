"""Build word clips and lesson players from the reviewed large-v3 alignment."""

import argparse
import csv
import hashlib
import importlib.util
import json
import io
import shutil
import re
from functools import lru_cache
from pathlib import Path
from audio_segments import cut
from audio_lexicon import english_score
from audio_repairs import apply_repairs, apply_label_repairs, add_reference_controls
from audio_tables import add_audio_columns, strip_audio_columns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/assets/audio/moag/words"
BLOCK = re.compile(
    r"\n<!-- moag-vocabulary-words -->\n.*?<!-- /moag-vocabulary-words -->\n", re.S
)
spec = importlib.util.spec_from_file_location(
    "vocab_alignment", ROOT / "scripts/align-vocabulary-audio.py"
)
alignment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alignment)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def course_lexicon():
    result = {}
    for path in sorted(
        (ROOT / "data/audio/moag/vocabulary-recognition").glob("lesson_??.json")
    ):
        for candidate in alignment.candidates(
            json.loads(path.read_text())["textbook_vocabulary"]
        ):
            result.setdefault(candidate["text"], candidate)
    return list(result.values())


def readable(text):
    return (
        bool(re.search(r"[\u0d00-\u0d7f]", text))
        and len(text) < 110
        and "\ufffd" not in text
        and not re.search(r"(.{1,4})\1{4}", text)
    )


def final_words(record):
    reviews_path = ROOT / "data/audio/moag/vocabulary-reviews.json"
    reviews = json.loads(reviews_path.read_text()) if reviews_path.exists() else {}
    adjustments_path = ROOT / "data/audio/moag/vocabulary-adjustments.json"
    if adjustments_path.exists():
        record = {**record, "words": [dict(word) for word in record["words"]]}
        for adjustment in json.loads(adjustments_path.read_text()):
            if adjustment["lesson"] != record["lesson"]:
                continue
            merged = [
                word for word in record["words"] if word["id"] in adjustment["merge"]
            ]
            assert [word["id"] for word in merged] == adjustment["merge"]
            first = merged[0]
            first.update(
                utterances=[u for word in merged for u in word["utterances"]],
                raw_texts=[t for word in merged for t in word["raw_texts"]],
                transcript=adjustment["transcript"],
                status="review",
                similarity=0,
                adjustment=adjustment["reason"],
            )
            record["words"] = [
                word
                for word in record["words"]
                if word["id"] not in adjustment["merge"][1:]
            ]
    path = (
        ROOT / f"data/audio/moag/vocabulary-rechecks/lesson_{record['lesson']:02d}.json"
    )
    rechecks = json.loads(path.read_text()) if path.exists() else {}
    candidates = alignment.candidates(record["textbook_vocabulary"])
    result = []
    excluded = []
    announcements = json.loads(
        (
            ROOT
            / f"data/audio/moag/vocabulary-recognition/lesson_{record['lesson']:02d}-boundaries.json"
        ).read_text()
    )["segments"]
    extra_path = ROOT / "data/audio/moag/vocabulary-tail-announcements.json"
    if extra_path.exists():
        announcements += [
            s
            for s in json.loads(extra_path.read_text())
            if s["lesson"] == record["lesson"]
        ]
    for original in record["words"]:
        word = {**original}
        evidence = rechecks.get(word["id"])
        if (
            evidence
            and evidence["start"] == word["utterances"][0]["start"]
            and evidence["end"] == word["utterances"][-1]["end"]
        ):
            word["recheck_text"] = evidence["text"]
            probe = dict(raw_texts=[evidence["text"]])
            best = max(candidates, key=lambda c: alignment.score(probe, c))
            best_score = alignment.score(probe, best)
            prior_score = alignment.score(probe, dict(text=word["transcript"]))
            if word["status"] == "matched":
                pass  # An isolated recheck must not override stronger contextual evidence.
            elif prior_score >= 0.7:
                word["status"] = "matched"
                word["similarity"] = round(prior_score, 3)
            elif best_score >= 0.85 and (
                alignment.score(original, best) >= 0.65
                or not any(readable(t) for t in original["raw_texts"])
            ):
                word.update(
                    transcript=best["text"],
                    meaning=best["meaning"],
                    textbook_row=best["row"],
                    similarity=round(best_score, 3),
                    status="matched",
                )
            elif not word["transcript"] and readable(evidence["text"]):
                word["transcript"] = evidence["text"].strip()
        # Repeated, clearly recognized forms absent from this edition's table
        # retain their spoken form rather than borrowing an unrelated table row.
        probe_text = word.get("recheck_text", "")
        if (
            original["similarity"] < 0.6
            and readable(probe_text)
            and max(
                (
                    alignment.similarity(probe_text, t)
                    for t in original["raw_texts"]
                    if readable(t)
                ),
                default=0,
            )
            >= 0.85
        ):
            best = max(
                course_lexicon(),
                key=lambda c: alignment.similarity(probe_text, c["text"]),
            )
            transcript = (
                best["text"]
                if alignment.similarity(probe_text, best["text"]) >= 0.9
                else probe_text
            )
            word.update(
                transcript=transcript, textbook_row=None, meaning="", status="review"
            )
        # A short following section title can lie before the old section cut.
        is_last = original["id"] == record["words"][-1]["id"]
        if is_last and len(word["utterances"]) == 1:
            start = word["utterances"][0]["start"]
            end = word["utterances"][0]["end"]
            title = next(
                (
                    s
                    for s in announcements
                    if s["start"] < end
                    and s["end"] > start
                    and re.search(r"lesson|reading practice|exercise", s["text"], re.I)
                ),
                None,
            )
            if title:
                excluded.append(
                    dict(
                        utterances=word["utterances"],
                        reason="Following section announcement",
                        english_recognition=title["text"],
                    )
                )
                continue
        word["transcript"] = re.sub(
            r"^past participle\s*\+\s*", "", word["transcript"], flags=re.IGNORECASE
        )
        word["transcript"] = re.sub(r"\[[A-Za-z]+\]", "", word["transcript"]).strip()
        if not readable(word["transcript"]) and readable(probe_text):
            tokens = probe_text.split()
            cleaned = " ".join(
                token
                for i, token in enumerate(tokens)
                if i == 0 or token != tokens[i - 1]
            )
            best = max(
                course_lexicon(), key=lambda c: alignment.similarity(cleaned, c["text"])
            )
            if (
                alignment.similarity(cleaned, best["text"]) >= 0.9
                and english_score(original, best) >= 0.5
            ):
                word.update(
                    transcript=best["text"],
                    meaning=best["meaning"],
                    textbook_row=None,
                    status="review",
                )
        if not readable(word["transcript"]):
            word.update(transcript="Unclear word", status="untranscribed")
        # Preserve disagreements instead of silently asserting that a broad
        # contextual match has verified an isolated pronunciation.
        if readable(probe_text):
            probe = dict(raw_texts=[probe_text])
            alternative = max(candidates, key=lambda c: alignment.score(probe, c))
            if (
                alignment.score(probe, alternative) >= 0.85
                and alignment.score(probe, dict(text=word["transcript"])) < 0.55
            ):
                word["status"] = "review"
                word["alignment_warning"] = (
                    "Isolated recognition favors " + alternative["text"]
                )
        review = reviews.get(word["id"])
        if (
            review
            and review["transcript"] == word["transcript"]
            and review["start"] == word["utterances"][0]["start"]
            and review["end"] == word["utterances"][-1]["end"]
        ):
            word["status"] = review["status"]
            word["review"] = review
        result.append(word)
    noise_path = ROOT / "data/audio/moag/vocabulary-noise-exclusions.json"
    noise = (
        {item["id"]: item for item in json.loads(noise_path.read_text())}
        if noise_path.exists()
        else {}
    )
    other_exclusions = ROOT / "data/audio/moag/vocabulary-word-exclusions.json"
    if other_exclusions.exists():
        noise.update(
            {item["id"]: item for item in json.loads(other_exclusions.read_text())}
        )
    kept = []
    for word in result:
        item = noise.get(word["id"])
        if item:
            assert item["start"] == word["utterances"][0]["start"]
            assert item["end"] == word["utterances"][-1]["end"]
            assert digest(ROOT / item["path"]) == item["sha256"]
            excluded.append(item)
        else:
            kept.append(word)
    result = kept
    result = apply_repairs(record, result)
    result = apply_label_repairs(record, result)
    # Multiple clips with the same proposed spelling are not automatically
    # evidence of repeated readings: they can indicate a displaced neighbor.
    from collections import defaultdict

    duplicates = defaultdict(list)
    for word in result:
        duplicates[word["transcript"]].append(word)
    for group in duplicates.values():
        if len(group) > 1:
            for word in group:
                if word.get("review", {}).get("reviewer") != "user":
                    if word["status"] != "untranscribed":
                        word["status"] = "review"
                    word["alignment_warning"] = (
                        "Duplicate proposed word assignment needs confirmation"
                    )
    return result, excluded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest_path = OUT / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    old = {c["path"]: c for c in previous.get("clips", [])}
    clips = []
    lessons = []
    ranges = []
    for number in range(1, 26):
        record = json.loads(
            (
                ROOT / f"data/audio/moag/vocabulary-alignment/lesson_{number:02d}.json"
            ).read_text()
        )
        words, excluded = final_words(record)
        announcements = json.loads(
            (
                ROOT
                / f"data/audio/moag/vocabulary-recognition/lesson_{number:02d}-boundaries.json"
            ).read_text()
        )["segments"]
        header = next(s for s in announcements if "vocabulary" in s["text"].lower())
        ranges.append(
            dict(
                lesson=number,
                start=header["start"],
                end=round(
                    max(
                        [words[-1]["utterances"][-1]["end"]]
                        + [
                            item["end"]
                            for item in excluded
                            if item.get("retained_in_continuous_recording")
                        ]
                    )
                    + 0.2,
                    4,
                ),
            )
        )
        for index, word in enumerate(words):
            start = word["utterances"][0]["start"]
            end = word["utterances"][-1]["end"]
            destination = OUT / f"{word['id']}.mp3"
            clip = dict(
                lesson=number,
                transcript=word["transcript"],
                meaning=word["meaning"],
                status=word["status"],
                source=record["source"],
                start=start,
                end=end,
                utterances=word["utterances"],
                recognition=word["raw_texts"],
                recheck=word.get("recheck_text"),
                adjustment=word.get("adjustment"),
                review=word.get("review"),
                alignment_warning=word.get("alignment_warning"),
                path=str(destination.relative_to(ROOT)),
            )
            if word.get("repair"):
                clip["repair"] = word["repair"]
            if word.get("label_review"):
                clip["label_review"] = word["label_review"]
            prior = old.get(clip["path"], {})
            unchanged = all(prior.get(k) == clip[k] for k in ("source", "start", "end"))
            if not args.check and (not unchanged or not destination.exists()):
                repair = word.get("repair")
                if repair and repair.get("audio"):
                    approved = ROOT / repair["audio"]
                    assert digest(approved) == repair["audio_sha256"]
                    shutil.copyfile(approved, destination)
                else:
                    cut(ROOT / record["source"], destination, start, end)
            assert destination.exists(), destination
            clip["sha256"] = digest(destination)
            if args.check:
                assert clip == prior, f"Word clip changed: {clip['path']}"
            clips.append(clip)
        reviews = sum(w["status"] != "matched" for w in words)
        block = (
            '\n<!-- moag-vocabulary-words -->\n<div class="lesson-audio">\n'
            "<p><strong>Selected vocabulary recording</strong></p>\n"
            f'<audio data-table-audio-player controls preload="none" aria-label="Lesson {number}: select a word in the vocabulary table"></audio>\n'
            '<p class="lesson-audio-note">Use the Audio column to hear a word. Recorded variants appear beside their written entry; additional recorded forms are included in the same table. Unconfirmed recordings stay in rows marked “check match” until their word is verified. A dash means no aligned recording yet.</p>\n'
            "</div>\n<!-- /moag-vocabulary-words -->\n"
        )
        page = ROOT / f"docs/lesson{number}.md"
        original = page.read_text()
        text = strip_audio_columns(BLOCK.sub("", original))
        heading = re.search(r"^(#{2,3}) Vocabulary\n", text, re.M)
        assert heading
        position = heading.end()
        following = re.search(
            r"^#{1," + str(len(heading[1])) + r"} ", text[position:], re.M
        )
        end = position + following.start() if following else len(text)
        body = text[position:end]
        forms = []
        for row in record["textbook_vocabulary"]:
            forms.append(
                [row["malayalam"]] + [c["text"] for c in alignment.candidates([row])]
            )
        for word in words:
            if word.get("label_review", {}).get("placement") == "vocabulary":
                forms[word["textbook_row"]].append(word["transcript"])
        entries = [
            dict(word, path=f"docs/assets/audio/moag/words/{word['id']}.mp3")
            for word in words
            if not word.get("reference_entry")
        ]
        body = add_audio_columns(body, entries, forms)
        text = text[:position] + body + text[end:]
        existing = re.match(
            r"\n<!-- moag-audio -->\n.*?<!-- /moag-audio -->\n", text[position:], re.S
        )
        if existing:
            position += existing.end()
        text = text[:position] + block + text[position:]
        text = add_reference_controls(text, words)
        assert strip_audio_columns(BLOCK.sub("", text)) == strip_audio_columns(
            BLOCK.sub("", original)
        ), "Underlying lesson text changed"
        if args.check:
            assert text == original, f"Word players need updating: {page}"
        else:
            page.write_text(text)
        covered = {
            w["textbook_row"] for w in words if w.get("textbook_row") is not None
        }
        missing = [
            r for i, r in enumerate(record["textbook_vocabulary"]) if i not in covered
        ]
        lessons.append(
            dict(
                lesson=number,
                words=len(words),
                uncertain=reviews,
                printed_entries_without_match=missing,
                excluded=excluded,
            )
        )
    manifest = dict(
        model="Whisper large-v3",
        method="Pause boundaries checked by acoustic comparison of adjacent repetitions. Clips propose individual vocabulary items, normally with their two recorded readings; flagged items require transcription and boundary review. Cuts re-encoded for accurate boundaries. Raw recognition, alignment, and individual rechecks retained in data/audio/moag/. Machine transcription is not fluent listening verification.",
        lessons=lessons,
        clips=clips,
    )
    ranges_path = ROOT / "data/audio/moag/vocabulary-ranges.json"
    if args.check:
        assert json.loads(ranges_path.read_text()) == ranges, (
            "Vocabulary ranges need updating"
        )
    else:
        ranges_path.write_text(json.dumps(ranges, indent=2) + "\n")
    if args.check:
        assert manifest == previous, "Word manifest needs updating"
    else:
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        active = {clip["path"] for clip in clips}
        retained_noise = {
            item["path"]
            for lesson in lessons
            for item in lesson["excluded"]
            if item.get("retain_artifact")
        }
        for path, clip in old.items():
            stale = ROOT / path
            if (
                path not in active
                and path not in retained_noise
                and stale.exists()
                and digest(stale) == clip["sha256"]
            ):
                stale.unlink()
    transcript_path = ROOT / "data/audio/moag/vocabulary-transcripts.csv"
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "lesson",
            "transcript",
            "meaning",
            "status",
            "start_seconds",
            "end_seconds",
            "clip",
        ]
    )
    for clip in clips:
        writer.writerow(
            [
                clip["lesson"],
                clip["transcript"],
                clip["meaning"],
                clip["status"],
                clip["start"],
                clip["end"],
                clip["path"],
            ]
        )
    for lesson in lessons:
        for entry in lesson["printed_entries_without_match"]:
            writer.writerow(
                [
                    lesson["lesson"],
                    entry["malayalam"],
                    entry["meaning"],
                    "not_aligned",
                    "",
                    "",
                    "",
                ]
            )
    if args.check:
        assert transcript_path.read_text() == buffer.getvalue(), (
            "Transcript CSV needs updating"
        )
    else:
        with transcript_path.open("w", newline="") as stream:
            stream.write(buffer.getvalue())
    print(
        f"{'Checked' if args.check else 'Built'} {len(clips)} vocabulary word clips in {len(lessons)} lessons; {sum(x['uncertain'] for x in lessons)} transcriptions flagged for review."
    )


if __name__ == "__main__":
    main()
