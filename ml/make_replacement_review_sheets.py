"""Generate taxon photo review sheets, favoring different attribution strings."""
import argparse
import io
import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw
from validate_inat_photos import NoRedirect, medium_url

PRIORITY = ("Dischidia nummularia", "Monstera pinnatipartita")


def build(source, directory):
    report = json.loads(Path(source).read_text(encoding="utf-8"))
    directory.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(NoRedirect)
    manifest = []
    for row in report["results"]:
        if row["species"] not in PRIORITY:
            continue
        images = row["validated_photos"]
        # Take one photo per attribution bucket first, then fill remaining slots.
        seen, first, rest = set(), [], []
        for item in images:
            credit = item["photographer"]
            if credit not in seen and credit != "no rights reserved":
                seen.add(credit)
                first.append(item)
            else:
                rest.append(item)
        chosen = (first + rest)[:12]
        sheet = Image.new("RGB", (1450, 1240), "white")
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 12), row["species"] + " — candidate photos, identity not verified", fill="black")
        for index, photo in enumerate(chosen):
            x = (index % 4) * 360
            y = (index // 4) * 400 + 40
            try:
                url = medium_url({"photo_url": photo["medium_url"], "photo_id": photo["photo_id"]})
                with opener.open(urllib.request.Request(url, headers={"User-Agent": "BitkiDokResearch/0.3"}), timeout=25) as response:
                    data = response.read(4_000_001)
                if len(data) > 4_000_000:
                    raise ValueError("oversized")
                with Image.open(io.BytesIO(data)) as im:
                    im.verify()
                with Image.open(io.BytesIO(data)) as im:
                    preview = im.convert("RGB")
                    preview.thumbnail((345, 315))
                sheet.paste(preview, (x + (345-preview.width)//2, y + (315-preview.height)//2))
                draw.text((x+6, y+325), f"photo {photo['photo_id']} / obs {photo['observation_id']}", fill="black")
                draw.text((x+6, y+340), photo["photographer"][:43], fill="black")
                draw.text((x+6, y+357), "license metadata: " + photo["license_metadata"], fill="black")
                manifest.append({"species": row["species"], "photo_id": photo["photo_id"],
                                 "observation_id": photo["observation_id"], "photographer": photo["photographer"],
                                 "license_metadata": photo["license_metadata"], "medium_url": url})
            except Exception as exc:
                draw.text((x+6, y+120), "FETCH ERROR " + type(exc).__name__, fill="red")
        sheet.save(directory / (row["species"].replace(" ", "_") + "_review.jpg"), quality=88)
    (directory / "manifest.json").write_text(json.dumps({
        "meaning": "Human/subject-matter expert review aids; no approved model labels.",
        "photos": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    build(args.source, args.out)
