from __future__ import annotations

import sys

import lief
import numpy
import sklearn
import xgboost


EXPECTED = {
    "python": "3.10",
    "numpy": "1.23.5",
    "sklearn": "1.1.3",
    "lief": "0.10.1",
    "xgboost": "1.7.6",
}


def main() -> int:
    actual = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "numpy": numpy.__version__,
        "sklearn": sklearn.__version__,
        # The verified Windows Conda build identifies itself as ``0.10.1-``.
        "lief": str(lief.__version__).rstrip("-"),
        "xgboost": xgboost.__version__,
    }

    print("Detected model environment:")
    for name, detected in actual.items():
        print(f"  {name}: {detected} (required: {EXPECTED[name]})")

    mismatches = [
        f"{name}: expected {EXPECTED[name]}, found {actual[name]}"
        for name in EXPECTED
        if actual[name] != EXPECTED[name]
    ]
    if mismatches:
        print("Dependency verification failed:", file=sys.stderr)
        for mismatch in mismatches:
            print(f"  {mismatch}", file=sys.stderr)
        return 1

    print("Exact EMBER/XGBoost environment verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

