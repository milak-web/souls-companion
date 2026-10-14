"""Build the static Pages artifact without publishing maintenance/research files."""
import argparse
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist'
FILES = ['index.html', 'ds1.html', 'games.html', 'manifest.webmanifest', '.nojekyll']
DIRECTORIES = ['css', 'js', 'database', 'assets', 'images', 'icons']


def build(link_assets=False):
    OUTPUT.mkdir(exist_ok=True)
    count = 0
    original_json = compact_json = 0
    for source in [ROOT / name for name in FILES] + [
        file for name in DIRECTORIES for file in sorted((ROOT / name).rglob('*')) if file.is_file()
    ]:
        if source.is_symlink():
            raise ValueError(f'Unexpected symlink: {source.relative_to(ROOT)}')
        target = OUTPUT / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()
        if source.suffix == '.json':
            original_json += source.stat().st_size
            data = json.loads(source.read_text(encoding='utf-8'))
            target.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf-8')
            compact_json += target.stat().st_size
        elif link_assets and source.relative_to(ROOT).parts[0] in ['assets', 'images']:
            os.link(source, target)
        else:
            shutil.copy2(source, target)
        count += 1
    total = sum(file.stat().st_size for file in OUTPUT.rglob('*') if file.is_file())
    print(f'Built {count} files ({total / 1024**2:.1f} MiB).')
    print(f'Catalog JSON: {original_json / 1024**2:.1f} to {compact_json / 1024**2:.1f} MiB; values unchanged.')
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--link-assets', action='store_true', help='Local disk-saving preview only; never use for a Pages upload.')
    build(parser.parse_args().link_assets)
