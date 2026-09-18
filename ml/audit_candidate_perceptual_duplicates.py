"""Candidate-only perceptual duplicate audit; never admits images to training."""
import argparse
import hashlib
import io
import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps
from validate_inat_photos import NoRedirect, medium_url, MAX_BYTES

def dhash(image):
    gray = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    result = 0
    for y in range(8):
        for x in range(8):
            result = (result << 1) | (pixels[y * 9 + x] > pixels[y * 9 + x + 1])
    return result

def audit(paths, output):
    entries, errors = [], []
    opener = urllib.request.build_opener(NoRedirect)
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        for row in document["results"]:
            for photo in row["validated_photos"]:
                try:
                    url = medium_url({"photo_url": photo["medium_url"], "photo_id": photo["photo_id"]})
                    req = urllib.request.Request(url, headers={"User-Agent": "BitkiDokResearch/0.4"})
                    with opener.open(req, timeout=25) as response:
                        raw = response.read(MAX_BYTES + 1)
                    if len(raw) > MAX_BYTES:
                        raise ValueError("image_too_large")
                    digest = hashlib.sha256(raw).hexdigest()
                    if digest != photo["sha256_medium"]:
                        raise ValueError("changed_medium_bytes")
                    with Image.open(io.BytesIO(raw)) as img:
                        img.verify()
                    with Image.open(io.BytesIO(raw)) as img:
                        h = dhash(img)
                    entries.append({"species": row["species"], "photo_id": photo["photo_id"],
                                    "observation_id": photo["observation_id"], "source": path.name,
                                    "dhash64": format(h, "016x")})
                except Exception as exc:
                    errors.append({"photo_id": photo["photo_id"], "source": path.name,
                                   "reason": str(exc) if isinstance(exc, ValueError) else type(exc).__name__})
    pairs = []
    for index, first in enumerate(entries):
        for second in entries[index + 1:]:
            distance = (int(first["dhash64"], 16) ^ int(second["dhash64"], 16)).bit_count()
            if distance <= 4:
                pairs.append({"photo_a": first["photo_id"], "species_a": first["species"],
                              "photo_b": second["photo_id"], "species_b": second["species"],
                              "distance": distance, "cross_species": first["species"] != second["species"]})
    result = {"meaning": "Perceptual candidates for human review; low dHash distance does not prove identical image, plant or species.",
              "sources": [str(p) for p in paths], "hash_method": "64-bit horizontal dHash grayscale 9x8",
              "pair_threshold_hamming": 4, "photos_checked": len(entries), "errors": errors,
              "candidate_pairs": sorted(pairs, key=lambda x: (x["distance"], x["photo_a"])),
              "hashes": entries, "approved_training_photos": 0}
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print({"photos_checked": len(entries), "failed": len(errors), "candidate_pairs": len(pairs)}, flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("sources", type=Path, nargs="+")
    args = parser.parse_args()
    audit(args.sources, args.output)
