from __future__ import annotations

from pathlib import Path

import numpy as np


class FeaturePipelineUnavailable(RuntimeError):
    pass


class EmberV2FeatureExtractor:
    """Strict adapter for the official 2,381-dimensional EMBER 2018 representation."""

    expected_dimension = 2381
    verified_lief_prefixes = ("0.9.0", "0.10.1")

    def __init__(self) -> None:
        try:
            import lief
            from ember.features import PEFeatureExtractor
        except ImportError as exc:
            raise FeaturePipelineUnavailable(
                "The exact EMBER v2 pipeline is not installed. Follow the model setup guide."
            ) from exc

        if not str(lief.__version__).startswith(self.verified_lief_prefixes):
            raise FeaturePipelineUnavailable(
                f"LIEF {lief.__version__} is not verified for EMBER v2. "
                "Install LIEF 0.9.0 or the officially verified 0.10.1 build."
            )
        self.lief_version = str(lief.__version__)
        self.extractor = PEFeatureExtractor(feature_version=2, print_feature_warning=False)
        if int(self.extractor.dim) != self.expected_dimension:
            raise FeaturePipelineUnavailable(
                f"EMBER extractor returned dimension {self.extractor.dim}; expected 2381."
            )

    def extract(self, path: Path) -> np.ndarray:
        bytez = path.read_bytes()
        vector = np.asarray(self.extractor.feature_vector(bytez), dtype=np.float32)
        if vector.shape != (self.expected_dimension,):
            raise FeaturePipelineUnavailable(
                f"Feature vector shape {vector.shape} is incompatible with the model."
            )
        if not np.isfinite(vector).all():
            raise FeaturePipelineUnavailable("Feature vector contains non-finite values.")
        return vector

