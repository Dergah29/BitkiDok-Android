"""Audit near-identical photo leakage in the original indoor health dataset."""
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image, ImageOps
from prepare_mendeley import URL, slug

def dhash(raw):
    with Image.open(io.BytesIO(raw)) as image:
        gray = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())
        value = 0
        for y in range(8):
            for x in range(8):
                value = value << 1 | (pixels[y * 9 + x] > pixels[y * 9 + x + 1])
        return value

def audit(out):
    with urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "BitkiDokResearch/0.5"}), timeout=120) as response:
        raw_zip = response.read(40_000_001)
    if len(raw_zip) > 40_000_000:
        raise ValueError("unexpected_archive_size")
    records = []
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        for entry in archive.infolist():
            if entry.is_dir() or Path(entry.filename).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            pieces = [x for x in entry.filename.replace("\\\\", "/").split("/") if x and not x.startswith(".") and x != "__MACOSX"]
            if len(pieces) < 2 or entry.file_size > 15_000_000:
                continue
            label = slug(pieces[-2])
            content = archive.read(entry)
            try:
                digest, visual = hashlib.sha256(content).hexdigest(), dhash(content)
            except Exception:
                continue
            records.append({"path": entry.filename, "label": label, "sha256": digest, "dhash": visual})
    if not 700 <= len(records) <= 900 or len({x["label"] for x in records}) != 9:
        raise ValueError("unexpected_dataset_contents")
    exact, near = [], []
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            if a["sha256"] == b["sha256"]:
                exact.append({"a": a["path"], "b": b["path"], "labels_conflict": a["label"] != b["label"]})
            elif a["label"] == b["label"]:
                distance = (a["dhash"] ^ b["dhash"]).bit_count()
                if distance <= 2:
                    near.append({"a": a["path"], "b": b["path"], "dhash_distance": distance})
    result = {"dataset": "https://data.mendeley.com/datasets/7wbstnfpjy/2",
              "original_images_decoded": len(records), "classes": len({x["label"] for x in records}),
              "exact_byte_duplicate_pairs": exact, "near_visual_candidate_pairs_same_label": near,
              "limits": ["dHash does not confirm the same physical plant or guarantee all near-duplicates are found.",
                         "The published 92.99% random-image validation score remains unverified on independent plants and phone photos.",
                         "No new disease classes or training data were produced."]}
    Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({"images": len(records), "exact_pairs": len(exact), "near_candidates": len(near)}, flush=True)

if __name__ == "__main__":
    audit(sys.argv[1])
