"""Audit image and license availability for the 200-species offline classifier.

Metadata only: does not download images or imply usable training coverage.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ALLOWED = {
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "http://creativecommons.org/publicdomain/zero/1.0/",
    "https://creativecommons.org/licenses/by/4.0/",
    "http://creativecommons.org/licenses/by/4.0/",
}
def get_json(path, params):
    url = "https://api.gbif.org/v1/" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "BitkiDokCoverageAudit/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=35) as reply:
                return json.load(reply)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

def audit(catalog, output, minimum=20, pages=4):
    plants = json.loads(Path(catalog).read_text(encoding="utf-8"))
    if len(plants) != 200 or len({p["gbif_taxon_key"] for p in plants}) != 200:
        raise ValueError("Expected 200 distinct GBIF taxon keys")
    results = []
    for number, plant in enumerate(plants, 1):
        key = plant["gbif_taxon_key"]
        seen_occurrences = set()
        seen_urls = set()
        failures = []
        for offset in range(0, pages * 300, 300):
            try:
                page = get_json("occurrence/search", {
                    "taxonKey": key, "mediaType": "StillImage",
                    "basisOfRecord": "HUMAN_OBSERVATION",
                    "limit": 300, "offset": offset,
                })
            except Exception as exc:
                failures.append(type(exc).__name__)
                break
            for item in page.get("results", []):
                if item.get("taxonKey") != key or item.get("taxonRank") != "SPECIES":
                    continue
                for media in item.get("media", []):
                    license_url = (media.get("license") or "").strip().rstrip("/") + "/"
                    if license_url not in ALLOWED or media.get("type") != "StillImage":
                        continue
                    url = media.get("identifier", "")
                    if not url.startswith("https://"):
                        continue
                    seen_occurrences.add(item["key"])
                    seen_urls.add(url)
            if page.get("endOfRecords"):
                break
        # Candidate metadata counts are upper bounds: links can fail, duplicate photos
        # can exist at different URLs, and images can be mislabeled.
        row = {
            "species": plant["accepted_name"], "gbif_taxon_key": key,
            "candidate_occurrences": len(seen_occurrences),
            "candidate_image_urls": len(seen_urls),
            "minimum_candidate_urls_met": len(seen_urls) >= minimum,
            "query_errors": failures,
            "photo_model_status": plant["photo_model_status"],
        }
        results.append(row)
        print(f"{number}/200 {row['species']}: {len(seen_urls)} candidates", flush=True)
        time.sleep(0.12)
    report = {
        "method": "GBIF occurrence metadata, first 1200 records per species; CC0/CC BY 4.0 only",
        "minimum_candidate_urls": minimum, "species_total": len(results),
        "candidate_threshold_met": sum(r["minimum_candidate_urls_met"] for r in results),
        "not_yet_enough_candidates": [r["species"] for r in results if not r["minimum_candidate_urls_met"]],
        "species_with_query_errors": [r["species"] for r in results if r["query_errors"]],
        "disclaimer": "Candidate URL count is not a usable-photo count or model accuracy.",
        "results": results,
    }
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    audit(sys.argv[1], sys.argv[2])
