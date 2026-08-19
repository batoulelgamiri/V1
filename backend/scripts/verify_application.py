from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.api.dependencies import get_detection_engine
from app.main import app


def main() -> int:
    engine = get_detection_engine()
    if not engine.available:
        print("Application loaded, but the model engine is unavailable.")
        return 1
    print(f"Application verified: {app.title}; model={engine.model_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
