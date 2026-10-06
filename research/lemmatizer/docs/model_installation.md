# Local model installation

Installed 2026-10-05 in `research/lemmatizer/.venv` (Python 3.12.9, macOS arm64).
The Sefaria application environment was not modified. The environment takes
about 975 MB and downloaded models/caches about 1.9 GB; both are ignored by Git.

| Component | Installed version |
|---|---|
| PyTorch | 2.14.1 |
| Transformers | 4.57.6 |
| Stanza | 1.11.0 |
| Shoshan | 0.4.0, pinned Git commit in comparison.json |

Exact dependency versions: `configs/model-requirements.lock.txt`.
Model revisions/settings: `configs/comparison.json`.
Downloaded file checksums and smoke-test outputs: `configs/model-installation.json`.
Stanza resources and processor dependencies were downloaded using resource
version 1.11.0, whose download implementation checks the resource MD5 values.
The additional SHA-256 inventory records the actual installed files.

## Use the environment

From the Sefaria-Data root:

```sh
source research/lemmatizer/.venv/bin/activate
python -B research/lemmatizer/src/smoke_models.py --model dicta --device mps
python -B research/lemmatizer/src/smoke_models.py --model shoshan --device mps
python -B research/lemmatizer/src/smoke_models.py --model stanza --device mps
```

All three completed offline inference on `הילדים קראו בספרים.` using Apple MPS.
Each returned the lexical lemmas ילד, קרא, ספר; Stanza also separated the article
and preposition. This checks installation only, not dataset accuracy, speed or
numerical parity with CPU. Each command starts a fresh process so model memory
is released between tests. `--device cpu` is available but was not benchmarked.

Dicta's `AutoModel` dynamic loader failed to copy transitive sibling Python
modules in this snapshot. The smoke test imports `BertForLexPrediction` directly
from the pinned local snapshot and calls its `from_pretrained` method. The
upstream Python files and weights remain unchanged. Use this same loading path
in the future comparison adapter.

## Reproduce installation

Use an Apple Silicon Python 3.12 interpreter to create the environment, then:

```sh
python3.12 -m venv research/lemmatizer/.venv
research/lemmatizer/.venv/bin/python -m pip install \
  -r research/lemmatizer/configs/model-requirements.lock.txt
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/install_models.py
```

The installer requires network access, downloads only the selected model
snapshots/processors and writes to `models/`. The smoke script uses offline
loading with local cache paths. The dependency lock captures this Mac setup;
other platforms may need compatible PyTorch wheels.

No full dataset evaluation has been launched. Next implement shared context
windows and the three prediction adapters, validate target alignment, then run
a small stratified comparison before evaluating the complete dataset.
