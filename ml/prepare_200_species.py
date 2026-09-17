"""Collect rights-cleared GBIF observations for the 200-species catalog.

A species enters training only when enough usable distinct observations download.
The output coverage.json records excluded species; it is never silently called 200-class.
"""
import argparse
import hashlib
import json
import random
import shutil
import time
from pathlib import Path
from prepare_gbif_species import ALLOWED, fetch_image, request_json

def collect(catalog_path, output, per_species, minimum):
    plants = json.loads(catalog_path.read_text(encoding="utf-8"))
    if len(plants) != 200 or len({p["gbif_taxon_key"] for p in plants}) != 200:
        raise ValueError("Catalog must have 200 unique taxon keys")
    output.mkdir(parents=True, exist_ok=True)
    randomizer = random.Random(42)
    counts, attribution, excluded = {}, [], {}
    for number, plant in enumerate(plants, 1):
        species, key = plant["accepted_name"], plant["gbif_taxon_key"]
        slug = species.lower().replace(" ", "_")
        candidates = []
        query = {"taxonKey": key, "mediaType": "StillImage",
                 "basisOfRecord": "HUMAN_OBSERVATION", "limit": 300}
        try:
            first_page = request_json("occurrence/search", dict(query, offset=0))
            total = first_page.get("count", 0)
        except Exception as exc:
            print(f"GBIF error for {species}: {exc}", flush=True)
            first_page, total = {"results": []}, 0
        # Search later parts of a large result set as well as its first pages.
        # GBIF offsets above 200000 are not supported by its search endpoint.
        offsets = [0, 300, 600, 900]
        if total > 1200:
            offsets += [min(max(1200, int(total * fraction) - 150), 199700)
                        for fraction in (0.1, 0.25, 0.5, 0.75, 0.9)]
        for offset in sorted(set(offsets)):
            try:
                page = first_page if offset == 0 else request_json(
                    "occurrence/search", dict(query, offset=offset))
            except Exception as exc:
                print(f"GBIF page error for {species} at {offset}: {exc}", flush=True)
                continue
            for record in page.get("results", []):
                if record.get("taxonKey") != key or record.get("taxonRank") != "SPECIES":
                    continue
                media = next((m for m in record.get("media", [])
                              if m.get("type") == "StillImage"
                              and (m.get("license") or "").strip().rstrip("/") + "/" in ALLOWED
                              and (m.get("identifier") or "").startswith("https://")), None)
                if media:
                    candidates.append((record, media))
            if len(candidates) >= per_species * 8:
                break
        randomizer.shuffle(candidates)
        seen_occurrences, seen_urls, seen_digests = set(), set(), set()
        photos = []
        for record, media in candidates:
            uri = media["identifier"]
            if record["key"] in seen_occurrences or uri in seen_urls:
                continue
            seen_occurrences.add(record["key"])
            seen_urls.add(uri)
            data = fetch_image(uri)
            if data is None:
                continue
            digest = hashlib.sha256(data).hexdigest()
            if digest in seen_digests:
                continue
            seen_digests.add(digest)
            # Split by occurrence, not by image; one photo per occurrence is used.
            split = "val" if len(photos) % 5 == 0 else "train"
            folder = output / split / slug
            folder.mkdir(parents=True, exist_ok=True)
            (folder / (digest + ".jpg")).write_bytes(data)
            photos.append({"species": species, "gbif_id": record["key"],
                           "sha256": digest, "url": uri,
                           "license": (media.get("license") or "").strip(),
                           "creator": media.get("creator") or record.get("rightsHolder") or "Unknown",
                           "source": "https://www.gbif.org/occurrence/" + str(record["key"])})
            if len(photos) >= per_species:
                break
        if len(photos) < minimum:
            for split in ("train", "val"):
                shutil.rmtree(output / split / slug, ignore_errors=True)
            excluded[species] = {"usable_photos": len(photos), "reason": "below_minimum"}
        else:
            counts[slug] = len(photos)
            attribution.extend(photos)
        print(f"{number}/200 {species}: {len(photos)} usable photos", flush=True)
        time.sleep(0.1)
    coverage = {
        "catalog_species": 200, "trained_species": len(counts),
        "excluded_species": excluded, "minimum_photos_per_species": minimum,
        "photos_per_species_target": per_species,
        "warning": "GBIF labels can be wrong; random observation split is not an independent real-world test.",
    }
    (output / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    (output / "counts.json").write_text(json.dumps(counts, indent=2) + "\n")
    (output / "attribution.json").write_text(json.dumps(attribution, indent=2) + "\n")
    if len(counts) < 4:
        raise RuntimeError("Not enough supported classes to train")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--per-species", type=int, default=25)
    parser.add_argument("--minimum", type=int, default=12)
    args = parser.parse_args()
    collect(args.catalog, args.output, args.per_species, args.minimum)
