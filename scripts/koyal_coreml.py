"""Reusable CPU Core ML runtime matching the local Koyal reference decoder.

Token durations are TDT frame skips, not verified phonetic boundaries.
"""

from pathlib import Path
import json
import time


class KoyalCoreML:
    def __init__(self, directory):
        import coremltools as ct
        import numpy as np
        import sentencepiece as spm
        import torch
        from nemo.collections.asr.modules import AudioToMelSpectrogramPreprocessor

        self.np, self.torch = np, torch
        torch.set_num_threads(4)
        directory = Path(directory)
        self.manifest = json.loads((directory / "manifest.json").read_text())
        config = dict(self.manifest["preprocessor"])
        config.pop("_target_", None)
        config["dither"] = 0
        self.preprocessor = AudioToMelSpectrogramPreprocessor(**config).eval()
        self.models = {
            name: ct.models.MLModel(
                str(directory / f"{name}.mlpackage"),
                compute_units=ct.ComputeUnit.CPU_ONLY,
            )
            for name in ("encoder", "predictor", "joint")
        }
        self.tokenizer = spm.SentencePieceProcessor(
            model_file=str(directory / "tokenizer.model")
        )
        self.frame_seconds = config["window_stride"] * 4

    def transcribe(self, audio):
        np, torch = self.np, self.torch
        started = time.perf_counter()
        with torch.inference_mode():
            features, length = self.preprocessor(
                input_signal=torch.from_numpy(audio)[None],
                length=torch.tensor([len(audio)]),
            )
        frames = self.manifest["frames"]
        if features.shape[-1] > frames:
            raise ValueError(
                f"{features.shape[-1]} mel frames exceed fixed model capacity {frames}"
            )
        padded = np.zeros((1, features.shape[1], frames), dtype=np.float32)
        padded[:, :, : features.shape[-1]] = features.numpy()
        prepared = time.perf_counter()
        enc = self.models["encoder"].predict(
            dict(features=padded, length=length.numpy().astype(np.int32))
        )
        encoded_at = time.perf_counter()
        shape = self.manifest["components"]["predictor"]["inputs"]["h"]
        h, c = np.zeros(shape, dtype=np.float32), np.zeros(shape, dtype=np.float32)
        blank = self.manifest["blank_id"]
        token, t, tokens, cached_prediction = blank, 0, [], None
        out_len = int(enc["encoded_length"].item())
        while t < out_len:
            skip = 0
            for _ in range(10):
                # Blank emissions do not alter predictor inputs. Reuse that exact
                # prediction, rather than crossing the Core ML bridge again.
                if cached_prediction is None:
                    cached_prediction = self.models["predictor"].predict(
                        dict(token=np.array([[token]], dtype=np.int32), h=h, c=c)
                    )
                pred = cached_prediction
                logits = (
                    self.models["joint"]
                    .predict(
                        dict(
                            encoded=enc["encoded"][:, :, t : t + 1],
                            predicted=pred["predicted"],
                        )
                    )["logits"]
                    .reshape(-1)
                )
                k = int(np.argmax(logits[: blank + 1]))
                skip = int(np.argmax(logits[blank + 1 :]))
                if k != blank:
                    tokens.append(
                        dict(
                            id=k,
                            piece=self.tokenizer.id_to_piece(k),
                            start=round(t * self.frame_seconds, 4),
                            duration=round(skip * self.frame_seconds, 4),
                        )
                    )
                    h, c, token = pred["h_out"], pred["c_out"], k
                    cached_prediction = None
                t += skip
                if skip:
                    break
            if skip == 0:
                t += 1
        finished = time.perf_counter()
        return dict(
            text=self.tokenizer.decode([x["id"] for x in tokens]),
            tokens=tokens,
            seconds=finished - started,
            preprocessing_seconds=prepared - started,
            encoder_seconds=encoded_at - prepared,
            decoder_seconds=finished - encoded_at,
        )
