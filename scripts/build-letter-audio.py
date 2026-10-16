"""Build individual letter clips, retaining complete alphabet and row recitations."""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from audio_segments import cut, speech_spans, duration
from audio_tables import TABLE, cells, add_audio_columns, strip_audio_columns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/assets/ut-austin/letters"
BLOCK = re.compile(r"\n<!-- letter-audio -->\n.*?<!-- /letter-audio -->\n\n", re.S)
GROUPS = [
    (
        "simple-vowels",
        "Simple vowels",
        "571065ff7755-Mal-Vowels-Row-1-Pronunciation.mp3",
        "അ ആ ഇ ഈ ഉ ഊ ഋ",
        "a aa i ii u uu ru",
    ),
    (
        "other-vowels",
        "Other vowels and special sounds",
        "5dfc96156a93-Mal-Vowels-Rows2-3-Pronunciation.mp3",
        "എ ഏ ഐ ഒ ഓ ഔ അം അഃ",
        "e ee ai o oo au am aha",
    ),
    (
        "ka-row",
        "ക row",
        "66b449bb683a-Mal-Consonants-Row-1-Pronunciation.mp3",
        "ക ഖ ഗ ഘ ങ",
        "ka kha ga gha nga",
    ),
    (
        "ca-row",
        "ച row",
        "375d8ea00de1-Mal-Consonants-Row-2-Pronunciation.mp3",
        "ച ഛ ജ ഝ ഞ",
        "ca cha ja jha nya",
    ),
    (
        "tta-row",
        "ട row",
        "f211900719d9-Mal-Consonants-Row-3.mp3",
        "ട ഠ ഡ ഢ ണ",
        "Ta Tha Da Dha Na",
    ),
    (
        "ta-row",
        "ത row",
        "90fbbe5af3a9-Mal-Consonants-ta-row.mp3",
        "ത ഥ ദ ധ ന",
        "ta tha da dha na",
    ),
    (
        "pa-row",
        "പ row",
        "eed4fedcdcfe-Mal-Consonants-pa-row.mp3",
        "പ ഫ ബ ഭ മ",
        "pa pha ba bha ma",
    ),
    (
        "semivowels",
        "Semivowels",
        "6c8c96e67a93-Mal-Consonants-semivowels.mp3",
        "യ ര ല വ",
        "ya ra la va",
    ),
    (
        "sibilants",
        "Sibilants and ഹ",
        "056a460ad698-Mal-Consonants-sibilants.mp3",
        "ശ ഷ സ ഹ",
        "sha Sha sa ha",
    ),
    (
        "special-consonants",
        "ള ഴ റ",
        "7fd7e07874a4-Mal-Consonants-Tamil-row.mp3",
        "ള ഴ റ",
        "La zha rra",
    ),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    previous_path = OUT / "manifest.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    old = {c["path"]: c for c in previous.get("clips", [])}
    clips = []
    recordings = []
    blocks = []
    for key, title, filename, symbols, romanizations in GROUPS:
        source = ROOT / "data/ut-austin/assets" / filename
        spans = speech_spans(source, noise=-42, pause=0.22)
        symbols = symbols.split()
        romanizations = romanizations.split()
        assert len(spans) >= len(symbols), (key, spans)
        row = OUT / f"{key}.mp3"
        if args.check:
            assert row.exists() and digest(row) == digest(source), row
        else:
            row.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, row)
        recordings.append(
            dict(
                group=key,
                source=str(source.relative_to(ROOT)),
                path=str(row.relative_to(ROOT)),
                sha256=digest(source),
            )
        )
        options = [
            f'<button type="button" data-audio-src="assets/ut-austin/letters/{key}.mp3" aria-pressed="true">Full row</button>'
        ]
        for index, (symbol, roman, (s, e)) in enumerate(
            zip(symbols, romanizations, spans)
        ):
            start = round(max(0, s - 0.12), 4)
            end = round(min(duration(source), e + 0.15), 4)
            path = OUT / f"{key}-{index + 1:02d}.mp3"
            record = dict(
                symbol=symbol,
                romanization=roman,
                group=key,
                source=str(source.relative_to(ROOT)),
                source_sha256=digest(source),
                start=start,
                end=end,
                path=str(path.relative_to(ROOT)),
            )
            prior = old.get(record["path"], {})
            unchanged = all(prior.get(k) == v for k, v in record.items())
            if not args.check and (not unchanged or not path.exists()):
                cut(source, path, start, end)
            assert path.exists(), path
            record["sha256"] = digest(path)
            if args.check:
                assert record == prior, record
            clips.append(record)
        blocks.append(
            f'<div class="lesson-audio">\n<p><strong>{title}</strong></p>\n<audio controls preload="none" aria-label="{title}: full row or selected letter" src="assets/ut-austin/letters/{key}.mp3"></audio>\n<div class="lesson-audio-cues">'
            + "".join(options)
            + "</div>\n</div>"
        )
    manifest = dict(
        method="Individual letter utterances in source chart order; FFmpeg pause detection at -42 dB, 0.22 seconds, excluding noise shorter than 0.1 seconds. Each cut has 120 ms leading and 150 ms trailing padding. Re-encoded for sample-accurate cuts. Complete row recordings and alphabet recitation retained. Romanization follows the textbook; zha and rra disambiguate the last row.",
        source_page="https://malayalam.la.utexas.edu/resources/pronunciation-the-basics/",
        license="CC BY 4.0; see ../manifest.json for source credits.",
        recordings=recordings,
        clips=clips,
    )
    if args.check:
        assert manifest == previous, "Letter manifest changed"
    else:
        previous_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
    page = ROOT / "docs/alphabet.md"
    original = page.read_text()
    text = strip_audio_columns(BLOCK.sub("", original))
    forms = [
        [cells(line)[0]]
        for table in TABLE.finditer(text)
        for line in table[0].splitlines()[2:]
    ]
    text = add_audio_columns(
        text,
        [
            dict(transcript=clip["symbol"], path=clip["path"], status="matched")
            for clip in clips
        ],
        forms,
    )
    block = (
        '\n<!-- letter-audio -->\n<a id="letter-audio"></a>\n<a id="alphabet-listen-to-the-alphabet-and-individual-letters"></a><!-- reading-anchor -->\n### Listen to the Alphabet and Individual Letters\n\nUse the Audio column beside each letter below. Consonants include the inherent vowel. The full alphabet and row recitations are also available.\n\n<div class="lesson-audio">\n<p><strong>Complete alphabet recitation</strong></p>\n<audio data-table-audio-player controls preload="none" aria-label="Complete Malayalam alphabet recitation" src="assets/ut-austin/alphabet.mp3"></audio>\n<div class="lesson-audio-cues"><button type="button" data-audio-src="assets/ut-austin/alphabet.mp3" aria-pressed="true">Full alphabet</button></div>\n</div>\n\n'
        + "<details><summary>Full vowel and consonant row recitations</summary>\n\n"
        + "\n\n".join(blocks)
        + "\n</details>"
        + "\n\nRecordings: [UT Austin, Malayalam Pronunciation: The Basics](https://malayalam.la.utexas.edu/resources/pronunciation-the-basics/), shared under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Individual clips are excerpts; full row recordings are unchanged. [Recording provenance and clip times](assets/ut-austin/letters/manifest.json).\n<!-- /letter-audio -->\n"
    )
    text = text.replace("**Vowels:**", block + "\n**Vowels:**", 1)
    if args.check:
        assert original == text, "Alphabet page needs updating"
    else:
        page.write_text(text)
    print(
        f"{'Checked' if args.check else 'Built'} {len(clips)} individual letter clips and {len(recordings)} full rows."
    )


if __name__ == "__main__":
    main()
