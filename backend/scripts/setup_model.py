from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path


MODEL_URL = (
    "https://huggingface.co/Pugazh24/X-MalForensics-XGBoost/resolve/main/"
    "baseline_xgboost.json"
)
EXPECTED_SHA256 = "1dafb3b9c826457c158f8950687ad653f005dd4d5a29a39040047499405e08ee"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and verify X-MalForensics-XGBoost")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "models" / "baseline_xgboost.json",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output: Path = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists() and not args.force:
        if digest(output) == EXPECTED_SHA256:
            print(f"Verified model already exists: {output}")
            return 0
        print("Existing model has the wrong SHA-256. Use --force to replace it.", file=sys.stderr)
        return 1

    temporary = output.with_suffix(output.suffix + ".download")
    temporary.unlink(missing_ok=True)
    print(f"Downloading public model from {MODEL_URL}")
    try:
        urllib.request.urlretrieve(MODEL_URL, temporary)
        actual = digest(temporary)
        if actual != EXPECTED_SHA256:
            raise RuntimeError(f"SHA-256 mismatch: expected {EXPECTED_SHA256}, received {actual}")
        temporary.replace(output)
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        print(f"Model setup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Verified model installed at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

