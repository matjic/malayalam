"""Generate Koyal word timestamps for original Moag vocabulary sections.

Requires a NeMo ASR environment, numpy, torch, and ffmpeg. JSON/CSV times
refer to the original lesson MP3, not the exported word clips. No cuts or
labels are modified. Optional SRT/VTT files also use original lesson times.
"""

import argparse
import csv
import json
import math
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RATE = 16000


def chunk_ranges(audio, seconds):
    """Split near low-energy 100 ms windows, without dropping/duplicating audio."""
    import numpy as np

    start = 0
    maximum = round(seconds * RATE)
    window = RATE // 10
    while len(audio) - start > maximum:
        target = start + maximum
        low = max(start + maximum // 2, target - 3 * RATE)
        candidates = range(low, target - window + 1, window)
        quiet = min(candidates, key=lambda i: float(np.mean(audio[i:i + window] ** 2)))
        end = quiet + window // 2
        yield start, end
        start = end
    if start < len(audio):
        yield start, len(audio)


def subtitle_time(seconds, separator):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{separator}{ms:03}'


def save(record, destination, captions):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.with_suffix('.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n'
    )
    fields = ['word', 'start', 'end', 'section_start', 'section_end', 'chunk', 'near_chunk_edge']
    with destination.with_suffix('.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(record['words'])
    if captions:
        for suffix, separator in [('srt', ','), ('vtt', '.')]:
            lines = ['WEBVTT\n'] if suffix == 'vtt' else []
            for index, word in enumerate(record['words'], 1):
                # Some TDT tokens have zero duration; give captions a visible cue.
                start, end = word['start'], max(word['end'], word['start'] + 0.04)
                lines.append(f'{index}\n{subtitle_time(start, separator)} --> '
                             f'{subtitle_time(end, separator)}\n{word["word"]}\n')
            destination.with_suffix('.' + suffix).write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True, help='Local Koyal .nemo checkpoint')
    parser.add_argument('--lessons', type=int, nargs='+', default=list(range(1, 26)))
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'data/audio/moag/koyal-timestamps')
    parser.add_argument('--chunk-seconds', type=float, default=25)
    parser.add_argument('--context', type=float, default=1, help='Extra seconds outside vocabulary range')
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--captions', action='store_true', help='Also write word-level SRT/VTT')
    args = parser.parse_args()
    if not 5 <= args.chunk_seconds <= 30:
        parser.error('--chunk-seconds must be between 5 and 30')
    if not math.isfinite(args.context) or args.context < 0 or args.threads < 1:
        parser.error('--context must be finite and nonnegative; --threads must be positive')
    if not args.model.is_file():
        parser.error('--model must point to a local .nemo checkpoint')
    ranges = {r['lesson']: r for r in json.loads((ROOT / 'data/audio/moag/vocabulary-ranges.json').read_text())}
    if any(n not in ranges for n in args.lessons):
        parser.error('Lessons must be between 1 and 25')

    import numpy as np
    import torch
    import nemo
    import nemo.collections.asr as asr

    torch.set_num_threads(args.threads)
    model = asr.models.ASRModel.restore_from(str(args.model), map_location='cpu')
    model.eval()
    for number in args.lessons:
        bounds = ranges[number]
        start = max(0, bounds['start'] - args.context)
        requested_end = bounds['end'] + args.context
        source = ROOT / f'data/audio/moag/lesson_{number:02}.mp3'
        audio = np.frombuffer(subprocess.check_output([
            'ffmpeg', '-v', 'error', '-i', str(source), '-ss', str(start),
            '-t', str(requested_end - start), '-ar', str(RATE), '-ac', '1', '-f', 'f32le', '-'
        ]), dtype=np.float32).copy()
        if not len(audio):
            raise RuntimeError(f'No audio decoded for lesson {number}')
        record = dict(
            format='koyal-word-timestamps-v1', lesson=number,
            source=str(source.relative_to(ROOT)), model='adalat-ai/koyal-ml-120m-1.0',
            checkpoint=str(args.model.resolve()), nemo_version=nemo.__version__,
            sample_rate=RATE, vocabulary_range=bounds,
            transcription_range=dict(start=start, end=start + len(audio) / RATE),
            time_basis='start/end are seconds in source MP3; section_start/end are relative to transcription_range.start',
            caveats=[
                'Automatic ASR, not verified text or phonetic boundaries; preserve repeated words.',
                'TDT timestamps approximate speech positions. Use nearby silence and padding for final cuts.',
                'near_chunk_edge flags words within 0.25 seconds of a recognition chunk boundary.',
                'Chunks meet at low-energy windows; no audio is omitted. A forced split can still divide speech.',
                'English section announcements may be misrecognized by the Malayalam model.',
            ], chunks=[], words=[])
        for index, (a, b) in enumerate(chunk_ranges(audio, args.chunk_seconds)):
            with tempfile.TemporaryDirectory(prefix='koyal-timestamps-') as temp:
                wav = Path(temp) / 'chunk.wav'
                import wave

                with wave.open(str(wav), 'wb') as stream:
                    stream.setnchannels(1)
                    stream.setsampwidth(2)
                    stream.setframerate(RATE)
                    stream.writeframes((np.clip(audio[a:b], -1, 1) * 32767).astype('<i2').tobytes())
                with torch.inference_mode():
                    hypothesis = model.transcribe([str(wav)], batch_size=1, timestamps=True, return_hypotheses=True)[0]
            stamps = getattr(hypothesis, 'timestamp', None)
            if not isinstance(stamps, dict) or 'word' not in stamps:
                raise RuntimeError('NeMo returned no word timestamps; use a NeMo version supporting TDT timestamps')
            offset, duration = start + a / RATE, (b - a) / RATE
            record['chunks'].append(dict(index=index, start=offset, end=start + b / RATE, text=hypothesis.text, raw_word_timestamps=stamps['word']))
            for word in stamps['word']:
                ws, we = float(word['start']), float(word['end'])
                if not (math.isfinite(ws) and math.isfinite(we) and 0 <= ws <= we <= duration + 0.1):
                    raise RuntimeError(f'Invalid timestamp: {word}')
                record['words'].append(dict(
                    word=word['word'], start=round(offset + ws, 4), end=round(offset + we, 4),
                    section_start=round(a / RATE + ws, 4), section_end=round(a / RATE + we, 4),
                    chunk=index, near_chunk_edge=ws < 0.25 or duration - we < 0.25))
            print(f'Lesson {number}, chunk {index + 1}: {hypothesis.text}', flush=True)
        record['text'] = ' '.join(c['text'] for c in record['chunks'])
        save(record, args.output_dir / f'lesson_{number:02}', args.captions)
        print(f'Saved lesson {number}: {len(record["words"])} words', flush=True)


if __name__ == '__main__':
    main()
