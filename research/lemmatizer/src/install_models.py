"""Download pinned comparison models into the ignored local models directory."""
import os
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'models'
os.environ.setdefault('HF_HOME', str(MODELS / 'hf_cache'))
os.environ.setdefault('HF_MODULES_CACHE', str(MODELS / 'hf_modules'))


def main():
    from huggingface_hub import snapshot_download
    import stanza
    config = json.loads((ROOT / 'configs/comparison.json').read_text())
    MODELS.mkdir(exist_ok=True)
    for name in ('dicta', 'shoshan'):
        info = config[name]
        print(f'Downloading {name}: {info["model"]} @ {info["revision"]}', flush=True)
        snapshot_download(repo_id=info['model'], revision=info['revision'],
                          local_dir=MODELS/name,
                          ignore_patterns=['pytorch_model.bin'] if name == 'dicta' else None)
    print('Downloading Hebrew Stanza processors and dependencies...', flush=True)
    stanza.download('he', model_dir=str(MODELS/'stanza'),
                    processors=config['stanza']['processors'], package=None,
                    resources_version=config['stanza']['resources_version'])
    print('Model downloads complete.', flush=True)


if __name__ == '__main__':
    main()
