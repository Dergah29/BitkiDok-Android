"""Adapt replacement photo metadata to the existing download/decoder audit.

No photos are promoted to training data by this report.
"""
import argparse
import json
import tempfile
from pathlib import Path

from validate_inat_photos import validate


def main(source, output, max_per_species=90):
    report = json.loads(Path(source).read_text(encoding="utf-8"))
    rows = []
    for row in report["results"]:
        rows.append({"species": row["species"], "gbif_usable_photos": 0,
                     "candidates": [{"observation_id": p["observation_id"],
                                     "photo_id": p["photo_id"],
                                     "photo_license": p["photo_license"],
                                     "photographer": p["photographer"],
                                     "photo_url": p["photo_url"]}
                                    for p in row["photo_candidates"]]})
    with tempfile.TemporaryDirectory() as temporary:
        input_path = Path(temporary) / "replacement_input.json"
        input_path.write_text(json.dumps({"results": rows}), encoding="utf-8")
        validate(input_path, output, max_per_species=max_per_species, delay=0.3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--max-per-species", type=int, default=90)
    args = parser.parse_args()
    main(args.source, args.output, args.max_per_species)
