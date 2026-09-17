"""Audit extra GBIF observation pages for missing catalog species."""
import json
import sys
import time
from pathlib import Path
from prepare_gbif_species import request_json, ALLOWED

def audit(catalog_file, coverage_file, output_file):
    plants = {p["accepted_name"]: p for p in json.loads(Path(catalog_file).read_text())}
    missing = [p["species"] for p in json.loads(Path(coverage_file).read_text())["species"] if p["usable_photos"] < 12]
    results = []
    for i, species in enumerate(missing, 1):
        key = plants[species]["gbif_taxon_key"]
        found = set()
        count = 0
        error = None
        try:
            first = request_json("occurrence/search", {
                "taxonKey": key, "mediaType": "StillImage",
                "basisOfRecord": "HUMAN_OBSERVATION", "limit": 1})
            count = first.get("count", 0)
            offsets = sorted({min(max(0, int(count*f)-150), 199700)
                              for f in (0.1, 0.25, 0.5, 0.75, 0.9)})
            for offset in offsets:
                page = request_json("occurrence/search", {
                    "taxonKey": key, "mediaType": "StillImage",
                    "basisOfRecord": "HUMAN_OBSERVATION",
                    "limit": 300, "offset": offset})
                for record in page.get("results", []):
                    if record.get("taxonKey") != key or record.get("taxonRank") != "SPECIES":
                        continue
                    for image in record.get("media", []):
                        license_url = (image.get("license") or "").strip().rstrip("/") + "/"
                        if image.get("type") == "StillImage" and license_url in ALLOWED and (image.get("identifier") or "").startswith("https://"):
                            found.add(image["identifier"])
            time.sleep(0.15)
        except Exception as exc:
            error = str(exc)[:160]
        results.append({"species": species, "gbif_observation_count": count,
                        "additional_page_candidate_urls": len(found),
                        "error": error})
        print(f"{i}/{len(missing)} {species}: {len(found)} candidates; observations={count}", flush=True)
    result = {"species_checked": len(missing),
              "species_with_additional_candidates": sum(p["additional_page_candidate_urls"] > 0 for p in results),
              "method": "Five additional GBIF search windows per species; metadata only, no image or label validation",
              "results": results}
    Path(output_file).write_text(json.dumps(result, indent=2) + "\n")

if __name__ == "__main__":
    audit(*sys.argv[1:4])
