"""Download and prepare the original, CC BY 4.0, 787-image Mendeley dataset."""
import csv
import io
import random
import re
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path
from PIL import Image

URL = 'https://data.mendeley.com/public-files/datasets/7wbstnfpjy/files/ad36d4df-acf3-4989-8472-44586cf871d3/file_downloaded'
SOURCE = 'https://data.mendeley.com/datasets/7wbstnfpjy/2'
CREATOR = 'Nishad Mahmud; Md Saiful Islam'


def slug(value):
    return re.sub(r'[^a-z0-9]+', '_', value.lower()).strip('_')


def prepare(output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory must be empty')
    req = urllib.request.Request(URL, headers={'User-Agent': 'BitkiDok-research/0.1'})
    with urllib.request.urlopen(req, timeout=120) as response:
        archive = response.read(40_000_001)
    if len(archive) > 40_000_000:
        raise ValueError('Unexpected archive size')
    classes = defaultdict(list)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for entry in z.infolist():
            if entry.is_dir() or Path(entry.filename).suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
                continue
            components = [part for part in entry.filename.replace('\\', '/').split('/') if part and not part.startswith('.') and part != '__MACOSX']
            if len(components) < 2 or entry.file_size > 15_000_000:
                continue
            label = slug(components[-2])
            if not label:
                continue
            raw = z.read(entry)
            try:
                with Image.open(io.BytesIO(raw)) as image:
                    image.verify()
            except Exception:
                continue
            classes[label].append((entry.filename, raw))
    print('Found classes:', {name: len(items) for name, items in classes.items()})
    if len(classes) != 9 or not 700 <= sum(map(len, classes.values())) <= 900:
        raise ValueError('Unexpected dataset classes or photo count; review archive manually before training')
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    with (output / 'manifest.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['path', 'label', 'license', 'source', 'creator'])
        writer.writeheader()
        for label, items in sorted(classes.items()):
            rng.shuffle(items)
            validation = max(2, round(len(items) * .2))
            for i, (name, raw) in enumerate(items):
                split = 'val' if i < validation else 'train'
                path = output / split / label / f'{i:04d}{Path(name).suffix.lower()}'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                writer.writerow({'path': path.relative_to(output).as_posix(), 'label': label, 'license': 'CC BY 4.0', 'source': SOURCE, 'creator': CREATOR})
    print('Dataset prepared:', output)


if __name__ == '__main__':
    prepare(sys.argv[1])
