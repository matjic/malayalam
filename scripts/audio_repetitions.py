"""Compare adjacent utterances to retain same-word pronunciation pairs.

Requires numpy and scipy from the transcription environment. This acoustic
comparison supplies boundaries, never text labels.
"""

import subprocess
import numpy as np
from scipy.fft import dct
from scipy.signal import stft


def features(source, utterances):
    audio = np.frombuffer(
        subprocess.check_output(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(source),
                "-ar",
                "16000",
                "-ac",
                "1",
                "-f",
                "f32le",
                "-",
            ]
        ),
        np.float32,
    )
    result = []
    # A compact log-spectrum cepstrum, excluding the overall energy coefficient.
    for u in utterances:
        a = audio[round(u["start"] * 16000) : round(u["end"] * 16000)]
        _, _, spectrum = stft(
            a, fs=16000, nperseg=400, noverlap=240, nfft=512, boundary=None
        )
        power = np.abs(spectrum) ** 2
        energy = power.sum(axis=0)
        keep = energy > max(energy.max() * 0.005, 1e-12)
        cepstrum = dct(np.log(np.maximum(power, 1e-12)), axis=0, norm="ortho")[
            1:14, keep
        ].T
        result.append(cepstrum if len(cepstrum) else np.zeros((1, 13)))
    scale = np.concatenate(result).std(axis=0) + 1e-5
    return [r / scale for r in result]


def distance(a, b):
    cost = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2) / np.sqrt(a.shape[1])
    n, m = cost.shape
    dp = np.full((n + 1, m + 1), np.inf)
    dp[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i, j] = cost[i - 1, j - 1] + min(
                dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1]
            )
    return float(dp[n, m] / max(n, m))


def pair_utterances(source, utterances):
    fs = features(source, utterances)
    distances = [distance(a, b) for a, b in zip(fs, fs[1:])]
    n = len(utterances)
    dp = [float("inf")] * (n + 1)
    back = {}
    dp[0] = 0
    # Preserve the ordinary two-read pattern unless the acoustic comparison makes
    # a single utterance clearly preferable. The single cost is relative to the
    # recording's own distribution, rather than a fixed volume threshold.
    baseline = float(np.percentile(distances, 40)) if distances else 1
    single = baseline * 0.9
    for i in range(n):
        if dp[i] + single < dp[i + 1]:
            dp[i + 1] = dp[i] + single
            back[i + 1] = i
        if i + 1 < n and dp[i] + distances[i] < dp[i + 2]:
            dp[i + 2] = dp[i] + distances[i]
            back[i + 2] = i
    groups = []
    i = n
    while i:
        start = back[i]
        groups.append(utterances[start:i])
        i = start
    groups.reverse()
    return groups, distances
