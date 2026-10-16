"""Shared pause detection for the word and letter recording builders."""

import re
import subprocess


def duration(path):
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            text=True,
        )
    )


def speech_spans(path, noise=-38, pause=0.4, minimum=0.1):
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-af",
            f"silencedetect=noise={noise}dB:d={pause}",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    start = 0.0
    spans = []
    for kind, value in re.findall(r"silence_(start|end): ([\d.]+)", result.stderr):
        point = float(value)
        if kind == "start" and point - start >= minimum:
            spans.append((start, point))
        elif kind == "end":
            start = point
    end = duration(path)
    if end - start >= minimum:
        # FFmpeg reports an open final silence's end at EOF, so start == end.
        if not spans or start > spans[-1][1]:
            spans.append((start, end))
    return spans


def cut(source, destination, start, end):
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Decode before seeking and re-encode: MP3 frame copying is too coarse for
    # individual consonants, and may retain sound from an adjacent item.
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-ss",
            str(start),
            "-t",
            str(end - start),
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
