"""Fail closed on missing per-photo provenance and split leakage."""
import csv
import sys
from pathlib import Path


def validate(root: Path):
    manifest = root / 'manifest.csv'
    if not manifest.is_file():
        raise ValueError('Missing manifest.csv')
    seen = set()
    counts = {}
    with manifest.open(newline='', encoding='utf-8') as fh:
        rows = csv.DictReader(fh)
        required = {'path', 'label', 'license', 'source', 'creator'}
        if not required.issubset(rows.fieldnames or []):
            raise ValueError('Missing required manifest columns')
        for row in rows:
            if any(not row.get(key, '').strip() for key in required):
                raise ValueError('Missing photo metadata')
            rel = Path(row['path'])
            if rel.is_absolute() or '..' in rel.parts or len(rel.parts) != 3:
                raise ValueError('Invalid photo path')
            split, label, filename = rel.parts
            if split not in {'train', 'val'} or label != row['label'] or not filename:
                raise ValueError('Path / label mismatch')
            if rel.as_posix() in seen or not (root / rel).is_file():
                raise ValueError('Duplicate or missing photo')
            seen.add(rel.as_posix())
            counts[(split, label)] = counts.get((split, label), 0) + 1
    if not seen:
        raise ValueError('Empty dataset')
    actual = {p.relative_to(root).as_posix() for split in ('train', 'val') for p in (root / split).rglob('*') if p.is_file()}
    if actual != seen:
        raise ValueError('Unlisted photos or missing manifest entries')
    labels = {label for _, label in counts}
    if len(labels) < 2 or any(counts.get((split, label), 0) < 2 for label in labels for split in ('train', 'val')):
        raise ValueError('Need at least two classes and two images per class in each split')
    return labels, counts


if __name__ == '__main__':
    labels, counts = validate(Path(sys.argv[1]))
    print(f'Validated {len(labels)} classes and {sum(counts.values())} photos')
