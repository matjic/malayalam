"""Render reversible audio columns in the textbook's existing Markdown tables."""

import html
import re
import unicodedata

TABLE = re.compile(r"(?:^\|[^\n]*\n)+", re.MULTILINE)
EXTRA = "<!-- recorded-audio-row -->"


def cells(line):
    return re.split(r"(?<!\\)\|", line.strip())[1:-1]


def key(text):
    text = re.sub(r"<!--.*?-->|<[^>]+>", "", text)
    text = html.unescape(text).replace("\\*", "").replace("*", "")
    return "".join(
        c for c in unicodedata.normalize("NFC", text) if "\u0d00" <= c <= "\u0d7f"
    )


def strip_audio_columns(text):
    def strip(match):
        lines = match[0].splitlines()
        if cells(lines[0])[-1].strip() != "Audio":
            return match[0]
        return "".join(
            re.sub(r"\|[^|]*\|\s*$", "|", line) + "\n"
            for line in lines
            if EXTRA not in line
        )

    return TABLE.sub(strip, text)


def button(entry, written):
    label = entry["transcript"]
    unplaced = (
        entry.get("label_review", {}).get("placement") == "unplaced_recorded_form"
    )
    review = (
        (" · check placement" if unplaced else " · check match")
        if entry.get("status", "matched") != "matched"
        else ""
    )
    source = entry["path"].removeprefix("docs/")
    primary = re.split(r"<br\s*/?>|\(", written)[0]
    variant = (
        f' <span lang="ml">{html.escape(label)}</span>'
        if key(primary) != key(label)
        else ""
    )
    return (
        f'<button type="button" class="row-audio-button" data-row-audio-src="{html.escape(source, quote=True)}" '
        f'data-audio-label="{html.escape(label, quote=True)}" aria-label="Play {html.escape(label, quote=True)}{review}" '
        f'title="Play {html.escape(label, quote=True)}{review}" aria-pressed="false">▶{variant}{review}</button>'
    )


def add_audio_columns(text, entries, forms):
    """forms supplies exact written alternatives for each original table row."""
    tables = list(TABLE.finditer(text))
    rows = [
        (table, i, line)
        for table in tables
        for i, line in enumerate(table[0].splitlines())
        if i >= 2
    ]
    assert len(rows) == len(forms), (len(rows), len(forms))
    assigned = [[] for _ in rows]
    extra = []
    for entry in entries:
        if entry.get("status", "matched") != "matched":
            extra.append(entry)
            continue
        matches = [
            i
            for i, alternatives in enumerate(forms)
            if key(entry["transcript"]) in {key(a) for a in alternatives}
        ]
        preferred = entry.get("textbook_row")
        if matches:
            index = preferred if preferred in matches else matches[0]
            assigned[index].append(entry)
        else:
            extra.append(entry)
    row_index = 0
    replacements = []
    for table_index, table in enumerate(tables):
        lines = table[0].splitlines()
        output = [lines[0].rstrip() + " Audio |", lines[1].rstrip() + "---|"]
        for line in lines[2:]:
            controls = (
                " ".join(
                    button(entry, entry.get("written_form", cells(line)[0]))
                    for entry in assigned[row_index]
                )
                or '<span class="audio-unmatched" title="No aligned recording yet">—</span>'
            )
            output.append(line.rstrip() + " " + controls + " |")
            row_index += 1
        if table_index == len(tables) - 1:
            for entry in extra:
                uncertain = entry.get("status", "matched") != "matched"
                unplaced = (
                    entry.get("label_review", {}).get("placement")
                    == "unplaced_recorded_form"
                )
                meaning = (
                    "Transcribed; placement in the printed tables needs review"
                    if unplaced
                    else "Audio-to-word match needs review"
                    if uncertain
                    else entry.get("meaning") or "Recorded form"
                )
                written = (
                    "Recorded form: "
                    if unplaced
                    else "Unconfirmed: "
                    if uncertain
                    else ""
                ) + entry["transcript"]
                output.append(
                    f"| {EXTRA} {html.escape(written)} | {meaning.replace('|', '&#124;')} | {button(entry, entry['transcript'])} |"
                )
        replacements.append((table.start(), table.end(), "\n".join(output) + "\n"))
    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]
    return text
