"""Select 200 unique taxonomically matched houseplant candidates from GBIF.

This verifies names, not suitability for a home or photo-model coverage.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

def match(name):
    url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode(
        {"name": name, "strict": "true"})
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BitkiDokCatalog/0.1"})
            with urllib.request.urlopen(req, timeout=25) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def main(source, output):
    rows = json.loads(source.read_text(encoding="utf-8"))
    selected, rejected, keys = [], [], set()
    for item in rows:
        name = item["scientific_name"]
        try:
            info = match(name)
        except Exception as exc:
            rejected.append({"name": name, "reason": str(exc)})
            continue
        key = info.get("usageKey")
        if (info.get("rank") != "SPECIES" or info.get("confidence", 0) < 90
                or not key):
            rejected.append({"name": name, "reason": "uncertain taxonomy", "match": info})
            continue
        canonical = info.get("canonicalName") or info.get("scientificName", "").split(" (")[0]
        if key in keys:
            rejected.append({"name": name, "reason": "same GBIF taxon"})
            continue
        keys.add(key)
        selected.append({"requested_name": name, "accepted_name": canonical,
                         "gbif_taxon_key": key, "category": item["category"],
                         "gbif_match_confidence": info["confidence"],
                         "photo_model_status": "not_trained"})
        if len(selected) == 200:
            break
    output.mkdir(parents=True, exist_ok=True)
    (output / "houseplants_200.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2))
    (output / "taxonomy_report.json").write_text(json.dumps({
        "candidate_count": len(rows), "accepted_count": len(selected),
        "rejected": rejected,
        "note": "Taxonomy check only. No claim that all 200 are photo-recognizable."
    }, ensure_ascii=False, indent=2))
    print("selected", len(selected), "rejected", len(rejected), flush=True)
    if len(selected) < 200:
        raise SystemExit("Not enough verified unique species; add more candidates")

if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
