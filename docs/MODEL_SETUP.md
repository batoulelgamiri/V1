# Verified model setup

## Public sources inspected

1. [X-MalForensics-XGBoost model card](https://huggingface.co/Pugazh24/X-MalForensics-XGBoost) states that `baseline_xgboost.json` is an XGBoost classifier trained on EMBER 2018, requires the `xgboost` and `ember` libraries, and consumes 2,381 structural PE features.
2. The [official Elastic EMBER repository](https://github.com/elastic/ember) defines EMBER 2018 as feature version 2. Its `PEFeatureExtractor(feature_version=2)` produces the ordered 2,381-element vector.
3. Elastic documents that EMBER v2 was calculated with LIEF 0.9.0 and that LIEF 0.10.1 was verified to produce consistent representations on Windows and Linux. It explicitly warns that other LIEF versions can produce unpredictable model results.
4. The application pins the archived official EMBER source at commit `d97a0b523de02f3fe5ea6089d080abacab6ee931`.
5. The exact environment pins NumPy 1.23.5 because the official extractor uses the historical `np.int` alias removed in NumPy 1.24.
6. It pins scikit-learn 1.1.3 because this EMBER revision relies on the pre-1.2 `FeatureHasher` string-input behavior.

The downloaded model was inspected as XGBoost JSON. It reports XGBoost format version `1.7.6`, objective `binary:logistic`, 100 trees, and `num_feature=2381`. The verified public artifact digest is:

```text
1dafb3b9c826457c158f8950687ad653f005dd4d5a29a39040047499405e08ee
```

The repository does not invent or approximate EMBER-compatible fields. It calls the official v2 extractor and rejects missing dependencies, incorrect dimensions, non-finite output, unverified LIEF versions, a model digest mismatch, or a model feature-count mismatch.

## Reproducible installation

The historical LIEF build is easiest to obtain through Conda:

```powershell
conda env create -f environment.yml
conda activate aegis-pe
python backend/scripts/setup_model.py
```

The setup script downloads only:

```text
https://huggingface.co/Pugazh24/X-MalForensics-XGBoost/resolve/main/baseline_xgboost.json
```

It writes through a temporary file, verifies SHA-256, and atomically moves the artifact to `backend/models/baseline_xgboost.json`. An existing mismatched file is never silently overwritten.

## Verify loading

Start the backend, then request:

```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

Expected fields include `model_available: true` and a model version beginning `hf-1dafb3b9c826-ember-v2`.

## Test analysis

Use a known benign Windows executable you are authorized to inspect:

```powershell
curl.exe -X POST http://localhost:8000/api/analyses/upload -F "file=@C:\\Windows\\System32\\where.exe"
```

The result is a probabilistic static classification, not an antivirus guarantee. Do not treat a benign result as proof of safety.

## Compatibility boundary

The model card does not publish training code or per-feature names inside the model; its compatibility statement is the EMBER 2018/2,381-feature contract. A model artifact without the exact extractor remains unavailable. The application does not enable an override for newer LIEF versions because doing so would violate that contract.
