"""Try BuzzASR on a deterministic sample of reviewed vocabulary clips.

Requires torch, transformers 4.57.6, numpy, and ffmpeg. Download the model
separately, then pass --model /path/to/BuzzASR-malayalam.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import unicodedata

import numpy as np
import torch
import transformers
from transformers import WhisperForConditionalGeneration, WhisperProcessor

ROOT = Path(__file__).resolve().parents[1]


def normalized(text):
    return "".join(c for c in unicodedata.normalize("NFC", text) if unicodedata.category(c)[0] in 'LMN')


def distance(a, b):
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        nxt = [i]
        for j, y in enumerate(b, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j - 1] + (x != y)))
        row = nxt
    return row[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', default='/private/tmp/buzzasr-results.json')
    parser.add_argument('--count', type=int, default=16)
    args = parser.parse_args()
    reviews = json.loads((ROOT / 'data/audio/moag/vocabulary-review-export.json').read_text())['reviews']
    # Spread across lessons and include both accepted and corrected ASR outputs.
    candidates = [r for r in reviews if r['decision'] in ('confirmed', 'corrected')]
    selected = []
    for decision in ('corrected', 'confirmed'):
        subset = [r for r in candidates if r['decision'] == decision]
        n = args.count // 2
        selected.extend(subset[round(i * (len(subset) - 1) / max(n - 1, 1))] for i in range(n))
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    dtype = torch.float16 if device == 'mps' else torch.float32
    print(f'Loading model on {device}', flush=True)
    proc = WhisperProcessor.from_pretrained(args.model, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(args.model, dtype=dtype, local_files_only=True).to(device).eval()
    results = dict(model='BuzzASR/malayalam', device=device, transformers_version=transformers.__version__, torch_version=torch.__version__, reference_source='data/audio/moag/vocabulary-review-export.json', normalization='NFC; retain letters, marks, numbers; ignore whitespace and punctuation; do not collapse repetitions', settings=dict(num_beams=1, no_repeat_ngram_size=3, repetition_penalty=1.2, max_new_tokens=96), rows=[])
    for r in selected:
        path = ROOT / 'docs' / r['clip']
        audio = np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-ar', '16000', '-ac', '1', '-f', 'f32le', '-']), dtype=np.float32).copy()
        inputs = proc(audio, sampling_rate=16000, return_tensors='pt', return_attention_mask=True)
        features = inputs.input_features.to(device=device, dtype=dtype)
        start = time.monotonic()
        with torch.inference_mode():
            ids = model.generate(features, attention_mask=inputs.attention_mask.to(device), **results['settings'])
        transcript = proc.batch_decode(ids, skip_special_tokens=True)[0]
        reference = r['correction'] if r['decision'] == 'corrected' else r['proposed_transcript']
        row = dict(id=r['id'], clip=r['clip'], reference=reference, previous=r['proposed_transcript'], buzzasr=transcript, seconds=round(time.monotonic()-start, 2), duration=len(audio)/16000)
        for name, text in [('previous', row['previous']), ('buzzasr', transcript)]:
            row[name + '_exact'] = normalized(text) == normalized(reference)
            row[name + '_edits'] = distance(normalized(reference), normalized(text))
        results['rows'].append(row)
        Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(row, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
