"""Reference Koyal Core ML TDT inference for short audio clips on macOS.

NeMo/PyTorch is used only for matching mel preprocessing and the optional
comparison; encoder, prediction network, and joint execute through Core ML.
This is a validation reference, not a standalone Swift/iOS implementation.
"""

import argparse
import json
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--audio', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compare-nemo', type=Path, help='Optional original .nemo checkpoint')
    parser.add_argument('--compute-units', choices=['cpu_only', 'cpu_and_ne', 'all'], default='cpu_only')
    args = parser.parse_args()
    import coremltools as ct
    import numpy as np
    import sentencepiece as spm
    import torch
    from nemo.collections.asr.modules import AudioToMelSpectrogramPreprocessor

    torch.set_num_threads(4)
    manifest = json.loads((args.models / 'manifest.json').read_text())
    config = dict(manifest['preprocessor'])
    config.pop('_target_', None)
    config['dither'] = 0
    preprocessor = AudioToMelSpectrogramPreprocessor(**config).eval()
    compute_units = {'cpu_only':ct.ComputeUnit.CPU_ONLY, 'cpu_and_ne':ct.ComputeUnit.CPU_AND_NE, 'all':ct.ComputeUnit.ALL}[args.compute_units]
    models = {n:ct.models.MLModel(str(args.models / f'{n}.mlpackage'), compute_units=compute_units) for n in ('encoder', 'predictor', 'joint')}
    tokenizer = spm.SentencePieceProcessor(model_file=str(args.models / 'tokenizer.model'))
    blank = manifest['blank_id']
    state_shape = manifest['components']['predictor']['inputs']['h']
    frame_seconds = config['window_stride'] * 4  # Koyal encoder has x4 subsampling.
    reference = None
    if args.compare_nemo:
        import nemo.collections.asr as asr

        reference = asr.models.ASRModel.restore_from(str(args.compare_nemo), map_location='cpu').eval()
        reference.preprocessor.featurizer.dither = 0
    report = []
    for source in args.audio:
        started = time.monotonic()
        audio = np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(source), '-ar', '16000', '-ac', '1', '-f', 'f32le', '-']), dtype=np.float32).copy()
        with torch.inference_mode():
            features, length = preprocessor(input_signal=torch.from_numpy(audio)[None], length=torch.tensor([len(audio)]))
        if features.shape[-1] > manifest['frames']:
            raise ValueError(f'{source}: {features.shape[-1]} frames exceeds exported {manifest["frames"]}; use shorter audio or re-export with --frames')
        padded = np.zeros((1, features.shape[1], manifest['frames']), dtype=np.float32)
        padded[:, :, :features.shape[-1]] = features.numpy()
        enc = models['encoder'].predict(dict(features=padded, length=length.numpy().astype(np.int32)))
        h = np.zeros(state_shape, dtype=np.float32)
        c = np.zeros(state_shape, dtype=np.float32)
        token, t, tokens = blank, 0, []
        out_len = int(enc['encoded_length'].item())
        while t < out_len:
            skip = 0
            for _ in range(10):
                pred = models['predictor'].predict(dict(token=np.array([[token]], dtype=np.int32), h=h, c=c))
                logits = models['joint'].predict(dict(encoded=enc['encoded'][:, :, t:t+1], predicted=pred['predicted']))['logits'].reshape(-1)
                k = int(np.argmax(logits[:blank+1]))
                skip = int(np.argmax(logits[blank+1:]))  # TDT durations are [0,1,2,3,4].
                if k != blank:
                    tokens.append(dict(id=k, piece=tokenizer.id_to_piece(k), start=round(t*frame_seconds, 4), duration=round(skip*frame_seconds, 4)))
                    h, c, token = pred['h_out'], pred['c_out'], k
                t += skip
                if skip:
                    break
            if skip == 0:
                t += 1
        row = dict(audio=str(source), coreml=tokenizer.decode([x['id'] for x in tokens]), tokens=tokens,
                   compute_units=args.compute_units, precision=manifest['precision'],
                   inference_seconds=round(time.monotonic() - started, 4))
        if reference is not None:
            with torch.inference_mode():
                row['nemo'] = reference.transcribe([audio], batch_size=1)[0].text
            row['matches_nemo'] = row['coreml'] == row['nemo']
        report.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
