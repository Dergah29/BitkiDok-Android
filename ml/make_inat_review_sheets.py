"""Make human-review contact sheets for the 15 potentially recoverable species.

Only CC0/CC-BY metadata candidates; sheets are visual review aids, not labels.
"""
import argparse
import io
import json
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from validate_inat_photos import NoRedirect, medium_url


def build(manifest_path, summary_path, directory, photos_per_species=4):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    eligible = {row["species"] for row in summary["rows"]
                if row["gbif_usable_photos"] + row["medium_images_decoded_unique"] >= 12}
    directory.mkdir(parents=True, exist_ok=True)
    rows, errors = [], []
    opener = urllib.request.build_opener(NoRedirect)
    for row in manifest["results"]:
        if row["species"] not in eligible:
            continue
        selected = []
        seen_observations = set()
        for candidate in row["candidates"]:
            if len(selected) >= photos_per_species:
                break
            if candidate["observation_id"] in seen_observations or candidate["photo_license"] not in {"cc0", "cc-by"}:
                continue
            try:
                url = medium_url(candidate)
                request = urllib.request.Request(url, headers={"User-Agent": "BitkiDokResearch/0.3 (github.com/Dergah29/BitkiDok-Android)"})
                with opener.open(request, timeout=20) as response:
                    data = response.read(4_000_001)
                if len(data) > 4_000_000:
                    raise ValueError("oversized")
                with Image.open(io.BytesIO(data)) as im:
                    im.verify()
                with Image.open(io.BytesIO(data)) as im:
                    if min(im.size) < 300:
                        raise ValueError("too_small")
                    preview = im.convert("RGB")
                seen_observations.add(candidate["observation_id"])
                selected.append((candidate, preview))
            except Exception as exc:
                errors.append({"species": row["species"], "photo_id": candidate["photo_id"], "error": str(exc)[:90]})
            time.sleep(0.2)
        rows.append((row["species"], selected))
    if len(rows) != 15:
        raise RuntimeError(f"Expected 15 priority species, found {len(rows)}")
    manifest_output = []
    for page in range(0, len(rows), 3):
        sheet = Image.new("RGB", (1320, 1170), "white")
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 8), f"BitkiDok candidates {page // 3 + 1}/5 — needs botanical review", fill="black")
        for row_index, (species, selected) in enumerate(rows[page:page + 3]):
            y = row_index * 385 + 40
            draw.text((20, y), species, fill="black")
            for col, (photo, image) in enumerate(selected):
                image.thumbnail((310, 310))
                x = col * 330 + (330 - image.width) // 2
                sheet.paste(image, (x, y + 25 + (310 - image.height) // 2))
                draw.text((col * 330 + 5, y + 340), f"obs {photo['observation_id']} / photo {photo['photo_id']}", fill="black")
                draw.text((col * 330 + 5, y + 355), f"license metadata: {photo['photo_license']}", fill="black")
                manifest_output.append({"species": species, **{k: photo[k] for k in
                                        ("observation_id", "photo_id", "photo_license", "photographer", "photo_url")}})
        sheet.save(directory / f"review_{page // 3 + 1:02d}.jpg", quality=86)
    (directory / "review_manifest.json").write_text(json.dumps({"image_count": len(manifest_output),
        "meaning": "Review samples only; cannot establish correct taxonomy or independent test accuracy.",
        "photos": manifest_output, "errors": errors}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Contact sheets: {len(rows)} species, {len(manifest_output)} thumbnails, {len(errors)} fetch errors", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("summary", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.manifest, args.summary, args.output)
