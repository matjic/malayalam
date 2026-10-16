"""Compare exported Core ML components with saved PyTorch test vectors on macOS."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--rtol', type=float, default=0.005)
    parser.add_argument('--atol', type=float, default=0.005)
    args = parser.parse_args()
    import coremltools as ct
    import numpy as np

    path = args.directory
    manifest = json.loads((path / 'manifest.json').read_text())
    report = {}
    failures = []
    for name in manifest['components']:
        model = ct.models.MLModel(str(path / f'{name}.mlpackage'), compute_units=ct.ComputeUnit.CPU_ONLY)
        inputs = dict(np.load(path / f'{name}-test-inputs.npz'))
        expected = dict(np.load(path / f'{name}-test-outputs.npz'))
        actual = model.predict(inputs)
        report[name] = {}
        for key in expected:
            delta = np.abs(actual[key] - expected[key])
            matches = bool(np.allclose(actual[key], expected[key], rtol=args.rtol, atol=args.atol))
            report[name][key] = dict(max_absolute_error=float(delta.max()), mean_absolute_error=float(delta.mean()),
                                    rtol=args.rtol, atol=args.atol, allclose=matches)
            if not matches:
                failures.append(f'{name}.{key}')
        manifest['components'][name]['coreml_prediction_checked'] = all(r['allclose'] for r in report[name].values())
        print(name, report[name], flush=True)
    (path / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    (path / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    if failures:
        raise SystemExit('Numerical tolerance failed (full report saved): ' + ', '.join(failures))


if __name__ == '__main__':
    main()
