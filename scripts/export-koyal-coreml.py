"""Export Koyal's TDT neural components directly from NeMo/PyTorch to Core ML.

Requires nemo-toolkit[asr], coremltools, torch, numpy on macOS. This exports
components, not a complete Swift transcriber. Feature extraction, tokenization,
and TDT duration/blank decoding must be supplied by the consuming application.
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--frames', type=int, default=1024, help='Fixed padded mel frame count')
    parser.add_argument('--fp16', action='store_true', help='Use FP16 internal computation; default FP32')
    args = parser.parse_args()
    if not args.model.is_file() or args.frames < 64:
        parser.error('Provide a local .nemo checkpoint and at least 64 frames')

    import coremltools as ct
    import numpy as np
    import torch
    import nemo.collections.asr as asr
    from nemo.core.classes import typecheck
    from omegaconf import OmegaConf

    torch.set_num_threads(4)
    torch.manual_seed(0)
    model = asr.models.ASRModel.restore_from(str(args.model), map_location='cpu').eval()
    model.joint.set_fuse_loss_wer(False)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    class Encoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = model.encoder

        def forward(self, features, length):
            return self.encoder(audio_signal=features, length=length)

    class Predictor(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.decoder = model.decoder

        def forward(self, token, h, c):
            g, (hn, cn) = self.decoder.predict(token, [h, c], add_sos=False)
            return g.transpose(1, 2), hn, cn

    class Joint(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.joint = model.joint

        def forward(self, encoded, predicted):
            return self.joint(encoder_outputs=encoded, decoder_outputs=predicted)

    decoder = model.decoder
    if not decoder.blank_as_pad:
        raise RuntimeError('This exporter requires blank_as_pad for predictor initialization')
    features = torch.randn(1, model.cfg.preprocessor.features, args.frames)
    length = torch.tensor([args.frames - 16], dtype=torch.int32)
    token = torch.tensor([[decoder.blank_idx]], dtype=torch.int32)
    states = decoder.initialize_state(torch.zeros(1, 1, decoder.pred_hidden))
    encoder, predictor, joint = Encoder().eval(), Predictor().eval(), Joint().eval()
    with torch.inference_mode(), typecheck.disable_checks():
        encoded, _ = encoder(features, length)
        predicted, _, _ = predictor(token, *states)
        parts = [
            ('encoder', encoder, (features, length), ['features', 'length'], ['encoded', 'encoded_length']),
            ('predictor', predictor, (token, *states), ['token', 'h', 'c'], ['predicted', 'h_out', 'c_out']),
            ('joint', joint, (encoded[:, :, :1], predicted), ['encoded', 'predicted'], ['logits']),
        ]
        manifest = dict(model='adalat-ai/koyal-ml-120m-1.0', checkpoint=str(args.model.resolve()),
                        frames=args.frames, precision='float16' if args.fp16 else 'float32',
                        blank_id=decoder.blank_idx,
                        preprocessor=OmegaConf.to_container(model.cfg.preprocessor, resolve=True),
                        decoder=OmegaConf.to_container(model.cfg.decoder, resolve=True),
                        joint=OmegaConf.to_container(model.cfg.joint, resolve=True),
                        components={},
                        status='Exported components only; application preprocessing and TDT decoding required')
        for name, module, example, input_names, output_names in parts:
            print(f'Tracing {name}', flush=True)
            traced = torch.jit.trace(module, example, check_trace=False)
            with torch.inference_mode():
                eager = module(*example)
                traced_result = traced(*example)
            eager = eager if isinstance(eager, tuple) else (eager,)
            traced_result = traced_result if isinstance(traced_result, tuple) else (traced_result,)
            for a, b in zip(eager, traced_result, strict=True):
                torch.testing.assert_close(a, b)
            inputs = [ct.TensorType(name=n, shape=tuple(t.shape), dtype=np.int32 if t.dtype in (torch.int32, torch.int64) else np.float32) for n, t in zip(input_names, example, strict=True)]
            print(f'Converting {name}', flush=True)
            converted = ct.convert(traced, inputs=inputs,
                                   outputs=[ct.TensorType(name=n) for n in output_names],
                                   convert_to='mlprogram', minimum_deployment_target=ct.target.macOS14,
                                   compute_precision=ct.precision.FLOAT16 if args.fp16 else ct.precision.FLOAT32,
                                   skip_model_load=True)
            converted.short_description = f'Koyal Malayalam TDT {name}'
            converted.license = 'CC-BY-4.0'
            converted.author = 'Adalat AI (original model)'
            converted.save(str(args.output_dir / f'{name}.mlpackage'))
            traced.save(str(args.output_dir / f'{name}.pt'))
            np.savez(args.output_dir / f'{name}-test-inputs.npz', **{n:t.numpy() for n,t in zip(input_names, example, strict=True)})
            np.savez(args.output_dir / f'{name}-test-outputs.npz', **{n:t.numpy() for n,t in zip(output_names, eager, strict=True)})
            manifest['components'][name] = dict(inputs={n:list(t.shape) for n,t in zip(input_names,example,strict=True)}, outputs=output_names, pytorch_trace_checked=True, coreml_prediction_checked=False)
            (args.output_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (args.output_dir / 'tokenizer.model').write_bytes(model.tokenizer.tokenizer.serialized_model_proto())
    vocab = {str(i):model.tokenizer.ids_to_tokens([i])[0] for i in range(decoder.blank_idx)}
    (args.output_dir / 'vocabulary.json').write_text(json.dumps(vocab, ensure_ascii=False, indent=2) + '\n')
    print(f'Saved components to {args.output_dir}. Core ML runtime validation remains required.', flush=True)


if __name__ == '__main__':
    main()
