"""Download licensed houseplant photos from GBIF for an experimental species classifier.

Usage: python ml/prepare_gbif_species.py out --per-species 50 --minimum 20
Only CC0 / CC BY 4.0 image records with explicit image rights are accepted.
"""
import argparse
import hashlib
import io
import json
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageOps

SPECIES = [
    "Monstera deliciosa", "Epipremnum aureum", "Dracaena trifasciata",
    "Chlorophytum comosum", "Ficus elastica", "Aloe vera",
    "Spathiphyllum wallisii", "Zamioculcas zamiifolia", "Crassula ovata",
    "Ficus benjamina", "Tradescantia zebrina", "Schlumbergera truncata",
]
ALLOWED = {"http://creativecommons.org/publicdomain/zero/1.0/",
           "https://creativecommons.org/publicdomain/zero/1.0/",
           "http://creativecommons.org/licenses/by/4.0/",
           "https://creativecommons.org/licenses/by/4.0/"}

def request_json(endpoint, params):
    url = "https://api.gbif.org/v1/" + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "BitkiDokResearch/0.1 (dataset attribution)"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def fetch_image(url):
    if urllib.parse.urlparse(url).scheme != "https":
        return None
    req = urllib.request.Request(url, headers={"User-Agent": "BitkiDokResearch/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if "image/" not in response.headers.get("Content-Type", ""):
                return None
            data = response.read(8_000_001)
            if len(data) > 8_000_000:
                return None
        with Image.open(io.BytesIO(data)) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            if min(im.size) < 200:
                return None
            im.thumbnail((640, 640))
            out = io.BytesIO()
            im.save(out, format="JPEG", quality=85)
            return out.getvalue()
    except Exception:
        return None

def main(output, per_species, minimum):
    rng = random.Random(42)
    output.mkdir(parents=True, exist_ok=True)
    attribution = []
    counts = {}
    for species in SPECIES:
        match = request_json("species/match", {"name": species, "strict": "true"})
        if match.get("rank") != "SPECIES" or match.get("confidence", 0) < 90:
            print("Skip uncertain taxonomy:", species, match, flush=True)
            continue
        slug = species.lower().replace(" ", "_")
        candidates = []
        # GBIF API search pages; no images are taken without an explicit photo license.
        for offset in (0, 300, 600, 900):
            page = request_json("occurrence/search", {
                "taxonKey": match["usageKey"], "mediaType": "StillImage",
                "basisOfRecord": "HUMAN_OBSERVATION", "limit": 300, "offset": offset,
            })
            for record in page.get("results", []):
                if (record.get("taxonKey") != match["usageKey"] or
                    record.get("taxonRank") != "SPECIES"):
                    continue
                for media in record.get("media", []):
                    license_url = (media.get("license") or "").strip()
                    if license_url.rstrip("/") + "/" not in ALLOWED:
                        continue
                    if media.get("type") != "StillImage" or not media.get("identifier"):
                        continue
                    candidates.append((record, media, license_url))
            if page.get("endOfRecords") or len(candidates) >= per_species * 6:
                break
        rng.shuffle(candidates)
        seen = set()
        photos = []
        for record, media, license_url in candidates:
            uri = media["identifier"]
            if uri in seen:
                continue
            seen.add(uri)
            data = fetch_image(uri)
            if data is None:
                continue
            digest = hashlib.sha256(data).hexdigest()
            if digest in {p["sha256"] for p in photos}:
                continue
            photos.append({"sha256": digest, "gbif_id": record["key"], "url": uri,
                           "license": license_url, "creator": media.get("creator") or record.get("rightsHolder") or "Unknown",
                           "source": "https://www.gbif.org/occurrence/" + str(record["key"])})
            folder = output / ("val" if len(photos) % 5 == 0 else "train") / slug
            folder.mkdir(parents=True, exist_ok=True)
            (folder / (digest + ".jpg")).write_bytes(data)
            if len(photos) >= per_species:
                break
        print(species, len(photos), flush=True)
        if len(photos) < minimum:
            import shutil
            for split in ("train", "val"):
                shutil.rmtree(output / split / slug, ignore_errors=True)
            print("Skip insufficient licensed photos:", species, flush=True)
            continue
        counts[slug] = len(photos)
        attribution.extend(dict(species=species, **p) for p in photos)
        time.sleep(0.2)
    if len(counts) < 4:
        raise RuntimeError("Fewer than four species have enough licensed photos")
    (output / "attribution.json").write_text(json.dumps(attribution, indent=2))
    (output / "counts.json").write_text(json.dumps(counts, indent=2))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    p.add_argument("--per-species", type=int, default=50)
    p.add_argument("--minimum", type=int, default=20)
    args = p.parse_args()
    main(args.output, args.per_species, args.minimum)
